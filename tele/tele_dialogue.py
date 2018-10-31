import re
from time import sleep
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from tele.tele_deco import TeleDeco
from core.constants import sql_session, quote
from core.dialogue import Dialogue
from core.deco import Deco
from sqlalchemy.sql.expression import func, and_, or_
from core.constants import quote_not_found_text


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
        from tele.telegram_quote_bot import bot
        import telebot
        try:
            bot.send_chat_action(self.chat_id, action)
        except telebot.apihelper.ApiException as e:
            print(e)

    def set_outgoing_quote(self):
        try:
            res = sql_session.query(
                                    quote.c.AUTHOR,
                                    quote.c.QUOTE,
                                    quote.c.TYPE,
                                    quote.c.FILE_ID
            ).filter(
                or_(
                    and_(
                        quote.c.QUOTE.isnot(None),
                        quote.c.AUTHOR.isnot(None)
                    ),
                    quote.c.FILE_ID.isnot(None)
                )
            ).order_by(
                func.random()
            ).limit(1).one()
            author = res[0]
            quote_text = res[1]
            self.OutMsg.item = res[2]
            self.OutMsg.file_id = res[3]
        except MultipleResultsFound as e:
            print(e)
            return
        except NoResultFound:
            author = 'system'
            quote_text = quote_not_found_text
            self.OutMsg.item = 'text'
            self.OutMsg.file_id = None

        if author is not None:
            author = author.title()

        if quote_text is not None:
            if len(re.findall(r'\W', quote_text[-1])) == 0:
                quote_text = quote_text[0].title() + quote_text[1:] + '.'
            else:
                quote_text = quote_text[0].title() + quote_text[1:]

        if self.OutMsg.item == 'text':
            self.OutMsg.parse_type = 'markdown'
            self.OutMsg.answer = quote_text + '\n\n_' + author + '_'

    @staticmethod
    def create_dlg(chat_id, user):
        return TeleDialogue(chat_id, chat_id, '', user, 'private')

    def is_valid_kwargs(self):
        return len(self.OutMsg.tele_kwargs) > 1
