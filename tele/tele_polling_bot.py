import time
import requests
import telebot
from telebot import util, apihelper
from tele.tele_dialogue import TeleDialogue
from core.non_text_deco import VideoDeco, AudioDeco, PhotoDeco, VoiceDeco
from core.text_deco import TextDeco
from core.constants import sql_engine, jobs


class TelePollingBot(telebot.TeleBot):
    def _TeleBot__threaded_polling(self, none_stop = False, interval = 0, timeout = 3):
        from tele.telegram_quote_bot import logger, bot
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

                    if job.repeat == 1 or job.repeat is True or job.repeat == 'true':
                        sql = "UPDATE JOBS SET LAST_SENT_ON_DATE = DATE('NOW') WHERE ROWID = '{}'".format(job.row_id)
                        sql_engine.execute(sql)
                    else:
                        sql = "DELETE FROM JOBS WHERE ROWID = '{}'".format(job.row_id)
                        sql_engine.execute(sql)

                    job.OutMsg.print_out_msg()
                except telebot.apihelper.ApiException as e:
                    print(e)
            logger.debug("Jobs done.")

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
