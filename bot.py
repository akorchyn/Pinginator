import logging
import os

from pymongo import MongoClient
from telegram import Update
from telegram.error import Unauthorized, ChatMigrated
from telegram.ext import Updater, Dispatcher, CallbackContext

import pinginator.common.exceptions as internal_exceptions
from pinginator.commands_handling.basic_commands import DISPATCHER_HANDLERS
from pinginator.commands_handling.bot_configuration import CONFIGURATION_COMMANDS
from pinginator.commands_handling.telegram_status_updates import TELEGRAM_HANDLES
from pinginator.common import db

if 'BOT_TOKEN' not in os.environ or 'MONGODB_URI' not in os.environ:
    print("Please set env variables: BOT_TOKEN, MONGODB_URI")
    exit(0)

TOKEN = os.environ['BOT_TOKEN']

updater = Updater(token=TOKEN, use_context=True)
dispatcher: Dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

db = db.PinginatorDb(MongoClient(os.environ['MONGODB_URI']), os.environ['DB'])


def error_callback(update: Update, context: CallbackContext):
    try:
        raise context.error
    except Unauthorized:
        db.remove_chat(update.effective_chat.id)
    except ChatMigrated as e:
        context.bot.send_message(e.new_chat_id, "New group, new life! Migration succeed")
        db.migrate_group(update.effective_chat.id, e.new_chat_id)
    except internal_exceptions.AccessDenied:
        context.bot.send_message(update.effective_chat.id, "Sorry, you are not privileged to do this.")
    except internal_exceptions.QueryAccessDenied:
        context.bot.answer_callback_query(update.callback_query.id, 'Sorry, you are not privileged to do this.')


dispatcher.bot_data['db'] = db
dispatcher.add_error_handler(error_callback)
for handles in [DISPATCHER_HANDLERS, CONFIGURATION_COMMANDS, TELEGRAM_HANDLES]:
    for handler in handles:
        dispatcher.add_handler(handler)
updater.start_polling()
