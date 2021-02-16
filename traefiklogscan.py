import os
import configparser
import requests
import json
import IP2Location
import sqlite3 as sl

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


def process_log(log_file, traefik_ip):
    ipdb = IP2Location.IP2Location(os.path.join("", "IP2LOCATION.BIN"))
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
    con.close()


#def query_data():
#    query = "SELECT count(DISTINCT ip) as ip, country_short from connections group by country_short"
#    cur.execute(query)
#    records = cur.fetchall()
#    for record in records:
#        print(record)


def load_config(config_file, config_section):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if os.path.isfile(dir_path + '/' + config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        logfile = config.get(config_section, 'logfile')
        traefik_ip = config.get(config_section, 'ip')
        if traefik_ip == 'dynamic':
            url = 'http://ipinfo.io/json'
            response = requests.get(url)
            data = response.json()
            traefik_ip = data['ip']
    return logfile, traefik_ip

def main():
    config_file = 'config.ini'
    config_section = 'dev'
    log_file, traefik_ip = load_config(config_file, config_section)
    process_log(log_file, traefik_ip)


if __name__ == '__main__':
    main()
