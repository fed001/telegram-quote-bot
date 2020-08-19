import os
import argparse
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import create_session
from configparser import RawConfigParser
import logging


core_path = os.path.dirname(__file__)
app_path = os.path.abspath(os.path.join(core_path, os.path.pardir))
ap = argparse.ArgumentParser(description='telegram_quote_bot')
ap.add_argument('--config', default='telegram_quote_bot.cfg', help='absolute config file path')
args = vars(ap.parse_args())
config_parser = RawConfigParser()
config_file_path = r'{}'.format(args['config'])
config_parser.read(config_file_path)
db_name = config_parser.get('database', 'name')
db_host = config_parser.get('database', 'host')
db_user = config_parser.get('database', 'user')
db_pw = config_parser.get('database', 'pw')
db_schema = config_parser.get('database', 'schema')
game_path = os.path.join(app_path, 'games')
pong_html_path = os.path.join(app_path, 'games/pong/index.html')
help_text = config_parser.get('general', 'help_text')
raw_log_level = config_parser.get('general', 'log_level')
raw_log_level_sqlalchemy = config_parser.get('general', 'log_level_sqlalchemy')
threads = config_parser.getint('general', 'threads')
threaded = threads != 1
log_level_dict = {'error': logging.ERROR,
                  'warn': logging.WARN,
                  'info': logging.INFO,
                  'debug': logging.DEBUG}
log_level = log_level_dict[raw_log_level]
log_level_sqlalchemy = log_level_dict[raw_log_level_sqlalchemy]
spotify_flag = config_parser.getboolean('spotify', 'enabled')
sp_user_id = config_parser.get('spotify', 'user_id')
sp_username = config_parser.get('spotify', 'username')
client_id = config_parser.get('spotify', 'client_id')
redirect_uri = config_parser.get('spotify', 'redirect_uri')
client_secret = config_parser.get('spotify', 'client_secret')
os.environ['SPOTIPY_REDIRECT_URI'] = redirect_uri
os.environ['SPOTIPY_CLIENT_SECRET'] = client_secret
os.environ['SPOTIPY_CLIENT_ID'] = client_id
tele_group_chat_id = config_parser.get('telegram', 'group_chat_id')
tele_job_user_id = config_parser.get('telegram', 'tele_job_user_id')
token = config_parser.get('telegram', 'token')
apis = ['spotify']
sql_engine = create_engine('postgresql://{}:{}@{}/{}'.format(db_user, db_pw, db_host, db_name))
sql_engine.echo = False
sql_session = create_session()
metadata = MetaData(sql_engine)
users = Table('users', metadata, autoload=True, schema=db_schema)
quote = Table('quote', metadata, autoload=True, schema=db_schema)
jobs = Table('jobs', metadata, autoload=True, schema=db_schema)
