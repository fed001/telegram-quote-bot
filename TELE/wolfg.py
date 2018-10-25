#-*- coding: UTF-8 -*-
"""
Wolfg
"""
import argparse
import logging
import sys
from os import path, environ
import telebot
from core.non_text_deco import NonTextDeco, PhotoDeco, VideoDeco, VoiceDeco, AudioDeco, LocationDeco, \
    StickerDeco, VideoNoteDeco
from core.text_deco import TextDeco

if __package__ is None:
    sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
else:
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from TELE.my_tele import MyTele
from TELE.tele_dialogue import TeleDialogue
from TELE.inline import inline_default_proc
logger = telebot.logger
telebot.logger.setLevel(logging.INFO)  # Outputs INFO/DEBUG messages to console.
from TELE.tele_utils import send_sticker, tele_get_user

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser(description='WOLFG Telegram Chatbot')
ap.add_argument('--game', dest='game', action='store_const',
                     const=True, default=False,
                     help='enable Game Support (default: disabled)')
args = vars(ap.parse_args())

inline_game_howto_text = "Start typing game name and choose a game from the list. Use this in any Chat."

if args["game"] is True:
    game_server_ip = environ['GAME_SERVER_IP']

token = environ['WOLFG_TELE_TOKEN']
bot = MyTele(token)


@bot.message_handler(commands = ['howto_inline_mode'])
def handle_command(message):
    """
    Send a howto message explaining inline mode.
    """
    user = tele_get_user(message)
    dia = TeleDialogue(message.chat.id, message.from_user.id, message.text, user, message.chat.type)
    dia.InMsg = TextDeco(dia.InMsg)
    dia.InMsg.print_in_msg(dia)
    bot.send_message(message.chat.id, inline_game_howto_text)


@bot.message_handler(content_types = ['text', 'photo', 'audio', 'voice', 'video', 'video_note'])
def handle_command(message):
    """Handle messages."""
    user = tele_get_user(message)
    dia = TeleDialogue(message.chat.id, message.from_user.id, message.text, user, message.chat.type, None, args)

    if message.text is not None:
        dia.InMsg = TextDeco(dia.InMsg)
    elif message.photo is not None:
        dia.InMsg = PhotoDeco(dia.InMsg, message.photo[len(message.photo) - 1].file_id)
    elif message.audio is not None:
        dia.InMsg = AudioDeco(dia.InMsg, message.audio.file_id)
    elif message.voice is not None:
        dia.InMsg = VoiceDeco(dia.InMsg, message.voice.file_id)
    elif message.video is not None:
        dia.InMsg = VideoDeco(dia.InMsg, message.video.file_id)
    elif message.video_note is not None:
        dia.InMsg = VideoNoteDeco(dia.InMsg, message.video_note.file_id)

    dia.InMsg.process_input(dia)
    dia.process_output()

    if 'game_short_name' in dia.OutMsg.tele_kwargs.keys():
        bot.send_game(**dia.OutMsg.tele_kwargs)
        dia.OutMsg = TextDeco(dia.OutMsg)
    elif 'photo' in dia.OutMsg.tele_kwargs.keys():
        bot.send_photo(**dia.OutMsg.tele_kwargs)
        dia.OutMsg = PhotoDeco(dia.OutMsg)
    elif 'audio' in dia.OutMsg.tele_kwargs.keys():
        bot.send_audio(**dia.OutMsg.tele_kwargs)
        dia.OutMsg = AudioDeco(dia.OutMsg)
    elif 'voice' in dia.OutMsg.tele_kwargs.keys():
        bot.send_voice(**dia.OutMsg.tele_kwargs)
        dia.OutMsg = VoiceDeco(dia.OutMsg)
    elif 'data' in dia.OutMsg.tele_kwargs.keys() and dia.OutMsg.item == 'video':
        bot.send_video(**dia.OutMsg.tele_kwargs)
        dia.OutMsg = VideoDeco(dia.OutMsg)
    elif 'data' in dia.OutMsg.tele_kwargs.keys() and dia.OutMsg.item == 'videonote':
        bot.send_video_note(**dia.OutMsg.tele_kwargs)
        dia.OutMsg = VideoNoteDeco(dia.OutMsg)
    elif dia.is_valid_kwargs():
        bot.send_message(**dia.OutMsg.tele_kwargs)
        dia.OutMsg = TextDeco(dia.OutMsg)
    else:
        dia.InMsg.print_in_msg(dia)
        return

    dia.InMsg.print_in_msg(dia)
    dia.OutMsg.print_out_msg()


@bot.message_handler(content_types = ['document'])
def handle_command(message):
    user = tele_get_user(message)
    dia = TeleDialogue(message.chat.id, message.from_user.id, message.text, user, message.chat.type)
    dia.InMsg = NonTextDeco(dia.InMsg)
    dia.InMsg.item = 'Document'
    dia.InMsg.print_in_msg(dia)


@bot.message_handler(content_types = ['location'])
def handle_command(message):
    dia = TeleDialogue(message.chat.id, message.from_user.id, message.text, message.chat.first_name + message.chat.last_name, message.chat.type)
    dia.InMsg = LocationDeco(dia.InMsg)
    dia.InMsg.print_in_msg(dia)


@bot.message_handler(content_types = ['sticker'])
def handle_command(message):
    user = tele_get_user(message)
    dia = TeleDialogue(message.chat.id, message.from_user.id, message.text, user, message.chat.type)
    dia.InMsg = StickerDeco(dia.InMsg)
    dia.InMsg.print_in_msg(dia)
    send_sticker(bot, dia.chat_id, 'CAADAgADCwEAAvR7GQABuArOzKHFjusC')
    dia.stop_awaiting_quote()
    dia.OutMsg = StickerDeco(dia.OutMsg)
    dia.OutMsg.print_out_msg()


@bot.callback_query_handler(lambda callback_query: callback_query.game_short_name == 'mygame' and args['game'])
def handle_query(callback_query):
    """Start game: Send game URL incl. parameters."""
    user_name = tele_get_user(callback_query)

    if callback_query.message is not None:
        msg_id = callback_query.message.message_id
        chat_id = str(callback_query.message.chat.id)
        args = 'msg_id=' + str(msg_id)
    elif callback_query.inline_message_id is not None:
        inline_msg_id = callback_query.inline_message_id
        chat_id = str(callback_query.from_user.id)
        args = 'inline_msg_id=' + str(inline_msg_id)
        
    args += '&chat_id=' + chat_id
    args += '&chat_instance=' + str(callback_query.chat_instance)
    args += '&user_name=' + user_name.replace(' ', '%20')

    bot.answer_callback_query(callback_query.id, url = game_server_ip + '/pong?' + args)


@bot.inline_handler(lambda query: args['game'])
def default_query(inline_query):
    """
    Show the default game Pong for inline query.
    """
    logger.info("User looking at default inline query.")

    try:
        inline_default_proc(bot, inline_query)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    bot.polling(none_stop = True, interval = 0, timeout = 3)
