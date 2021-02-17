import os
from os import path
import configparser
import requests
import json
import zipfile
import IP2Location
import sqlite3 as sl

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.express as px
import pandas as pd


##################################################
#                                                #
#  page_refresh_interval specifies page refresh  #
#  timing with new access log data               #
#                                                #
##################################################
#page_refresh_interval = 10    # in minutes

####################################
#                                  #
#  Initialize database at startup  #
#                                  #
####################################
con = sl.connect('connections.db')
cur = con.cursor()

cur.execute("DROP TABLE IF EXISTS connections")
cur.execute("""CREATE TABLE connections (
    ip text,
    requestmethod text,
    requestpath text,
    requestprotocol text,
    requestscheme text,
    statuscode text,
    time text,
    city text,
    region text,
    country_short text,
    country_long text)""")


#####################################
#                                   #
#  Loads variables from config.ini  #
#                                   #
#####################################
def load_config(config_file, config_section):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if os.path.isfile(dir_path + '/' + config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        logfile = config.get(config_section, 'logfile')
        traefik_ip = config.get(config_section, 'hostip')
        ip_token = config.get(config_section, 'ip2location token')
        page_refresh_interval = int(config.get(config_section, 'refresh interval'))
        if traefik_ip == 'dynamic':
            url = 'http://ipinfo.io/json'
            response = requests.get(url)
            data = response.json()
            traefik_ip = data['ip']
    return logfile, traefik_ip, page_refresh_interval, ip_token

config_file = 'config.ini'
config_section = 'dev'
log_file, traefik_ip, page_refresh_interval, ip_token = load_config(config_file, config_section)  # Load config


###########################################################
#                                                         #
#  Download IP2 LOCATION DB if not found.  Requires free  #
#  account at https://lite.ip2location.com/ to obtain a   #
#  download token for the config.ini file.                #
#                                                         #
###########################################################
def get_ipdb(url):
    target_path = os.path.join("", "IP2LOCATION-LITE-DB3.BIN.ZIP")
    r = requests.get(url, stream=True)
    handle = open(target_path, 'wb')
    for chunk in r.iter_content(chunk_size=512):
        if chunk:
            handle.write(chunk)
    handle.close()
    if zipfile.is_zipfile(target_path) == False:
        with open(target_path, 'r') as text_file:
            zip_error = text_file.read()
        print('Received ' + zip_error + ' response from IP DB provider.  Please check IP2LOCATION TOKEN is set correctly in config.ini.')
        os.remove(target_path)
        raise SystemExit
    else:
        with zipfile.ZipFile(target_path) as zf:
            zf.extractall()
        os.remove(target_path)
    if path.exists('IP2LOCATION-LITE-DB3.BIN'):
        print('IP DB file successfully extracted.')
    else:
        print('IP DB file extraction failed.')
        raise SystemExit
    return


#######################################################################
#                                                                     #
#  Read Traefik access log and populate SQL database with the fields  #
#  we care about.  Exclude Traefik server IP entries in the log.      #                                               
#                                                                     #
#######################################################################
def process_log(log_file, traefik_ip, ip_token):
    try:
        ipdb = IP2Location.IP2Location(os.path.join("", "IP2LOCATION-LITE-DB3.BIN"))
    except:
        print('IP Location DB not found, fetching...')
        get_ipdb('https://www.ip2location.com/download/?token=' + ip_token + '&file=DB3LITEBIN')
        ipdb = IP2Location.IP2Location(os.path.join("", "IP2LOCATION-LITE-DB3.BIN"))
    data = []
    i = 0
    with open(log_file) as f:
        for line in f:
            data.append(json.loads(line))
        while i < len(data):
            if data[i]['ClientHost'] != traefik_ip:
                details = ipdb.get_all(data[i]['ClientHost'])
                sql_work = "INSERT INTO connections (ip, requestmethod, requestpath, requestprotocol, requestscheme, statuscode, time, city, region, country_short, country_long) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                cur.execute(sql_work, (data[i]['ClientHost'], data[i]['RequestMethod'], data[i]['RequestPath'], data[i]['RequestProtocol'], data[i]['RequestScheme'], data[i]['DownstreamStatus'], data[i]['time'], details.city, details.region, details.country_short, details.country_long))
            i = i + 1
    con.commit()

process_log(log_file, traefik_ip, ip_token)                                # Populate SQL database with log data


##################################################################
#                                                                #
#  Update the log DB with recent log activity.  Called from the  #
#  DASH app callback functions.                                  #
#                                                                #
##################################################################
def update_log(log_file, traefik_ip):
    update_con = sl.connect('connections.db')
    tempdf=pd.read_sql_query('SELECT time from connections ORDER BY time', update_con) 
    last_time=tempdf.iloc[len(tempdf)-1]['time']
    ipdb = IP2Location.IP2Location(os.path.join("", "IP2LOCATION-LITE-DB3.BIN"))
    data = []
    i = 0
    with open(log_file) as f:
        for line in f:
            data.append(json.loads(line))
        while i < len(data):
            if data[i]['ClientHost'] != traefik_ip and data[i]['time'] > last_time:
                details = ipdb.get_all(data[i]['ClientHost'])
                sql_work = "INSERT INTO connections (ip, requestmethod, requestpath, requestprotocol, requestscheme, statuscode, time, city, region, country_short, country_long) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                update_con.execute(sql_work, (data[i]['ClientHost'], data[i]['RequestMethod'], data[i]['RequestPath'], data[i]['RequestProtocol'], data[i]['RequestScheme'], data[i]['DownstreamStatus'], data[i]['time'], details.city, details.region, details.country_short, details.country_long))
            i = i + 1
    update_con.commit()
    update_con.close()


###################################################################
#                                                                 #
#  Define SQL queries and populate dataframes for bar chart (df)  #
#  and data table (df2)                                           #
#                                                                 #
###################################################################
query1 = 'SELECT country_short as Country, count(DISTINCT ip) as "Distinct IPs", count(ip) as "Connections" from connections group by country_short'
df = pd.read_sql_query(query1, con)
query2 = 'SELECT ip as IP, city as City, region as Region, country_long as Country, time as Time, statuscode as "HTTP Response", requestmethod as Method, requestprotocol as Protocol, requestpath as "Path Attempt" from connections ORDER BY time DESC, country_long, city, ip'
df2 = pd.read_sql_query(query2, con)
con.close()


#####################
#                   #
#  Define DASH app  #
#                   #
#####################
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


###################################
#                                 #
#  Dynamically scale bar height   #
#                                 #
###################################
def calc_column_height(dfy):
    l = len(dfy)
    c = 0
    high = 0
    while c < l:
        if dfy.iloc[c]['Distinct IPs'] + dfy.iloc[c]['Connections'] > high:
            high = dfy.iloc[c]['Distinct IPs'] + dfy.iloc[c]['Connections']
        c = c + 1
    high = high + (10 - (high  % 10))
    return high


#######################################################
#                                                     #
#  Used for 'Dark Mode'.  Currently not implemented.  #
#                                                     #
#######################################################
colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}


##########################
#                        #
#  Bar chart definition  #
#                        #
##########################
fig = px.bar(
    df, 
    y=["Distinct IPs", "Connections"], 
    x="Country", 
    orientation='v', 
    height=500, 
    barmode="stack", 
    range_y=[0,calc_column_height(df)], 
)
fig.update_layout(
#    plot_bgcolor=colors['background'],  #future dark mode implementaton
#    paper_bgcolor=colors['background'], #future dark mode implementaton
#    font_color=colors['text']           #future dark mode implementaton
    yaxis=dict(title='Distinct IPs / Connection Attempts'),
#    xaxis_tickangle=45,
    legend_title_text=''
    )

##########################
#                        #
#  DASH app page layout  #
#                        #
##########################
app.layout = html.Div(children=[
    html.H1(children='Traefik External Access Attempts'),

    dcc.Graph(
        id='location-graph',
        figure=fig
    ),

    html.Div(children='''
        Log Data (most recent first)
    '''),

    html.Div(children=
        dash_table.DataTable(          # Defines log data table layout, viewed below bar chart
    		id='table',
			style_data={
            'whitespace': 'normal',
			'height': 'auto',
			'textAlign': 'left'},
			columns=[{"name": i, "id": i} for i in df2.columns],
			data=df2.to_dict('records'),
            style_header={
                'textAlign': 'left'},
            style_data_conditional=[
                {
                    'if': {
                        'column_id': 'Path',
                    },
                    'whiteSpace': 'normal',
                    'height': 'auto',   
                },
                {
                    'if': {
                        'column_id': 'Country',
                    },
                    'textAlign': 'center',
                },
                {
                    'if': {
                        'column_id': 'HTTP Response',
                    },
                    'textAlign': 'center',
                },
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ]
        ),
    ),

    dcc.Interval(                                # Defines page refresh interval
    id='interval-component',
    interval=page_refresh_interval*(60*1000),    # in milliseconds, page_refresh_interval is desired minutes between refreshes
    n_intervals=0
    )
])

#####################################################################
#                                                                   #
#  Updates bar chart with refreshed data at interval defined above  #
#                                                                   #
#####################################################################
@app.callback(Output('location-graph', 'figure'),
              Input('interval-component', 'n_intervals'))
def update_graph(n):
    update_log(log_file, traefik_ip)                       # grab latest log updates
    update_con = sl.connect('connections.db')
    update_df = pd.read_sql_query(query1, update_con)      # update the pandas dataframe
    fig = px.bar(
        update_df, 
        y=["Distinct IPs", "Connections"], 
        x="Country", 
        orientation='v', 
        height=500, 
        barmode="stack", 
        range_y=[0,calc_column_height(update_df)]
    )
    update_con.close()
    fig.update_layout(
#    plot_bgcolor=colors['background'],
#    paper_bgcolor=colors['background'],
#    font_color=colors['text']
        transition_duration=500,
#        xaxis_tickangle=45,
        yaxis=dict(title='Distinct IPs / Connection Attempts'),
        legend_title_text=''
    )
    return fig

##########################################################################
#                                                                        #
#  Updates log data table with refreshed data at interval defined above  #
#                                                                        #
##########################################################################
@app.callback(Output('table', 'data'),
    Input('interval-component', 'n_intervals'))
def update_table(n):
    update_log(log_file, traefik_ip)                       # grab latest log updates
    update_con = sl.connect('connections.db')
    update_df2 = pd.read_sql_query(query2, update_con)     # update the pandas dataframe
    update_con.close()
    return update_df2.to_dict('records')


def main():
    app.run_server(debug=True)                             # Run the DASH web app
    print()

if __name__ == '__main__':
    main()
