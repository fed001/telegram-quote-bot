import random
import re
from time import sleep
import logging
from telegram_quote_bot.db_query import query, insert

logger = logging.getLogger('TeleBot')


def is_not_empty(string):
    if string is not None and len(re.findall(r'(\S+)', string)) > 0:
        return True
    else:
        return False


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


def go_sleep(limit):
    logger.info("Sleeping {} second(s)...".format(limit))
    seconds = random.randint(1, limit)
    sleep(seconds)


def get_result_message(inserted_rows):
    ret_val = """Error! Invalid Format or duplicate? Try again or /abort""" if inserted_rows == 0 \
            else """Success! {} Quote(s) inserted in Database. Send me more Quotes anytime or /abort to stop adding Quotes.""".format(inserted_rows)
    return ret_val


def user_is_fiehe_subscriber(user_id):
    row_exists = query("""SELECT EXISTS(SELECT 1 FROM "jobs" WHERE chat_id = %s AND interval = 'on fiehe pl');""",
                       (user_id,))
    ret_val = True if row_exists[0][0] else False
    return ret_val


def user_is_quote_subscriber(user_id):
    row_exists = query("""SELECT EXISTS(SELECT 1 FROM "jobs" WHERE chat_id = %s AND interval = 'daily');""", (user_id,))
    ret_val = True if row_exists[0][0] else False
    return ret_val


def get_subscribed_time(user_id):
    row = query("""SELECT to_send_at_time FROM "jobs" WHERE chat_id = %s AND interval = 'daily';""", (user_id,))
    ret_val = str(row[0][0]) if len(row) > 0 and row[0] is not None and len(row[0]) > 0 and row[0][0] is not None \
        else None
    return ret_val


def get_random_quote_from_dict(quote_list):
    random_index = random.randint(0, len(quote_list) - 1)
    return quote_list[random_index]


def get_quote_list():
    return query("""select quote, author, type, file_id from "quote" order by random()""")


def get_user_dict():
    user_list = query("""select chat_id, user_name, comment, awaiting_quote, user_id from "users";""")
    user_dict = {}
    for user in user_list:
        user_dict[user[4]] = {'chat_id': user[0], 'user_name': user[1], 'comment': user[2], 'awaiting_quote': user[3],
                              'user_id': user[4]}
    return user_dict


def get_job_dict():
    job_list = query("""select row_id, chat_id, user_name, msg_text, msg_markup, repeat, interval, last_sent_on_date,
                        to_send_at_time from "jobs";""")
    job_dict = {}
    for job in job_list:
        job_dict[job[0]] = {'row_id': job[0], 'chat_id': job[1], 'user_name': job[2], 'msg_text': job[3],
                            'msg_markup': job[4], 'repeat': job[5], 'interval': job[6], 'last_sent_on_date': job[7],
                            'to_send_at_time': job[8]}
    return job_dict


def update_database(repeat, interval, row_id, job_handler):
    if repeat == 'true':
        if interval == 'on fiehe pl':
            insert("""UPDATE "jobs" SET msg_text = NULL WHERE row_id = %s;""", (row_id,))
        else:
            insert("""UPDATE "jobs" SET last_sent_on_date = current_date WHERE row_id = %s;""", (row_id,))
    else:
        insert("""DELETE FROM "jobs" WHERE row_id = %s;""", (row_id,))
    job_handler.update()


def stop_awaiting_quote(user_id, user_handler):
    insert("""UPDATE "users" SET awaiting_quote = 'False', comment = '' WHERE user_id = %s;""", (user_id,))
    user_handler.update_dict()


def is_new_subscription_time(chat_type, message_text):
    return chat_type == 'private' and message_text is not None and len(message_text) == 5\
           and message_text[2] == ':' and message_text[0:2].isdigit() and message_text[3:].isdigit()


def tele_get_user(first_name, last_name, username):
    has_first_name = first_name is not None
    has_last_name = last_name is not None
    has_user_name = username is not None
    ret_val = None
    if has_first_name and has_last_name:
        ret_val = first_name + ' ' + last_name
    elif has_first_name:
        ret_val = first_name
    elif has_last_name:
        ret_val = last_name
    elif has_user_name:
        ret_val = username
    return ret_val


def get_formatted_quote(author, quote):
    formatted_quote = quote[0].title() + quote[1:] + '.' if len(re.findall(r'\W', quote[-1])) == 0 \
                else quote[0].title() + quote[1:]
    return formatted_quote + '\n\n_' + author.title() + '_'
