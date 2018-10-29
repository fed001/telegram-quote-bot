from core.deco import Deco


class TeleDeco(Deco):
    def __init__(self, dia):
        super(TeleDeco, self).__init__(dia, '')
        self.tele_kwargs = {}
        self.disable_web_page_preview = 'False'
        self.answer = ""
        self.item = None

    def prepare_kwargs(self):
        self.tele_kwargs['chat_id'] = self.chat_id
        if self.answer and self.markup \
                and self.markup.keyboard and len(self.markup.keyboard) == 1:
            self.tele_kwargs['text'] = self.answer
            self.tele_kwargs['reply_markup'] = self.markup
        elif self.my_url:
            self.tele_kwargs['text'] = self.my_url
        elif self.answer and self.parse_type == 'markdown':  # for Quotes
            self.tele_kwargs['text'] = self.answer
            self.tele_kwargs['parse_mode'] = self.parse_type
        elif self.answer and self.disable_web_page_preview == 'True':  # for Help Message
            self.tele_kwargs['text'] = self.answer
            self.tele_kwargs['disable_web_page_preview'] = True
        elif self.file_id:
            if self.item in ['photo', 'audio', 'voice']:
                self.tele_kwargs[self.item] = self.file_id
            elif self.item in ['video', 'videonote']:
                self.tele_kwargs['data'] = self.file_id
        elif self.answer:
            self.tele_kwargs['text'] = self.answer
