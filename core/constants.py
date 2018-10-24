#-*- coding: UTF-8 -*-
import os
import sys
from os.path import expanduser
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import create_session
if sys.version_info > (3,):  # python 3
    import configparser as ConfigParser
else:  # python 2
    import ConfigParser


home_path = expanduser("~")
core_path = os.path.dirname(__file__)
app_path = os.path.abspath(os.path.join(core_path, os.path.pardir))
configParser = ConfigParser.RawConfigParser()
configFilePath = r'{}/wolfg.cfg'.format(app_path)
configParser.read(configFilePath)
db_path = os.path.join(app_path, 'db/mydb.db')
log_path = os.path.join(app_path, 'log')
game_path = os.path.join(app_path, 'games')
html_path = os.path.join(app_path, 'playlists/create_online_playlist.html')
pong_html_path = os.path.join(app_path, 'games/pong/index.html')
yt_channel_id = configParser.get('youtube', 'channel_id')
help_text = configParser.get('general', 'help_text')
abort_text = configParser.get('general', 'abort_text')
quote_invalid_text = configParser.get('general', 'quote_invalid_text')
quote_not_found_text = configParser.get('general', 'quote_not_found_text')
quote_success_text = configParser.get('general', 'quote_success_text')
not_subscribed_text = configParser.get('general', 'not_subscribed_text')
removing_subscription_text = configParser.get('general', 'removing_subscription_text')
already_subscribed_text = configParser.get('general', 'already_subscribed_text')
adding_subscription_text = configParser.get('general', 'adding_subscription_text')
subscription_not_private_text = configParser.get('general', 'subscription_not_private_text')
quote_not_private_text = configParser.get('general', 'quote_not_private_text')
sp_user_id = configParser.get('spotify', 'user_id')
exclamation_mark_pic_url = configParser.get('general', 'exclamation_mark_pic_url')
sp_username = configParser.get('spotify', 'username')

apis = []
apis.append('spotify')
apis.append('youtube')

sql_engine = create_engine('sqlite:///' + db_path)
sql_engine.echo = False
sql_session = create_session()
metadata = MetaData(sql_engine)
users = Table('users', metadata, autoload = True)
quote = Table('quote', metadata, autoload = True)
jobs = Table('jobs', metadata, autoload = True)
