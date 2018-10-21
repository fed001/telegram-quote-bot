from sqlalchemy import Column, String, Boolean, MetaData, UniqueConstraint, create_engine
from sqlalchemy.ext.declarative import declarative_base

sql_engine = create_engine('sqlite:///my2.db')
Base = declarative_base()
metadata = MetaData()


class Users(Base):
    __tablename__ = 'USERS'
    CHAT_ID = Column(String(250), primary_key = True)
    BOT_TYPE = Column(String(250), nullable = False)
    USER_NAME = Column(String(250), nullable = False)
    COMMENT = Column(String(250), nullable = False)
    AWAITING_QUOTE = Column(Boolean, nullable = False)
    USER_ID = Column(String(250), nullable = False)
    __table_args__ = (UniqueConstraint('CHAT_ID', 'BOT_TYPE', 'USER_NAME', 'USER_ID', name = '_unique_users'),)


class Music(Base):
    __tablename__ = 'MUSIC'
    ARTIST = Column(String(250), primary_key = True)
    TRACK = Column(String(250))
    DATE = Column(String(250))
    TIME = Column(String(250))
    DJ = Column(String(250))
    __table_args__ = (UniqueConstraint('ARTIST', 'TRACK', 'DATE', 'TIME', 'DJ', name = '_unique_music'),)


class Playlist(Base):
    __tablename__ = 'PLAYLIST'
    KEY = Column(String(250), primary_key = True)
    PL_TITLE = Column(String(250))
    PL_DESCRIPTION = Column(String(250))
    ARTIST = Column(String(250))
    TRACK = Column(String(250))


class Quote(Base):
    __tablename__ = 'QUOTE'
    AUTHOR = Column(String(250))
    QUOTE = Column(String(250), primary_key = True, nullable = True)
    TIME_ADDED = Column(String(250))
    ADDED_BY = Column(String(250))
    TYPE = Column(String(250))
    FILE_ID = Column(String(250), primary_key = True, nullable = True)


class Jobs(Base):
    __tablename__ = 'JOBS'
    CHAT_ID = Column(String(250), primary_key = True)
    BOT_TYPE = Column(String(250), primary_key = True)
    USER_NAME = Column(String(250), primary_key = True)
    MSG_TEXT = Column(String(250), primary_key = True)
    MSG_MARKUP = Column(String(250))
    REPEAT = Column(String(250))
    INTERVAL = Column(String(250))
    LAST_SENT_ON_DATE = Column(String(250))
    TO_SEND_AT_TIME = Column(String(250))
    __table_args__ = (UniqueConstraint('CHAT_ID', 'BOT_TYPE', 'USER_NAME', 'MSG_TEXT', name = '_unique_jobs'),)


class Games(Base):
    __tablename__ = 'GAMES'
    CHAT_ID = Column(String(250), primary_key = True)
    BOT_TYPE = Column(String(250), primary_key = True)
    USER_NAME = Column(String(250), primary_key = True)
    GAME = Column(String(250), primary_key = True)
    SCORE = Column(String(250))
    MSG_ID = Column(String(250), primary_key = True)
    INLINE_MSG_ID = Column(String(250), primary_key = True)
    CHAT_INSTANCE = Column(String(250), primary_key = True)
    TO_UPDATE = Column(Boolean)
    __table_args__ = (UniqueConstraint('CHAT_ID', 'BOT_TYPE', 'USER_NAME', 'GAME', 'MSG_ID', 'INLINE_MSG_ID',
                                       'CHAT_INSTANCE', name = '_unique_games'),)


class Location(Base):
    __tablename__ = 'LOCATION'
    LATITUDE = Column(String(250), primary_key = True)
    LONGITUDE = Column(String(250), primary_key = True)
    TITLE = Column(String(250), primary_key = True)
    ADDRESS = Column(String(250), primary_key = True)
    __table_args__ = (UniqueConstraint('LATITUDE', 'LONGITUDE', 'TITLE', 'ADDRESS', name = '_unique_locations'),)


class Cache(Base):
    __tablename__ = 'CACHE'
    PLATFORM = Column(String(250), primary_key = True)
    PLAYLIST_TITLE = Column(String(250), primary_key = True)
    PLAYLIST_ID = Column(String(250), primary_key = True)
    VIDEO_ID = Column(String(250), primary_key = True)
    DATE = Column(String(250), primary_key = True)
    __table_args__ = (UniqueConstraint('PLATFORM', 'PLAYLIST_TITLE', 'PLAYLIST_ID', 'VIDEO_ID', 'DATE',
                                       name = '_unique_cache'),)


Base.metadata.create_all(bind = sql_engine)
