from telegram import Update
from telegram.ext import CallbackContext, Filters, MessageHandler

import pinginator.helpers.helpers as helpers
from pinginator.common.group import User


@helpers.insert_user
def insert_user(*_):
    pass


def remove_user(update: Update, context: CallbackContext):
    context.bot_data['db'].remove_user(update.effective_chat.id,
                                       User(update.effective_message.left_chat_member.id))


TELEGRAM_HANDLES = [MessageHandler(Filters.status_update & (~Filters.status_update.left_chat_member),
                                   callback=insert_user),
                    MessageHandler(Filters.status_update.left_chat_member, remove_user)
                    ]
