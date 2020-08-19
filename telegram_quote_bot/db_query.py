import psycopg2
from psycopg2 import extras
import logging
from telegram_quote_bot.config import db_host, db_user, db_pw, db_name, db_schema, log_level
log_level_is_debug = log_level == logging.DEBUG
conn = psycopg2.connect('host={} user={} password={} dbname={}'.format(db_host, db_user, db_pw, db_name))
conn.set_session(autocommit=True)
logger = logging.getLogger('TeleBot')


def query(command, arguments=None):
    cursor = conn.cursor()
    cursor.execute("SET search_path TO " + db_schema)
    logger.debug("Executing command {} with arguments {}.".format(command, arguments))
    if arguments is None:
        cursor.execute(command)
    else:
        cursor.execute(command, arguments)
    result = cursor.fetchall()
    logger.debug("SQL Query result: {}.".format(result))
    return result


def insert(command, arguments=None):
    cursor = conn.cursor()
    cursor.execute("SET search_path TO " + db_schema)
    logger.debug("Executing command {} with arguments {}.".format(command, arguments))
    if arguments is None:
        cursor.execute(command)
    else:
        cursor.execute(command, arguments)
    result = cursor.rowcount
    logger.debug("SQL Insert affected {} row(s).".format(result))
    return result


def insert_multiple(command, arguments):
    cursor = conn.cursor()
    extras.execute_values(cursor, command, arguments)
    result = cursor.rowcount
    logger.debug("SQL Insert affected {} row(s).".format(result))
    return result
