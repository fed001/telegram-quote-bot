from sqlalchemy import Column, String, Boolean, MetaData, UniqueConstraint, create_engine
from sqlalchemy.ext.declarative import declarative_base

sql_engine = create_engine('sqlite:///mydb.db')
Base = declarative_base()
metadata = MetaData()


class Users(Base):
    __tablename__ = 'USERS'
    CHAT_ID = Column(String(250), primary_key = True)
    BOT_TYPE = Column(String(250), nullable = False)
    USER_NAME = Column(String(250), nullable = False)
    COMMENT = Column(String(250), nullable = True)
    AWAITING_QUOTE = Column(Boolean, nullable = False)
    USER_ID = Column(String(250), nullable = False)
    __table_args__ = (UniqueConstraint('CHAT_ID', 'BOT_TYPE', 'USER_NAME', 'USER_ID', name = '_unique_users'),)


class Quote(Base):
    __tablename__ = 'QUOTE'
    AUTHOR = Column(String(250))
    QUOTE = Column(String(250), primary_key = True, nullable = True, unique = True)
    TIME_ADDED = Column(String(250))
    ADDED_BY = Column(String(250))
    TYPE = Column(String(250))
    FILE_ID = Column(String(250), primary_key = True, nullable = True, unique = True)


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


class Scores(Base):
    __tablename__ = 'SCORES'
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
                                       'CHAT_INSTANCE', name = '_unique_scores'),)


class Games(Base):
    __tablename__ = 'GAMES'
    GAME_NAME = Column(String(250), primary_key = True)
    GAME_SHORT_NAME = Column(String(250), primary_key = True)
    __table_args__ = (UniqueConstraint('GAME_NAME', 'GAME_SHORT_NAME', name = '_unique_games'),)


Base.metadata.create_all(bind = sql_engine)
