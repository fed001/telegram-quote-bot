from datetime import datetime
import re
from core.constants import sql_session, users
from core.tools import is_not_empty
from sqlalchemy import func, and_
from core.constants import quote
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound


class TextDeco(object):
    def __init__(self, decoratee):
        self._decoratee = decoratee
        self.item = 'Text'

    def __getattr__(self, name):
        return getattr(self._decoratee, name)

    def process_input(self, dia):
        if dia.user is not '':
            try:
                user_exists = sql_session.query(users).filter(
                    users.c.CHAT_ID == dia.chat_id).one()
            except MultipleResultsFound as e:
                print(e)
            except NoResultFound:
                pass
            if not user_exists:
                try:
                    sql_session.execute(users.insert(
                        [dia.chat_id, dia.bot_type, dia.user, '', 0, dia.user_id]))
                except sqlalchemy.exc.IntegrityError as e:
                    print(e)
            else:
                sql_session.execute(
                    users.update().values(
                        USER_ID = dia.user_id
                    ).where(
                        users.c.CHAT_ID == self.chat_id
                    )
                )
        try:
            is_awaiting_quote = sql_session.query(users).filter(
                and_(
                    users.c.AWAITING_QUOTE == 1,
                    users.c.CHAT_ID == dia.user_id
                )
            ).one()
        except MultipleResultsFound as e:
            print(e)
            return
        except NoResultFound:
            return

        in_msg_body_lower = ''
        in_msg_body_lower = dia.InMsg.in_msg_body.lower().replace('/', '')
        in_msg_body_lower = re.sub(r"@.+", "", in_msg_body_lower)

        if is_awaiting_quote is not None and dia.type == 'private':
            i = 0
            data = in_msg_body_lower.split('\n')
            for item in data:
                data_piece = item.split(' - ')
                if len(data_piece) == 2:
                    author = data_piece[0]
                    quote_text = data_piece[1]
                    if is_not_empty(author) and is_not_empty(quote_text):
                        try:
                            rowcount = sql_session.execute(quote.insert(
                                [author,
                                 quote_text,
                                 func.now(),
                                 dia.user_id,
                                 'text',
                                 None]).prefix_with("OR IGNORE")).rowcount
                        except sqlalchemy.exc.IntegrityError as e:
                            print(e)
                        i += rowcount
                else:
                    continue
            dia.check_incoming_quote(i, in_msg_body_lower)

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
