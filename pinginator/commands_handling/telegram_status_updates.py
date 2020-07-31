from telegram import Update
from telegram.ext import CallbackContext, Filters, MessageHandler

import pinginator.helpers.helpers as helpers
from pinginator.common.group import User


@helpers.insert_user
def insert_user(*_):
    pass


def remove_user(update: Update, context: CallbackContext):
    if update.effective_message.left_chat_member.id == context.bot.id:
        context.bot_data['db'].remove_group(update.effective_chat.id)
        return
    context.bot_data['db'].remove_user(update.effective_chat.id,
                                       User(update.effective_message.left_chat_member.id))


def group_upgraded_to_supergroup(update: Update, context: CallbackContext):
    if update.effective_message.migrate_to_chat_id is not None:
        context.bot_data['db'].migrate_group(update.effective_chat.id, update.effective_message.migrate_to_chat_id)


TELEGRAM_HANDLES = [MessageHandler(Filters.status_update & (~Filters.status_update.left_chat_member)
                                   & (~Filters.status_update.migrate), callback=insert_user),
                    MessageHandler(Filters.status_update.left_chat_member, remove_user),
                    MessageHandler(Filters.status_update.migrate, group_upgraded_to_supergroup)
                    ]
