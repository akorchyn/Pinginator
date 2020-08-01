import functools

from telegram import Bot, Update
from telegram.ext import CallbackContext

from pinginator.common.group import User


def get_admin_ids(bot: Bot, chat_id: int):
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]


def is_creator(bot: Bot, group_id: int, user_id: int) -> bool:
    status = bot.get_chat_member(group_id, user_id)
    return status.status == 'creator'


def is_administrator(bot: Bot, group_id: int, user_id: int) -> bool:
    return user_id in get_admin_ids(bot, group_id)


def insert_user(func):
    """
    If given user is not a bot and chat_type is not a private, the decorator tries to store into the given database
    """

    @functools.wraps(func)
    def wrapper(update: Update, context: CallbackContext):
        db = context.bot_data['db']
        if update.effective_chat.type != 'private' and not update.effective_user.is_bot:
            db.insert_user(update.effective_chat.id, User(update.effective_user.id))
        for new_chat_member in update.effective_message.new_chat_members:
            if new_chat_member.is_bot:
                continue
            db.insert_user(update.effective_chat.id, User(new_chat_member.id))
        return func(update, context)

    return wrapper
