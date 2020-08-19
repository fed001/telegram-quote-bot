from sqlalchemy import Column, String, Boolean, UniqueConstraint, Sequence, Integer, TIME, TEXT
from sqlalchemy.ext.declarative import declarative_base
import os
import argparse
from sqlalchemy import create_engine, MetaData
from configparser import RawConfigParser


core_path = os.path.dirname(__file__)
app_path = os.path.abspath(os.path.join(core_path, os.path.pardir))
ap = argparse.ArgumentParser(description='Database Setup')
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
sql_engine = create_engine('postgresql://{}:{}@{}/{}'.format(db_user, db_pw, db_host, db_name))
metadata = MetaData(schema=db_schema)
Base = declarative_base(metadata=metadata)


class Users(Base):
    __tablename__ = 'users'
    row_id = Column(Integer, Sequence('user_id_seq', optional=True), primary_key=True)
    chat_id = Column(String(250))
    bot_type = Column(String(250), default=TEXT('telegram'))
    user_name = Column(String(250))
    comment = Column(String(250))
    awaiting_quote = Column(Boolean)
    user_id = Column(String(250))
    __table_args__ = (UniqueConstraint('chat_id', 'bot_type', 'user_name', 'user_id', name='_unique_users'),)


class Music(Base):
    __tablename__ = 'music'
    row_id = Column(Integer, Sequence('music_id_seq', optional=True), primary_key=True)
    artist = Column(String(250))
    track = Column(String(250))
    date = Column(String(250))
    time = Column(String(250))
    dj = Column(String(250))
    __table_args__ = (UniqueConstraint('artist', 'track', 'date', 'time', 'dj', name='_unique_track_dates'),
                      UniqueConstraint('artist', 'track', 'date', 'dj', name='_unique_track_dates_without_time'))


class Playlist(Base):
    __tablename__ = 'playlist'
    row_id = Column(Integer, Sequence('playlist_id_seq', optional=True), primary_key=True)
    pl_title = Column(String(250))
    pl_description = Column(String(250))
    artist = Column(String(250))
    track = Column(String(250))


class Quote(Base):
    __tablename__ = 'quote'
    row_id = Column(Integer, Sequence('quote_id_seq', optional=True), primary_key=True)
    author = Column(String(250))
    quote = Column(String(1000))
    date_added = Column(String(250))
    added_by = Column(String(250))
    type = Column(String(250))
    file_id = Column(String(250))
    __table_args__ = (UniqueConstraint('author', 'quote', 'type', 'file_id', name='_unique_quotes'),)
    __table_args__ = (UniqueConstraint('author', 'quote', 'type', name='_unique_text_quotes'),)
    __table_args__ = (UniqueConstraint('type', 'file_id', name='_unique_media_quotes'),)


class Jobs(Base):
    __tablename__ = 'jobs'
    row_id = Column(Integer, Sequence('jobs_id_seq', optional=True), primary_key=True)
    chat_id = Column(String(250))
    bot_type = Column(String(250), default=TEXT('telegram'))
    user_name = Column(String(250))
    msg_text = Column(String(250))
    msg_markup = Column(String(250))
    repeat = Column(String(250))
    interval = Column(String(250))
    last_sent_on_date = Column(String(250))
    to_send_at_time = Column(TIME(250))


class Games(Base):
    __tablename__ = 'games'
    row_id = Column(Integer, Sequence('games_id_seq', optional=True), primary_key=True)
    chat_id = Column(String(250))
    bot_type = Column(String(250))
    user_name = Column(String(250))
    game = Column(String(250))
    score = Column(String(250))
    msg_id = Column(String(250))
    inline_msg_id = Column(String(250))
    chat_instance = Column(String(250))
    to_update = Column(Boolean)
    __table_args__ = (UniqueConstraint('chat_id', 'bot_type', 'user_name', 'game', 'msg_id', 'inline_msg_id',
                                       'chat_instance', name='_unique_games'),)


class Location(Base):
    __tablename__ = 'location'
    row_id = Column(Integer, Sequence('location_id_seq', optional=True), primary_key=True)
    latitude = Column(String(250))
    longitude = Column(String(250))
    title = Column(String(250))
    address = Column(String(250))
    __table_args__ = (UniqueConstraint('latitude', 'longitude', 'title', 'address', name='_unique_locations'),)


class Cache(Base):
    __tablename__ = 'cache'
    row_id = Column(Integer, Sequence('cache_id_seq', optional=True), primary_key=True)
    platform = Column(String(250), default=TEXT('spotify'))
    playlist_title = Column(String(250))
    playlist_id = Column(String(250))
    video_id = Column(String(250))
    date = Column(String(250), default='current_date')
    __table_args__ = (UniqueConstraint('platform', 'playlist_title', 'playlist_id', 'video_id', 'date',
                                       name='_unique_cache'),)


Base.metadata.create_all(bind=sql_engine)
sql_engine.execute("""ALTER TABLE {schema}."cache" ALTER COLUMN platform SET DEFAULT 'spotify';
ALTER TABLE {schema}."cache" ALTER COLUMN "date" SET DEFAULT current_date;
ALTER TABLE {schema}.jobs ALTER COLUMN bot_type SET DEFAULT 'telegram';
ALTER TABLE {schema}.jobs ALTER COLUMN to_send_at_time TYPE time(6) USING to_send_at_time::time;
ALTER TABLE {schema}.jobs ALTER COLUMN to_send_at_time SET DEFAULT time '09:00:00';
ALTER TABLE {schema}.users ALTER COLUMN bot_type SET DEFAULT 'telegram';
ALTER TABLE {schema}.users ALTER COLUMN awaiting_quote SET DEFAULT false;
ALTER TABLE {schema}."quote" ALTER COLUMN date_added SET DEFAULT current_date;
ALTER TABLE {schema}."quote" ADD CONSTRAINT "_unique_text_quotes" UNIQUE (author,"quote","type");
ALTER TABLE {schema}."quote" ADD CONSTRAINT "_unique_media_quotes" UNIQUE ("type",file_id);
CREATE INDEX users_user_id_idx ON {schema}.users (user_id);""".format(schema=db_schema))
#one time
# ALTER TABLE public."quote" RENAME COLUMN time_added TO date_added;
