from datetime import datetime
import re
from core.constants import sql_session, users
from core.dbQuery import query, insert
from core.tools import is_not_empty


class TextDeco(object):
    def __init__(self, decoratee):
        self._decoratee = decoratee
        self.item = 'Text'

    def __getattr__(self, name):
        return getattr(self._decoratee, name)

    def process_input(self, dia):
        if dia.user is not '':
            user_exists = sql_session.query(users).filter(
                users.c.CHAT_ID == dia.chat_id)
            if not user_exists.first():
                insert("""INSERT INTO USERS VALUES (?, ?, ?, '', 0, ?)""",
                       (dia.chat_id, dia.bot_type, dia.user, dia.user_id))
            else:
                insert("""UPDATE USERS SET USER_ID = ? WHERE CHAT_ID LIKE ?""", (dia.user_id, dia.chat_id))
        is_awaiting_quote = query("""SELECT AWAITING_QUOTE FROM USERS WHERE AWAITING_QUOTE = 1
                                     AND CHAT_ID LIKE ?;""", (dia.user_id,))
        in_msg_body_lower = ''
        in_msg_body_lower = dia.InMsg.in_msg_body.lower().replace('/', '')
        in_msg_body_lower = re.sub(r"@.+", "", in_msg_body_lower)
        if any(cmd == in_msg_body_lower for cmd in ['help', 'start']):
            self.disable_web_page_preview = 'True'
            self.markup_type = 'text'
        elif in_msg_body_lower == 'addquote':
            insert("""UPDATE USERS SET AWAITING_QUOTE = 1 WHERE CHAT_ID LIKE ?;""", (dia.user_id,))
        elif in_msg_body_lower == 'quote':
            self.markup_type = 'text'
        elif len(is_awaiting_quote) > 0 and dia.type == 'private':
            i = 0
            data = in_msg_body_lower.split('\n')
            for item in data:
                data_piece = item.split(' - ')
                if len(data_piece) == 2:
                    author = data_piece[0]
                    quote = data_piece[1]
                    if is_not_empty(author) and is_not_empty(quote):
                        rowcount = insert(
                            """INSERT OR IGNORE INTO QUOTE VALUES (?, ?, DATE('NOW'), ?, 'text', NULL)""",
                            (author, quote, dia.user_id))
                        i += rowcount
                else:
                    break
            dia.check_quote(i, in_msg_body_lower)

    def print_in_msg(self, dia):
        if hasattr(dia, 'type') and dia.type == 'pseudo':
            return

        print(str(datetime.now()), '{0} from {1} (Chat ID = {2}, User ID = {3}). Text from User = {4}'.format(
            self.item, self.user, str(self.chat_id), str(self.user_id), self.in_msg_body.encode('utf-8')))

    def print_out_msg(self):
        logged_answer = self.answer
        if logged_answer is None:
            logged_answer = ''
        if self.my_url and self.my_url != '':
            logged_answer = logged_answer + ' ' + self.my_url

        try:
            print(str(datetime.now()), 'Responding {0} (Chat ID = {1}, User ID = {2}). Answer from Bot = {3}'.format(
                                        self.user, self.chat_id, self.user_id, logged_answer.encode('utf-8')))
        except UnicodeDecodeError:
            print(str(datetime.now()), 'Responding {0} (Chat ID = {1}, User ID = {2}). Answer from Bot = {3}'.format(
                self.user, self.chat_id, self.user_id, logged_answer))
        except Exception as e:
            print(e)
