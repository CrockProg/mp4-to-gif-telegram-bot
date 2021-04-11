#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.


import logging
import subprocess
import time

from functools import wraps
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import NetworkError
from telegram import ChatAction
from ffmpy3 import FFmpeg
from config import TG_TOKEN
from config import FOLDER


#Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

last_time = {}

def send_action(action):
    """Sends `action` while processing func command."""
    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(update, context,  *args, **kwargs)
        return command_func

    return decorator


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi! I can convert .mp4 to .gif')


def help_command(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Send a video file')


@send_action(ChatAction.UPLOAD_VIDEO)
def video_handler(update, context):
    """Anti-Flood"""
    chat_id = update.message.chat_id
    if chat_id not in last_time:
        last_time[chat_id] = time.time()
    else:
        if (time.time() - last_time[chat_id]) * 1000 < 3000:
            return 0
        last_time[chat_id] = time.time()

    """Create a gif when user sends a video"""
    update.message.reply_text('Processing...')
    file = context.bot.getFile(update.message.video.file_id)
    file_id = str(update.message.video.file_id)
    file.download(FOLDER+file_id+'.mp4')
    ff = FFmpeg(
        inputs = {FOLDER+file_id+'.mp4' : None},
        outputs = {FOLDER+file_id+'.gif' : ['-vf', "fps=14,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"]})
    subprocess.call(ff.cmd)
    try:
        context.bot.send_animation(chat_id=chat_id, animation=open(FOLDER+file_id+'.gif', 'rb'))
    except NetworkError:
        update.message.reply_text('File is too large!')

def main():
    """Start the bot."""
    #Create the Updater and pass it your bot's token.
    updater = Updater(TG_TOKEN, use_context=True)

    #Get the dispatcher to register handlers
    dp = updater.dispatcher

    #on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))

    #on noncommand video message - catch it
    dp.add_handler(MessageHandler(Filters.video, video_handler, run_async=True))

    #Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    updater.idle()


if __name__ == '__main__':
    main()
