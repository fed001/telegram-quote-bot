from telegram_quote_bot.utils import get_user_dict


class UserHandler:
    def __init__(self):
        self.user_dict = get_user_dict()

    def get_user(self, user_id):
        ret_val = self.user_dict[str(user_id)] if str(user_id) in self.user_dict else None
        return ret_val

    def update_dict(self):
        self.user_dict = get_user_dict()

    def is_new_job(self, message):
        if self.get_user(message.from_user.id) is None:
            return False

        user = self.get_user(message.from_user.id)
        return user['comment'] == 'job' and message.chat.type == 'private'

    def is_new_quote(self, message):
        if self.get_user(message.from_user.id) is None:
            return False

        user = self.get_user(message.from_user.id)
        return user['awaiting_quote'] is True and message.chat.type == 'private'
