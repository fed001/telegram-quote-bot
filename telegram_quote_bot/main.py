"""
telegram_quote_bot
"""
import logging
from systemd.journal import JournaldLogHandler
from telegram_quote_bot.config import token, log_level, log_level_sqlalchemy, threaded, threads, spotify_flag
from telegram_quote_bot.message import IncomingMessage
from telegram_quote_bot.utils import is_new_subscription_time
from telegram_quote_bot.telegram_quote_bot import TelegramQuoteBot

logger = logging.getLogger('TeleBot')

if logger.hasHandlers():
    logger.handlers.clear()

logger.setLevel(log_level)
logger.addHandler(JournaldLogHandler())
logging.getLogger('sqlalchemy.engine').setLevel(log_level_sqlalchemy)

bot = TelegramQuoteBot(token=token, spotify_flag=spotify_flag, threaded=threaded, num_threads=threads)


@bot.message_handler(content_types=['text'], commands=['help', 'start'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text)
    bot.help_command(in_msg)


@bot.message_handler(content_types=['text'], commands=['subscribe_quote'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text)
    bot.subscribe_quote_command(in_msg)


@bot.message_handler(content_types=['text'], commands=['addjob'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text)
    bot.addjob_command(in_msg)


@bot.message_handler(content_types=['text'], commands=['spotify'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text)
    bot.spotify_command(in_msg)


@bot.message_handler(content_types=['text'], commands=['unsubscribe_quote'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text)
    bot.unsubscribe_quote_command(in_msg)


@bot.message_handler(content_types=['text'], commands=['unsubscribe_fiehe'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text)
    bot.unsubscribe_fiehe_command(in_msg)


@bot.message_handler(content_types=['text'], commands=['subscribe_fiehe'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text)
    bot.subscribe_fiehe_command(in_msg)


@bot.message_handler(content_types=['text'], commands=['addquote'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text)
    bot.addquote_command(in_msg)


@bot.message_handler(content_types=['text'], commands=['abort'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text)
    bot.abort_command(in_msg)


@bot.message_handler(content_types=['text'], commands=['quote'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text)
    bot.quote_command(in_msg)


@bot.message_handler(content_types=['text'], func=lambda message: is_new_subscription_time(message.chat.type,
                                                                                           message.text))
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text)
    bot.process_new_subscription_time(in_msg)


@bot.message_handler(content_types=['text'], func=lambda message: bot.user_handler.is_new_quote(message))
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text)
    bot.process_user_text_quote(in_msg)


@bot.message_handler(content_types=['text'], func=lambda message: bot.user_handler.is_new_job(message))
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text)
    bot.process_new_job(in_msg)


@bot.message_handler(content_types=['photo'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text, 'photo',
                             message.photo[len(message.photo) - 1].file_id)
    bot.process_user_media_quote(in_msg)


@bot.message_handler(content_types=['audio'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text, 'audio',
                             message.audio.file_id)
    bot.process_user_media_quote(in_msg)


@bot.message_handler(content_types=['voice'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text, 'voice',
                             message.voice.file_id)
    bot.process_user_media_quote(in_msg)


@bot.message_handler(content_types=['video'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text, 'video',
                             message.video.file_id)
    bot.process_user_media_quote(in_msg)


@bot.message_handler(content_types=['video_note'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text, 'video_note',
                             message.video_note.file_id)
    bot.process_user_media_quote(in_msg)


@bot.message_handler(content_types=['location'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text, 'location')
    bot.send_rdm_location(in_msg)


@bot.message_handler(content_types=['sticker'])
def handle_command(message):
    in_msg = IncomingMessage(message.chat.id, message.chat.type, message.from_user.id, message.from_user.first_name,
                             message.from_user.last_name, message.from_user.username, message.text, 'sticker')
    bot.send_wolf_sticker(in_msg)


def main():
    bot.polling(none_stop=True, interval=1, timeout=5)


if __name__ == "__main__":
    main()
