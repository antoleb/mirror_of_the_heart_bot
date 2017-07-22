#!/usr/bin/python3

import datetime
import os
import requests
import settings
import sys
import uuid
from io import BytesIO
from urllib import request

import cv2
import numpy as np
import telebot
from PIL import Image
from telebot import types

from eye_swap import EyeSwapper


bot = telebot.TeleBot(settings.API_TOKEN)
eye_swapper = EyeSwapper()

chat_photo = dict()


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, settings.HELP_MESSAGE)


def receive_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    file_url = 'https://api.telegram.org/file/bot{}/{}'.format(settings.API_TOKEN, file_info.file_path)
    raw_img = request.urlopen(file_url).read()

    arr = np.asarray(bytearray(raw_img), dtype=np.uint8)
    img = cv2.imdecode(arr,-1)
    return img


def ask_processor(message):
    markup = types.ReplyKeyboardMarkup(row_width=4)
    for eye_type_name in eye_swapper.eye_types():
        button = types.KeyboardButton(eye_type_name)
        markup.add(button)
    bot.send_message(message.chat.id, "Choose eyes!", reply_markup=markup)

def save_img(image):
    path = os.path.join(settings.SAVE_PATH, str(uuid.uuid4()) + '.png')
    cv2.imwrite(path, image)

    return path


@bot.message_handler(content_types=['text'])
def handle_eye_type(message):
    img = chat_photo.get(message.chat.id, None)
    if img is None:
        bot.send_message(message.chat.id, settings.ONLY_PHOTO_MESSAGE)
        return
    processed_img = eye_swapper.process_img(img, message.text)
    if processed_img is not None:
        path = save_img(processed_img)
        bot.send_photo(message.chat.id, open(path, 'rb'))
    else:
        bot.send_message(message.chat.id, settings.BAD_IMAGE_MESSAGE)


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        img = receive_photo(message)
        chat_photo[message.chat.id] = img
        ask_processor(message)
    except:
        bot.send_message(message.chat.id, settings.BAD_IMAGE_MESSAGE)

if __name__ == '__main__':
    bot.polling()
