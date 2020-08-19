from logging import getLogger
from telegram_quote_bot.utils import get_random_quote_from_dict, get_formatted_quote, tele_get_user

logger = getLogger('TeleBot')


class IncomingMessage:
    def __init__(self, chat_id, chat_type, user_id, first_name, last_name, username, msg_body, media_type=None,
                 file_id=None):
        self.chat_id = str(chat_id)
        self.user_id = str(user_id)
        self.msg_body = msg_body
        self.user = tele_get_user(first_name, last_name, username)
        self.type = chat_type
        self.file_id = file_id
        self.media_type = media_type
        logger.info(self.create_msg_log())

    def create_msg_log(self):
        outgoing_msg = self.media_type if self.msg_body is None or self.msg_body == '' else self.msg_body
        return 'Received message from {0} (Chat ID = {1}, User ID = {2}). Message from User = {3}'.format(
                    self.user, str(self.chat_id), str(self.user_id), outgoing_msg.encode('utf-8'))


class OutgoingMessage:
    def __init__(self, chat_id, user, user_id=None, parse_mode=None, msg_body=None, media_type=None, file_id=None):
        self.tele_kwargs = {}
        self.msg_body = msg_body
        self.file_id = file_id
        self.media_type = media_type
        self.chat_id = chat_id
        self.user_id = user_id
        self.user = user
        self.parse_mode = parse_mode

    def map_kwargs(self):
        self.tele_kwargs['chat_id'] = self.chat_id
        if self.msg_body:
            self.tele_kwargs['text'] = self.msg_body
            self.tele_kwargs['parse_mode'] = 'markdown'
        elif self.file_id:
            if self.media_type in ['photo', 'audio', 'voice']:
                self.tele_kwargs[self.media_type] = self.file_id
            elif self.media_type in ['video', 'video_note']:
                self.tele_kwargs['data'] = self.file_id

    def create_msg_log(self):
        outgoing_msg = self.media_type if self.msg_body is None or self.msg_body == '' else self.msg_body

        try:
            return 'Sending message to {0} (Chat ID = {1}, User ID = {2}). Message from Bot = {3}'.format(
                                        self.user, self.chat_id, self.user_id, outgoing_msg.encode('utf-8'))
        except UnicodeDecodeError:
            return 'Sending message to {0} (Chat ID = {1}, User ID = {2}). Message from Bot = {3}'.format(
                    self.user, self.chat_id, self.user_id, outgoing_msg)

    def map_random_quote_to_message(self, quote_list):
        try:
            raw_quote, author, media_type, file_id = get_random_quote_from_dict(quote_list)
            if raw_quote is not None:
                self.msg_body = get_formatted_quote(author, raw_quote)
            elif file_id is not None:
                self.file_id = file_id
            else:
                self.msg_body = "No quote found."
            self.media_type = media_type
        except Exception as e:
            logger.error(e)

