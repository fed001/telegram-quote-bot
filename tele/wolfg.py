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

from tele.my_tele import MyTele
from tele.tele_dialogue import TeleDialogue
logger = telebot.logger
telebot.logger.setLevel(logging.INFO)  # Outputs INFO/DEBUG messages to console.
from tele.tele_utils import send_sticker, tele_get_user

token = environ['WOLFG_TELE_TOKEN']
bot = MyTele(token)


@bot.message_handler(content_types = ['text', 'photo', 'audio', 'voice', 'video', 'video_note'])
def handle_command(message):
    """Handle messages."""
    user = tele_get_user(message)
    dia = TeleDialogue(message.chat.id, message.from_user.id, message.text, user, message.chat.type, None)

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

    if 'photo' in dia.OutMsg.tele_kwargs.keys():
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


if __name__ == "__main__":
    bot.polling(none_stop = True, interval = 0, timeout = 3)
