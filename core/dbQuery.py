#-*- coding: UTF-8 -*-
import os
import random
import re
import sqlite3

import constants
from core.constants import db_path


# for DB use
def clean_up_string(input_string):
    try:
        input_string = input_string.replace('&#8217;', '\'\'')
        input_string = input_string.replace('&#038;', '&')
        input_string = input_string.replace('&#036;', '$')
        input_string = input_string.replace('&#8220;', '""')
        input_string = input_string.replace('&#8221;', '""')
        input_string = input_string.replace('&#8211;', '-')
        input_string = input_string.replace('&#39;', "")
        input_string = input_string.replace('\\', '')
        input_string = input_string.replace('"', '""')
        return my_strip(input_string)
    except Exception as exc:
        print 'Exception occurred: ', str(exc)


def my_strip(input_string):
    if input_string:
        while re.match('^[\w-]', input_string) is None:
            if input_string[-1] == '.' \
                    or input_string[-1] == ')'\
                    or input_string[-1] == '?'\
                    or input_string[-1] == '!':
                break
            start_pos = re.search(r'^[\w-]', input_string).start()
            input_string = input_string[:start_pos] + input_string[start_pos + 1:]
            if len(input_string) == 0:
                break
        return input_string
    else:
        return None


def query(command, arguments = [], debug = False):
    db = sqlite3.connect(db_path)
    db.text_factory = str
    cursor = db.cursor()
    if debug:
        print("Executing command {} with arguments {}.".format(command, arguments))
    cursor.execute(command, arguments)
    result = cursor.fetchall()
    db.close()
    if debug:
        print("SQL Query result: {}.".format(result))
    return result


def insert(command, arguments = [], debug = False):
    db = sqlite3.connect(db_path)
    db.text_factory = str
    cursor = db.cursor()
    if debug:
        print("Executing command {} with arguments {}.".format(command, arguments))
    cursor.execute(command, arguments)
    db.commit()
    result = cursor.rowcount
    db.close()
    if debug:
        print("SQL Insert affected {} row(s).".format(result))
    return result


def clean_data(row):
    data = row.rstrip()
    from core.tools import my_rstrip
    data = my_rstrip(data)
    return data
