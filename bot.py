import logging
import os
import traceback

from pymongo import MongoClient
from telegram import Update
from telegram.error import Unauthorized, ChatMigrated, NetworkError, BadRequest
from telegram.ext import Updater, Dispatcher, CallbackContext

import pinginator.common.exceptions as internal_exceptions
from pinginator.commands_handling.basic_commands import DISPATCHER_HANDLERS
from pinginator.commands_handling.bot_configuration import CONFIGURATION_COMMANDS
from pinginator.commands_handling.scheduled_messages import SCHEDULED_MESSAGE_COMMANDS, load_jobs
from pinginator.commands_handling.telegram_status_updates import TELEGRAM_HANDLES
from pinginator.common import db

if 'BOT_TOKEN' not in os.environ or 'DB_URL' not in os.environ:
    print("Please set env variables: BOT_TOKEN, DB_URL")
    exit(0)

OWNER_ID = int(os.environ['OWNER_ID']) if 'OWNER_ID' in os.environ else None
TOKEN = os.environ['BOT_TOKEN']

updater = Updater(token=TOKEN, use_context=True)
dispatcher: Dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

db = db.PinginatorDb(MongoClient(os.environ['DB_URL']), os.environ['DB'])


def write_to_owner(update: Update):
    if OWNER_ID is not None:
        message = "Exception threw located:\nUpdate:\n```" + update.to_dict().__str__() + "```\n" + \
                  "Traceback:\n```" + traceback.format_exc() + "```"
        dispatcher.bot.send_message(OWNER_ID, message, parse_mode="Markdown")


def error_callback(update: Update, context: CallbackContext):
    try:
        raise context.error
    except Unauthorized:
        db.remove_group(update.effective_chat.id)
    except ChatMigrated as e:
        db.migrate_group(update.effective_chat.id, e.new_chat_id)
    except internal_exceptions.AccessDenied:
        context.bot.send_message(update.effective_chat.id, "Sorry, you are not privileged to do this.")
    except internal_exceptions.QueryAccessDenied:
        context.bot.answer_callback_query(update.callback_query.id, 'Sorry, you are not privileged to do this.')
    except (NetworkError, BadRequest) as e:
        logging.getLogger().critical(e)
    except BaseException as e:
        write_to_owner(update)
        raise e


dispatcher.bot_data['db'] = db
dispatcher.bot_data['waiting_input'] = []
dispatcher.add_error_handler(error_callback)
load_jobs(dispatcher.job_queue, db)
for handles in [DISPATCHER_HANDLERS, CONFIGURATION_COMMANDS, TELEGRAM_HANDLES, SCHEDULED_MESSAGE_COMMANDS]:
    for handler in handles:
        dispatcher.add_handler(handler)
updater.start_polling()
