import os
import configparser
import requests
import re
import json
import ipinfo
from tinydb import TinyDB, Query

db = TinyDB('traefik.db')

def process_log(ipinfo_handler, log_file, traefik_ip):
    db.truncate()
    data = []
    i = 0
    with open(log_file) as f:
        for line in f:
            data.append(json.loads(line))
        while i < len(data):
            if data[i]['ClientHost'] != traefik_ip:
                details = ipinfo_handler.getDetails(data[i]['ClientHost'])
                db.insert({'OriginIP': data[i]['ClientHost'], 'RequestMethod': data[i]['RequestMethod'], 'RequestPath': data[i]['RequestPath'], 'RequestProtocol': data[i]['RequestProtocol'], 
                    'RequestScheme': data[i]['RequestScheme'], 'StatusCode': data[i]['DownstreamStatus'], 'Time': [data[i]['time']], 'City': details.city, 'Country': details.country}) 
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
    log_file, traefik_ip, ipinfo_token = load_config(config_file, config_section)
    ipinfo_handler = ipinfo.getHandler(ipinfo_token)

    process_log(ipinfo_handler, log_file, traefik_ip)


if __name__ == '__main__':
    main()
