import os
import configparser
import requests
import re
import json
import ipinfo
from tinydb import TinyDB, Query

ipinfo_token = 'c2f7ab93d0969a'
handler = ipinfo.getHandler(ipinfo_token)
db = TinyDB('traefik.db')

def process_log(log_file, traefik_ip):
    db.truncate()
    data = []
    i = 0
    with open('traefik.json') as f:
        for line in f:
            data.append(json.loads(line))
            if data[i]['ClientHost'] != traefik_ip:
                details = handler.getDetails(data[i]['ClientHost'])
                db.insert({'OriginIP': data[i]['ClientHost'], 'RequestHost': data[i]['RequestHost'], 'RequestPort': data[i]['RequestPort'], 'RequestMethod': data[i]['RequestMethod'], 'RequestPath': data[i]['RequestPath'], 
                    'RequestProtocol': data[i]['RequestProtocol'], 'RequestScheme': data[i]['RequestScheme'], 'RouterName': data[i]['RouterName'], 'Time': [data[i]['time']], 'City': details.city, 'Country': details.country}) 






#            details = handler.getDetails(data[i]['ClientHost'])
#            db.insert(details.all)
#            print(details.all)
            i = i + 1





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
        ipinfo_token = config.get(config_section, 'ipinfo_token')
    return logfile, traefik_ip, ipinfo_token

def main():
    config_file = 'config.ini'
    config_section = 'dev'
#    log_file_name = load_config(config_file, config_section)
    log_file, traefik_ip, ipinfo_token = load_config(config_file, config_section)

#    print(log_file, traefik_ip)

    process_log(log_file, traefik_ip)


if __name__ == '__main__':
    main()
