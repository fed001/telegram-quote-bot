from datetime import datetime
from sqlalchemy import and_, func, or_
from core.constants import sql_session, users, quote
from core.dbQuery import insert
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound


class NonTextDeco(object):
    def __init__(self, decoratee):
        self._decoratee = decoratee

    def __getattr__(self, name):
        return getattr(self._decoratee, name)

    def process_input(self, dia):
        if self.user is not '':
            user_exists = sql_session.query(users.c.USER_NAME).filter(
                users.c.CHAT_ID == self.chat_id)
            if not user_exists.first():  # need this in Stickers & Locations also
                try:
                    sql_session.execute(users.insert(
                        [self.chat_id, self.bot_type, self.user, '', False, self.user_id]))
                except sqlalchemy.exc.IntegrityError as e:  # unique constraint violated
                    print(e)
            else:
                insert("""UPDATE USERS SET USER_ID = ? WHERE CHAT_ID LIKE ?""", (self.user_id, self.chat_id))
        try:
            awaiting_incoming_quote = sql_session.query(users.c.AWAITING_QUOTE).filter(
                and_(
                    or_(
                        users.c.AWAITING_QUOTE == 1,
                        users.c.AWAITING_QUOTE == 'True'
                    ),
                    users.c.CHAT_ID == self.user_id
                )
            ).one()
        except NoResultFound as e:
            print(e)
            return
        except MultipleResultsFound as e:
            print(e)
            return

        in_msg_body_lower = ''

        if awaiting_incoming_quote and dia.type == 'private':
            i = 0
            try:
                rowcount = sql_session.execute(quote.insert(
                        [None,
                         None,
                         func.now(),
                         self.user,
                         self.item.lower(),
                         dia.InMsg.file_id]).prefix_with("OR IGNORE")).rowcount
            except sqlalchemy.exc.IntegrityError as e:  # unique constraint violated
                print(e)
            i += rowcount
            dia.check_incoming_quote(i, in_msg_body_lower)

    def print_in_msg(self, dia):
        print(str(datetime.now()), '{0} from {1} (Chat ID = {2}, User ID = {3}).'.format(
            self.item, self.user, str(self.chat_id), str(self.user_id)))

    def print_out_msg(self):
        if hasattr(self, 'type') and self.type == 'pseudo':
            return

        logged_answer = self.answer
        if logged_answer is None:
            logged_answer = ''
        if self.my_url and self.my_url != '':
            logged_answer = logged_answer + ' ' + self.my_url
        if logged_answer == '' and hasattr(self, 'item'):
            logged_answer = self.item

        print(str(datetime.now()), 'Responding {0} (Chat ID = {1}, User ID = {2}). Answer from Bot = {3}'.format(
                                        self.user, self.chat_id, self.user_id, logged_answer))


class PhotoDeco(object):
    def __init__(self, decoratee, file_id = None):
        self._decoratee = NonTextDeco(decoratee)
        self._decoratee.item = 'Photo'
        self.item = 'Photo'
        if file_id is not None:
            self.file_id = file_id

    def __getattr__(self, name):
        return getattr(self._decoratee, name)


class VideoDeco(object):
    def __init__(self, decoratee, file_id = None):
        self._decoratee = NonTextDeco(decoratee)
        self._decoratee.item = 'Video'
        self.item = 'Video'
        if file_id is not None:
            self.file_id = file_id

    def __getattr__(self, name):
        return getattr(self._decoratee, name)


class VideoNoteDeco(object):
    def __init__(self, decoratee, file_id = None):
        self._decoratee = NonTextDeco(decoratee)
        self._decoratee.item = 'VideoNote'
        self.item = 'VideoNote'
        if file_id is not None:
            self.file_id = file_id

    def __getattr__(self, name):
        return getattr(self._decoratee, name)


class VoiceDeco(object):
    def __init__(self, decoratee, file_id = None):
        self._decoratee = NonTextDeco(decoratee)
        self.item = 'Voice'
        self._decoratee.item = 'Voice'
        if file_id is not None:
            self.file_id = file_id

    def __getattr__(self, name):
        return getattr(self._decoratee, name)


class AudioDeco(object):
    def __init__(self, decoratee, file_id = None):
        self._decoratee = NonTextDeco(decoratee)
        self._decoratee.item = 'Audio'
        self.item = 'Audio'
        if file_id is not None:
            self.file_id = file_id

    def __getattr__(self, name):
        return getattr(self._decoratee, name)


class LocationDeco(object):
    def __init__(self, decoratee):
        self._decoratee = NonTextDeco(decoratee)
        self._decoratee.item = 'Location'
        self.item = 'Location'

    def __getattr__(self, name):
        return getattr(self._decoratee, name)


class StickerDeco(object):
    def __init__(self, decoratee):
        self._decoratee = NonTextDeco(decoratee)
        self._decoratee.item = 'Sticker'
        self.item = 'Sticker'

    def __getattr__(self, name):
        return getattr(self._decoratee, name)
