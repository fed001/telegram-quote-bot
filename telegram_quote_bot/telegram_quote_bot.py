import re
import time
import requests
import logging
from sqlalchemy import exc
from telebot import TeleBot, util, apihelper
from telegram_quote_bot.config import sql_session, users, tele_group_chat_id, help_text, tele_job_user_id
from telegram_quote_bot.db_query import insert, query
from telegram_quote_bot.job_handler import JobHandler
from telegram_quote_bot.message import OutgoingMessage
from telegram_quote_bot.user_handler import UserHandler
from telegram_quote_bot.utils import get_result_message, is_not_empty, user_is_fiehe_subscriber, user_is_quote_subscriber, \
    get_subscribed_time, get_quote_list, update_database, stop_awaiting_quote
from telegram_quote_bot.spotify_handler import SpotifyHandler
logger = logging.getLogger('TeleBot')


class TelegramQuoteBot(TeleBot):
    def __init__(self, token, spotify_flag, threaded=True, skip_pending=False, num_threads=2):
        super().__init__(token, threaded, skip_pending, num_threads)
        self.spotify_flag = spotify_flag
        if self.spotify_flag:
            sp = SpotifyHandler()
            sp.update_playlist_cache()
        self.quote_list = get_quote_list()
        self.user_handler = UserHandler()
        self.job_handler = JobHandler()

    def _TeleBot__non_threaded_polling(self, none_stop=False, interval=0, timeout=3):
        logger.info('Started polling.')
        self._TeleBot__stop_polling.clear()
        error_interval = 0.25

        while not self._TeleBot__stop_polling.wait(interval):
            logger.debug("Started polling loop iteration")
            self.process_jobs()
            try:
                self._TeleBot__retrieve_updates(timeout)
                error_interval = 0.25
            except apihelper.ApiException as e:
                logger.error(e)
                if not none_stop:
                    self._TeleBot__stop_polling.set()
                    logger.info("Exception occurred. Stopping.")
                else:
                    logger.info("Waiting for {0} seconds until retry".format(error_interval))
                    time.sleep(error_interval)
                    error_interval *= 2
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received.")
                self._TeleBot__stop_polling.set()
                break

        logger.info('Stopped polling.')

    def _TeleBot__threaded_polling(self, none_stop=False, interval=0, timeout=3):
        logger.info('Started polling.')
        self._TeleBot__stop_polling.clear()
        error_interval = .25

        polling_thread = util.WorkerThread(name="PollingThread")
        or_event = util.OrEvent(polling_thread.done_event,
                                polling_thread.exception_event,
                                self.worker_pool.exception_event)

        while not self._TeleBot__stop_polling.wait(interval):
            logger.debug("Started polling loop iteration")
            self.process_jobs()

            or_event.clear()
            try:
                polling_thread.put(self._TeleBot__retrieve_updates, timeout)
                or_event.wait()  # wait for polling thread finish, polling thread error or thread pool error
                polling_thread.raise_exceptions()
                self.worker_pool.raise_exceptions()
                error_interval = .25
            except (apihelper.ApiException, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                logger.error(e)
                if not none_stop:
                    self._TeleBot__stop_polling.set()
                    logger.error("Exception occurred. Stopping.")
                else:
                    polling_thread.clear_exceptions()
                    self.worker_pool.clear_exceptions()
                    logger.error("Waiting for {0} seconds until retry".format(error_interval))
                    time.sleep(error_interval)
                    error_interval *= 2
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received.")
                self._TeleBot__stop_polling.set()
                polling_thread.stop()
                break

        logger.info('Stopped polling.')

    def process_jobs(self):
        jobs = self.job_handler.get_due_jobs()
        for job in jobs:
            parse_mode = 'markdown' if job['msg_markup'] else None
            out_msg = OutgoingMessage(job['chat_id'], job['user_name'], parse_mode=parse_mode)
            if job['msg_text'] == 'quote':
                out_msg.map_random_quote_to_message(self.quote_list)
            else:
                out_msg.msg_body = job['msg_text']
            out_msg.map_kwargs()
            self.start_job(out_msg)
            update_database(job['repeat'], job['interval'], job['row_id'], self.job_handler)
        logger.debug("Jobs done.")

    def start_job(self, out_msg):
        try:
            logger.info("Starting Job for user {}...".format(out_msg.user))
            if 'photo' in out_msg.tele_kwargs.keys():
                self.send_chat_action(out_msg.chat_id, 'upload_photo')
                self.send_photo(**out_msg.tele_kwargs)
            elif 'audio' in out_msg.tele_kwargs.keys():
                self.send_chat_action(out_msg.chat_id, 'record_audio')
                self.send_audio(**out_msg.tele_kwargs)
            elif 'voice' in out_msg.tele_kwargs.keys():
                self.send_chat_action(out_msg.chat_id, 'record_audio')
                self.send_voice(**out_msg.tele_kwargs)
            elif 'data' in out_msg.tele_kwargs.keys():
                if out_msg.media_type == 'video_note':
                    self.send_chat_action(out_msg.chat_id, 'record_video_note')
                    self.send_video_note(**out_msg.tele_kwargs)
                else:
                    self.send_chat_action(out_msg.chat_id, 'record_video')
                    self.send_video(**out_msg.tele_kwargs)
            else:
                self.send_chat_action(out_msg.chat_id, 'typing')
                self.send_message(**out_msg.tele_kwargs)

            logger.info(out_msg.create_msg_log())
        except apihelper.ApiException as e:
            logger.error(e)

    def process_user_media_quote(self, in_msg):
        user = self.user_handler.get_user(in_msg.user_id)
        if user is None:
            return

        if user['awaiting_quote'] is True and in_msg.type == 'private':
            rows_inserted = 0
            rowcount = insert("""insert into "quote" (added_by, type, file_id) values (%s, %s, %s)""",
                              (user['user_id'], in_msg.media_type.lower(), in_msg.file_id))
            rows_inserted += rowcount
            msg_body = get_result_message(rows_inserted)
        elif user['awaiting_quote'] is True and in_msg.type != 'private':
            msg_body = "Open a private Chat with me and add your Quote(s) there.".format(in_msg.user)
        else:
            return

        out_msg = OutgoingMessage(in_msg.chat_id, in_msg.user, user_id=in_msg.user_id, msg_body=msg_body)
        out_msg.map_kwargs()
        self.send_and_log(out_msg)

    def process_new_job(self, in_msg):
        in_msg_body_lower = in_msg.msg_body.lower().replace('/', '')
        in_msg_body_lower = re.sub(r"@.+", "", in_msg_body_lower)

        try:
            insert("""insert into "jobs" (chat_id, user_name, msg_text, msg_markup, repeat)
                    values (%s, %s, %s, %s, %s)""",
                   (tele_group_chat_id, tele_job_user_id, in_msg_body_lower, False, False))
            self.job_handler.update()
            sql_session.execute(users.update().values(comment='').where(users.c.chat_id == in_msg.user_id))
            self.user_handler.update_dict()
        except exc.IntegrityError as e:
            logger.error(e)

    def process_user_text_quote(self, in_msg):
        inserted_rows = 0
        submitted_quotes = in_msg.msg_body.split('\n')
        for submitted_quote in submitted_quotes:
            data_piece = submitted_quote.split(' - ')
            if len(data_piece) == 2:
                author = data_piece[0]
                quote = data_piece[1]
                if is_not_empty(author) and is_not_empty(quote):
                    rowcount = insert("""INSERT INTO "quote" (author, quote, added_by, type)
                        VALUES (%s, %s, %s, 'text') ON CONFLICT DO NOTHING;""", (author, quote, in_msg.user_id))
                    inserted_rows += rowcount
            else:
                break
        out_msg = OutgoingMessage(in_msg.chat_id, in_msg.user, user_id=in_msg.user_id,
                                  msg_body=get_result_message(inserted_rows))
        out_msg.map_kwargs()
        self.send_and_log(out_msg)

    def process_new_subscription_time(self, in_msg):
        if not user_is_quote_subscriber(in_msg.user_id):
            msg_body = "{} is not subscribed.".format(in_msg.user)
        elif not (int(in_msg.msg_body[0:2]) < 24 and int(in_msg.msg_body[3:]) < 60):
            msg_body = """Error! Invalid time format?"""
        else:
            target_time = in_msg.msg_body + ':00'
            rowcount = insert("""UPDATE "jobs" SET to_send_at_time = time %s
                                 WHERE chat_id = %s AND interval = 'daily';""", (target_time, in_msg.user_id))
            self.job_handler.update()

            if rowcount > 0:
                msg_body = """Success! Time for your daily quote updated to {} in Database.""".format(
                    in_msg.msg_body)
                stop_awaiting_quote(in_msg.user_id, self.user_handler)
            else:
                msg_body = """Error! Invalid time format?"""
        out_msg = OutgoingMessage(in_msg.chat_id, in_msg.user, user_id=in_msg.user_id, msg_body=msg_body)
        out_msg.map_kwargs()
        self.send_and_log(out_msg)

    def addquote_command(self, in_msg):
        if in_msg.type == 'private':
            msg_body = """OK, you can either send me an Audio File, Video File, Voice Note, Picture or type a list of Text Quotes in the following format:

Author1 - Text
Author2 - Another Text
                """
            insert("""UPDATE "users" SET awaiting_quote = 'True' WHERE user_id = %s;""", (in_msg.user_id,))
            self.user_handler.update_dict()
        else:
            msg_body = "{}, open a private Chat with me and add quotes there.".format(in_msg.user)

        out_msg = OutgoingMessage(in_msg.chat_id, in_msg.user, user_id=in_msg.user_id, msg_body=msg_body)
        out_msg.map_kwargs()
        self.send_and_log(out_msg)

    def abort_command(self, in_msg):
        stop_awaiting_quote(in_msg.user_id, self.user_handler)
        out_msg = OutgoingMessage(in_msg.chat_id, in_msg.user, user_id=in_msg.user_id, msg_body="""Operation aborted.""")
        out_msg.map_kwargs()
        self.send_and_log(out_msg)

    def subscribe_fiehe_command(self, in_msg):
        if user_is_fiehe_subscriber(in_msg.user_id):
            msg_body = """{}, you're already subscribed for new Fiehe playlists.""".format(in_msg.user)
        else:
            stop_awaiting_quote(in_msg.user_id, self.user_handler)
            if in_msg.type == 'private':
                msg_body = """Sending you new Fiehe playlists from now."""
                insert("""INSERT INTO "jobs" (chat_id, user_name, msg_markup, repeat, interval)
                        VALUES (%s, %s, 'true', 'true', 'on fiehe pl');""", (in_msg.user_id, in_msg.user,))
                self.job_handler.update()
            else:
                msg_body = "{}, open a private Chat with me and subscribe there.".format(in_msg.user)

        out_msg = OutgoingMessage(in_msg.chat_id, in_msg.user, user_id=in_msg.user_id, msg_body=msg_body)
        out_msg.map_kwargs()
        self.send_and_log(out_msg)

    def unsubscribe_fiehe_command(self, in_msg):
        stop_awaiting_quote(in_msg.user_id, self.user_handler)
        if user_is_fiehe_subscriber(in_msg.user_id):
            msg_body = "Removing user {} from Fiehe Subscribers...".format(in_msg.user)
            insert("""DELETE FROM "jobs" WHERE chat_id = %s AND interval = 'on fiehe pl';""", (in_msg.user_id,))
            self.job_handler.update()
        else:
            msg_body = "User {} is not subscribed.".format(in_msg.user)

        out_msg = OutgoingMessage(in_msg.chat_id, in_msg.user, user_id=in_msg.user_id, msg_body=msg_body)
        out_msg.map_kwargs()
        self.send_and_log(out_msg)

    def unsubscribe_quote_command(self, in_msg):
        stop_awaiting_quote(in_msg.user_id, self.user_handler)
        if user_is_quote_subscriber(in_msg.user_id):
            msg_body = "Removing user {} from Subscribers...".format(in_msg.user)
            insert("""DELETE FROM "jobs" WHERE chat_id = %s AND interval = 'daily';""", (str(in_msg.user_id),))
            self.job_handler.update()
        else:
            msg_body = "{} is not subscribed.".format(in_msg.user)
        out_msg = OutgoingMessage(in_msg.chat_id, in_msg.user, user_id=in_msg.user_id, msg_body=msg_body)
        out_msg.map_kwargs()
        self.send_and_log(out_msg)

    def spotify_command(self, in_msg):
        stop_awaiting_quote(in_msg.user_id, self.user_handler)
        if self.spotify_flag:
            spotify_handler = SpotifyHandler()
            spotify_handler.update_playlist_cache()
            self.job_handler.update()
            msg_body = "Success! SpotifyHandler dict updated."
        else:
            msg_body = "Spotify not configured."
        out_msg = OutgoingMessage(in_msg.chat_id, in_msg.user, user_id=in_msg.user_id, msg_body=msg_body)
        out_msg.map_kwargs()
        self.send_and_log(out_msg)

    def addjob_command(self, in_msg):
        insert("""UPDATE "users" SET awaiting_quote = 'False', comment = 'job' WHERE user_id = %s""",
               (str(in_msg.user_id),))
        self.user_handler.update_dict()
        out_msg = OutgoingMessage(in_msg.chat_id, in_msg.user, user_id=in_msg.user_id, msg_body="""OK, you can type your Text.""")
        out_msg.map_kwargs()
        self.send_and_log(out_msg)

    def subscribe_quote_command(self, in_msg):
        if user_is_quote_subscriber(in_msg.user_id):
            subscribed_time = get_subscribed_time(in_msg.user_id)
            msg_body = """You're subscribed for daily quotes at {} CET.
To change the time, you can send me the desired time in CET in the following format:

hh:mm""".format(subscribed_time[:-3]) if in_msg.type == 'private' else """{}, you're subscribed for daily quotes at {} CET.
To change the time, open a private Chat with me and subscribe there.""".format(in_msg.user, subscribed_time[:-3])
        else:
            stop_awaiting_quote(in_msg.user_id, self.user_handler)
            if in_msg.type == 'private':
                repeat = 'true'
                interval = 'daily'
                msg_body = """Sending you daily quotes at 09:00 CET. To change the time, you can send me the desired time in CET in the following format:

hh:mm"""
                insert("""INSERT INTO "jobs" (chat_id, user_name, msg_text, msg_markup, repeat, interval)
                        VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;""",
                       (in_msg.user_id, in_msg.user, 'quote', 'true', repeat, interval))
                self.job_handler.update()
            else:
                msg_body = "{}, open a private Chat with me and subscribe there.".format(in_msg.user)

        out_msg = OutgoingMessage(in_msg.chat_id, in_msg.user, user_id=in_msg.user_id, msg_body=msg_body)
        out_msg.map_kwargs()
        self.send_and_log(out_msg)

    def help_command(self, in_msg):
        out_msg = OutgoingMessage(in_msg.chat_id, in_msg.user, user_id=in_msg.user_id, msg_body=help_text)
        out_msg.map_kwargs()
        self.send_and_log(out_msg)
        stop_awaiting_quote(in_msg.user_id, self.user_handler)

    def quote_command(self, in_msg):
        stop_awaiting_quote(in_msg.user_id, self.user_handler)
        out_msg = OutgoingMessage(in_msg.chat_id, in_msg.user, user_id=in_msg.user_id)
        out_msg.map_random_quote_to_message(self.quote_list)
        out_msg.map_kwargs()

        if 'photo' in out_msg.tele_kwargs.keys():
            self.try_send_chat_action(out_msg.chat_id, 'upload_photo')
            self.send_photo(**out_msg.tele_kwargs)
        elif 'audio' in out_msg.tele_kwargs.keys():
            self.try_send_chat_action(out_msg.chat_id, 'upload_audio')
            self.send_audio(**out_msg.tele_kwargs)
        elif 'voice' in out_msg.tele_kwargs.keys():
            self.try_send_chat_action(out_msg.chat_id, 'upload_audio')
            self.send_voice(**out_msg.tele_kwargs)
        elif 'data' in out_msg.tele_kwargs.keys() and out_msg.media_type == 'video':
            self.try_send_chat_action(out_msg.chat_id, 'upload_video')
            self.send_video(**out_msg.tele_kwargs)
        elif 'data' in out_msg.tele_kwargs.keys() and out_msg.media_type == 'video_note':
            self.try_send_chat_action(out_msg.chat_id, 'upload_video_note')
            self.send_video_note(**out_msg.tele_kwargs)
        else:
            self.send_message(**out_msg.tele_kwargs)

        logger.info(out_msg.create_msg_log())

    def try_send_chat_action(self, chat_id, action):
        try:
            self.send_chat_action(chat_id, action)
        except apihelper.ApiException as e:
            logger.error(e)

    def send_voice_file(self, chat_id, path):
        with open(path, 'r') as voice_file:
            self.try_send_chat_action(chat_id, 'record_audio')
            self.send_voice(chat_id, voice_file)

    def send_photo_file(self, chat_id, path):
        with open(path, 'r') as photo_file:
            self.try_send_chat_action(chat_id, 'upload_photo')
            self.send_photo(chat_id, photo_file)

    def send_rdm_location(self, in_msg):
        rdm_location = query("""SELECT longitude, latitude, title, address FROM "location" ORDER BY RANDOM()
                             LIMIT 1;""")
        self.send_venue(in_msg.chat_id, longitude=rdm_location[0][0], latitude=rdm_location[0][1],
                        title=rdm_location[0][2], address=rdm_location[0][3])
        stop_awaiting_quote(in_msg.user_id, self.user_handler)
        out_msg = OutgoingMessage(in_msg.chat_id, in_msg.user, user_id=in_msg.user_id, media_type='location')
        logger.info(out_msg.create_msg_log())

    def send_wolf_sticker(self, in_msg):
        self.send_sticker(in_msg.chat_id, 'CAADAgADCwEAAvR7GQABuArOzKHFjusC')
        stop_awaiting_quote(in_msg.user_id, self.user_handler)
        out_msg = OutgoingMessage(in_msg.chat_id, in_msg.user, user_id=in_msg.user_id, media_type='sticker')
        logger.info(out_msg.create_msg_log())

    def send_and_log(self, out_msg):
        self.send_message(**out_msg.tele_kwargs)
        logger.info(out_msg.create_msg_log())
