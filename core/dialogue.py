# -*- coding: UTF-8 -*-
import re
import time
from sqlalchemy import *
from core.constants import help_text, sql_session, users, jobs, abort_text, quote_invalid_text, quote_not_found_text,\
    quote_success_text, not_subscribed_text, removing_subscription_text, already_subscribed_text, \
    adding_subscription_text, subscription_not_private_text, quote_not_private_text
from core.dbQuery import query, insert


class Dialogue(object):
    def __init__(self, chat_id, bot_type, user, args = None):
        self.chat_id = chat_id
        self.bot_type = bot_type
        self.user = user
        self.job_dial = []
        self.msg = None
        if args is not None:
            self.game_flag = args['game']
        else:
            self.game_flag = False

    def send_typing_status(self):
        pass

    def is_user_in_jobs(self):
        row_exists = sql_session.query(jobs).filter(
            and_(jobs.c.CHAT_ID == self.user_id, jobs.c.BOT_TYPE == self.bot_type))

        if row_exists.first():
            return True
        else:
            return False

    def get_rdm_quote(self):
        try:
            quote_rows = self.perform_quote_select()
            if quote_rows is not None:
                raw_quote = quote_rows[0]
                author = quote_rows[1]
                type = quote_rows[2]
                file_id = quote_rows[3]
            else:
                raw_quote = quote_not_found_text
                author = "system"
                type = 'text'
                file_id = None
            if author is not None:
                author = author.title()
            if raw_quote is not None:
                if len(re.findall(r'\W', raw_quote[-1])) == 0:
                    formatted_quote = raw_quote[0].title() + raw_quote[1:] + '.'
                else:
                    formatted_quote = raw_quote[0].title() + raw_quote[1:]

            self.OutMsg.file_id = file_id
            time.sleep(0.1)
            self.OutMsg.item = type
            if type == 'text':
                self.format_quote(author, formatted_quote)
        except Exception as e:
            print(e)

    def format_quote(self, author, quote):
        pass

    def check_quote(self, i, in_msg_body_lower):
        if i == 0:
            if in_msg_body_lower == 'abort':
                self.stop_awaiting_quote()
                self.OutMsg.answer = abort_text
            else:
                self.OutMsg.answer = quote_invalid_text
        else:
            self.OutMsg.answer = quote_success_text.format(i)

    def perform_quote_select(self):
        pass

    def process_output(self):
        skip_cleanup = False
        is_awaiting_quote = sql_session.query(users).filter(
            and_(or_(users.c.AWAITING_QUOTE is True, users.c.AWAITING_QUOTE == 1), users.c.CHAT_ID == self.user_id)).first()
        in_msg_body_lower = ''
        if hasattr(self.InMsg, 'in_msg_body') and self.InMsg.in_msg_body is not None:
            in_msg_body_lower = self.InMsg.in_msg_body.lower().replace('/', '')
        in_msg_body_lower = re.sub(r"@.+", "", in_msg_body_lower)
        if any(ext == in_msg_body_lower for ext in ['help', 'start']):
            self.OutMsg.disable_web_page_preview = 'True'
            self.OutMsg.answer = help_text
        elif in_msg_body_lower == 'update':
            self.handle_jobs()
            return
        elif in_msg_body_lower == 'pong'and self.game_flag:
            self.OutMsg.markup_type = 'game'
        elif in_msg_body_lower == 'addquote':
            skip_cleanup = True
            self.send_typing_status()
            self.OutMsg.answer = """OK, you can either send me an Audio File, Video File, Voice Note, Picture or type a list of Text Quotes in the following format:

Author1 - Text
Author2 - Another Text
                """
            insert("""UPDATE USERS SET AWAITING_QUOTE = 1 WHERE CHAT_ID LIKE ?;""", (self.user_id,))
        elif in_msg_body_lower == 'quote':
            self.send_typing_status()
            self.get_rdm_quote()
        elif in_msg_body_lower == 'unsubscribe':
            self.send_typing_status()
            if self.is_user_in_jobs():
                self.OutMsg.answer = removing_subscription_text.format(self.user)
                insert("""DELETE FROM JOBS WHERE BOT_TYPE LIKE ? AND CHAT_ID LIKE ?""",
                       (self.bot_type, self.user_id))
            else:
                self.OutMsg.answer = not_subscribed_text.format(self.user)
        elif in_msg_body_lower == 'subscribe':
            self.send_typing_status()
            is_user_in_subscribers = self.is_user_in_jobs()
            if is_user_in_subscribers:
                self.OutMsg.answer = already_subscribed_text.format(self.user)
            elif not is_user_in_subscribers:
                if self.type == 'private':
                    repeat = 'true'
                    interval = 'daily'
                    self.OutMsg.answer = adding_subscription_text.format(self.user)
                    insert("""INSERT OR IGNORE INTO JOBS VALUES (?, ?, ?, ?, ?, ?, ?, NULL, '09:00:00')""",
                           (self.user_id, self.bot_type, self.user, 'quote', 1, repeat, interval))
                else:
                    self.OutMsg.answer = subscription_not_private_text.format(self.user)
        elif is_awaiting_quote is not None and (self.OutMsg.answer is None or self.OutMsg.answer == '') \
            and self.type != 'private':
            skip_cleanup = True
            self.send_typing_status()
            self.OutMsg.answer = quote_not_private_text.format(self.user)
        else:
            skip_cleanup = True

        if skip_cleanup is False:
            self.stop_awaiting_quote()

        self.OutMsg.prepare_kwargs()

    def stop_awaiting_quote(self):
        insert("""UPDATE USERS SET AWAITING_QUOTE = 0 WHERE CHAT_ID LIKE ?""", (self.user_id,))

    def handle_jobs(self):
        jobs = query("""SELECT *, ROWID, TO_SEND_AT_TIME AS C
                        FROM JOBS WHERE BOT_TYPE LIKE ?
                        AND (LAST_SENT_ON_DATE IS NULL OR LAST_SENT_ON_DATE < DATE('NOW'))
                        AND TIME('NOW', 'LOCALTIME') > C""", (self.bot_type, ))
        i = 0
        for job in jobs:
            chat_id = job[0]
            user = job[2]
            self.job_dial.append(self.create_dlg(chat_id, user))
            self.job_dial[i].OutMsg.answer = job[3]
            self.job_dial[i].OutMsg.chat_id = chat_id
            self.job_dial[i].OutMsg.user = user
            if self.job_dial[i].OutMsg.answer == 'quote':
                self.job_dial[i].get_rdm_quote()
            self.job_dial[i].format_required = job[4]
            if self.job_dial[i].format_required:
                self.job_dial[i].OutMsg.parse_mode = 'markdown'
            self.job_dial[i].repeat = job[5]
            self.job_dial[i].interval = job[6]
            self.job_dial[i].row_id = job[9]
            self.job_dial[i].OutMsg.prepare_kwargs()
            self.job_dial[i].stop_awaiting_quote()
            i += 1

