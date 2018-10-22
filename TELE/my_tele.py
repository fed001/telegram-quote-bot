import time
import requests
import telebot
from telebot import util, apihelper
from core.dbQuery import insert, query
from TELE.tele_dialogue import TeleDialogue
from core.non_text_deco import VideoDeco, AudioDeco, PhotoDeco, VoiceDeco
from core.text_deco import TextDeco


class MyTele(telebot.TeleBot):
    def _TeleBot__threaded_polling(self, none_stop = False, interval = 0, timeout = 3):
        from TELE.wolfg import logger, bot
        logger.info('Started polling.')
        self._TeleBot__stop_polling.clear()
        error_interval = .25

        polling_thread = util.WorkerThread(name = "PollingThread")
        or_event = util.OrEvent(polling_thread.done_event,
                                polling_thread.exception_event,
                                self.worker_pool.exception_event)

        while not self._TeleBot__stop_polling.wait(interval):
            db_dial = TeleDialogue('', '', 'update', '', 'pseudo')
            db_dial.InMsg = TextDeco(db_dial.InMsg)
            db_dial.InMsg.item = 'Text'
            db_dial.InMsg.process_input(db_dial)
            db_dial.OutMsg = TextDeco(db_dial.OutMsg)
            db_dial.process_output()

            for job in db_dial.job_dial:
                try:
                    logger.info("Starting Job for user {}...".format(job.user))
                    if 'photo' in job.OutMsg.tele_kwargs.keys():
                        bot.send_chat_action(job.chat_id, 'upload_photo')
                        bot.send_photo(**job.OutMsg.tele_kwargs)
                        job.OutMsg = PhotoDeco(job.OutMsg)
                    elif 'audio' in job.OutMsg.tele_kwargs.keys():
                        bot.send_chat_action(job.chat_id, 'record_audio')
                        bot.send_audio(**job.OutMsg.tele_kwargs)
                        job.OutMsg = AudioDeco(job.OutMsg)
                    elif 'voice' in job.OutMsg.tele_kwargs.keys():
                        bot.send_chat_action(job.chat_id, 'record_audio')
                        bot.send_voice(**job.OutMsg.tele_kwargs)
                        job.OutMsg = VoiceDeco(job.OutMsg)
                    elif 'data' in job.OutMsg.tele_kwargs.keys():
                        if job.OutMsg.item == 'videonote':
                            bot.send_chat_action(job.chat_id, 'record_video_note')
                            bot.send_video_note(**job.OutMsg.tele_kwargs)
                        else:
                            bot.send_chat_action(job.chat_id, 'record_video')
                            bot.send_video(**job.OutMsg.tele_kwargs)
                        job.OutMsg = VideoDeco(job.OutMsg)
                    elif job.is_valid_kwargs():
                        bot.send_chat_action(job.chat_id, 'typing')
                        bot.send_message(**job.OutMsg.tele_kwargs)
                        job.OutMsg = TextDeco(job.OutMsg)

                    if job.repeat == 'true':
                        insert("""UPDATE JOBS SET LAST_SENT_ON_DATE = DATE('NOW') WHERE ROWID = ?""", (job.row_id,))
                    else:
                        insert("""DELETE FROM JOBS WHERE ROWID = ?""", (job.row_id,))
                    job.OutMsg.print_out_msg()
                except telebot.apihelper.ApiException as e:
                    print(e)
            logger.debug("Jobs done.")
            game_users = query("""SELECT USER_NAME, CHAT_ID, SCORE, MSG_ID, INLINE_MSG_ID, CHAT_INSTANCE FROM GAMES
                                WHERE TO_UPDATE = 1 AND (MSG_ID NOT LIKE '' OR INLINE_MSG_ID NOT LIKE '');""")
            for gu in game_users:
                user_id = query("""SELECT USER_ID FROM USERS WHERE USER_NAME LIKE ?""", (gu[0], ))
                if len(user_id) > 0:
                    user_id = user_id[0][0]
                msg_id = gu[3]
                chat_id = gu[1]
                inline_msg_id = gu[4]
                chat_instance = gu[5]
                if inline_msg_id != '':
                    chat_id = None
                score = int(gu[2])
                try:
                    ret = None
                    # chat_id => disable_edit_message
                    # message_id => chat_id
                    # inline_message_id => message_id
                    # edit_message => inline_message_id
                    ret = bot.set_game_score(force = False,
                                             user_id = user_id,
                                             message_id = chat_id,
                                             score = score,
                                             chat_id = False,
                                             inline_message_id = msg_id,
                                             edit_message = inline_msg_id)
                except telebot.apihelper.ApiException as e:
                    logger.info("Telegram API exception!", exc_info = e)
                if ret:
                    logger.info("Updated game score for {}.".format(gu[0]))
                insert("""UPDATE GAMES SET TO_UPDATE = 0 WHERE CHAT_INSTANCE LIKE ?""", (chat_instance, ))

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
                    logger.info("Exception occurred. Stopping.")
                else:
                    polling_thread.clear_exceptions()
                    self.worker_pool.clear_exceptions()
                    logger.info("Waiting for {0} seconds until retry".format(error_interval))
                    time.sleep(error_interval)
                    error_interval *= 2
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received.")
                self._TeleBot__stop_polling.set()
                polling_thread.stop()
                break

        logger.info('Stopped polling.')
