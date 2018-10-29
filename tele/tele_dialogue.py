from time import sleep

from tele.tele_deco import TeleDeco
from core.constants import sql_session, quote
from core.dialogue import Dialogue
from core.deco import Deco
from sqlalchemy.sql.expression import func, and_, or_


class TeleDialogue(Dialogue):
    def __init__(self, chat_id, user_id, in_msg_body, user, dia_type, file_id = None):
        super(TeleDialogue, self).__init__(chat_id, 'telegram', user)
        self.user_id = user_id
        self.type = dia_type
        self.markup = None
        self.disable_web_page_preview = 'False'
        self.my_url = ""
        self.markup_type = None
        self.parse_type = ''
        self.answer = ""
        self.job_dial = []
        self.msg = None
        self.file_id = None
        self.InMsg = Deco(self, in_msg_body, file_id)
        self.OutMsg = TeleDeco(self)

    def send_typing_status(self):
        self.tele_out_action('typing')

    def tele_out_action(self, action):
        """
        Telegram: Send chat action typing.
        Kik: Adjust dlg.msg.
        :param action: Chat action type.
        :return:
        """
        sleep(0.1)
        from tele.wolfg import bot
        import telebot
        try:
            bot.send_chat_action(self.chat_id, action)
        except telebot.apihelper.ApiException as e:
            print(e)

    def format_quote(self, author, quote):
        self.OutMsg.parse_type = 'markdown'
        self.OutMsg.answer = quote + '\n\n_' + author + '_'

    @staticmethod
    def create_dlg(chat_id, user):
        return TeleDialogue(chat_id, chat_id, '', user, 'private')

    @staticmethod
    def perform_quote_select():
        this = sql_session.query(
                                quote.c.QUOTE,
                                quote.c.AUTHOR,
                                quote.c.TYPE,
                                quote.c.FILE_ID
        ).filter(
            or_(and_(quote.c.QUOTE.isnot(None), quote.c.AUTHOR.isnot(None)),
                quote.c.FILE_ID.isnot(None))
        ).order_by(
            func.random()
        ).limit(1)
        return this.first()

    def is_valid_kwargs(self):
        return len(self.OutMsg.tele_kwargs) > 1
