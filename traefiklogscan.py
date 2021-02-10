import re
from tinydb import TinyDB

def parse_log:
    



def load_config(config_file, config_section):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if os.path.isfile(dir_path + '/' + config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        logfile = config.get(config_section, 'logfile')
    return log_file

def main():
    config_file = 'config.ini'
    config_section = 'dev'
    log_file = load_config(config_file, config_section)
    log_db = TinyDB(log_file)


if __name__ == '__main__':
    main()
