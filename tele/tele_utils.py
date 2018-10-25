#-*- coding: UTF-8 -*-
import time
from time import sleep
from core.dbQuery import query


def send_voice(bot, chat_id, path):
    with open(path, 'r') as voiceFile:
        bot.send_chat_action(chat_id, 'record_audio')
        bot.send_voice(chat_id, voiceFile)


def send_photo(bot, chat_id, path):
    with open(path, 'r') as f1:
        bot.send_chat_action(chat_id, 'upload_photo')
        bot.send_photo(chat_id, f1)


def send_gif_video(bot, chat_id, path):
    with open(path, 'r') as f1:
        bot.send_chat_action(chat_id, 'upload_video')
        bot.send_document(chat_id, f1)


def send_mp4_video(bot, chat_id, path):
    with open(path, 'r') as f1:
        bot.send_chat_action(chat_id, 'upload_video_note')
        bot.send_video_note(chat_id, f1)


def send_sticker(bot, chat_id, file_id):
    bot.send_sticker(chat_id, file_id)


def tele_get_user(message):
    sleep(0.1)
    has_first_name = message.from_user.first_name is not None
    has_last_name = message.from_user.last_name is not None
    has_user_name = message.from_user.username is not None
    if has_first_name and has_last_name:
        return message.from_user.first_name + ' ' + message.from_user.last_name
    elif has_first_name:
        return message.from_user.first_name
    elif has_last_name:
        return message.from_user.last_name
    elif has_user_name:
        return message.from_user.user_name
