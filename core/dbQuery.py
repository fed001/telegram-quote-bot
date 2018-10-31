#-*- coding: UTF-8 -*-
import sqlite3
from core.constants import db_path


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
