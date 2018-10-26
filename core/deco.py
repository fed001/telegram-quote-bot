class Deco(object):
    def __init__(self, dia, msg_body, file_id = None):
        self.chat_id = dia.chat_id
        self.user_id = dia.user_id
        self.bot_type = dia.bot_type
        self.in_msg_body = msg_body
        self.user = dia.user
        self.type = None
        self.markup = None
        self.my_url = ""
        self.markup_type = None
        self.parse_type = ''
        self.answer = ""
        self.job_dial = []
        self.msg = None
        self.file_id = file_id
