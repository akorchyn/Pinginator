import functools

from telegram import Bot, Update
from telegram.ext import CallbackContext

from pinginator.common.exceptions import AccessDenied, QueryAccessDenied
from pinginator.common.group import User
from pinginator.helpers.user_loading import TELETHON_ENABLED


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
        if TELETHON_ENABLED:
            return func(update, context)
        db = context.bot_data['db']
        if update.effective_chat.type != 'private' and not update.effective_user.is_bot:
            db.insert_user(update.effective_chat.id, User(update.effective_user.id))
        for new_chat_member in update.effective_message.new_chat_members:
            if new_chat_member.is_bot:
                continue
            db.insert_user(update.effective_chat.id, User(new_chat_member.id))
        return func(update, context)

    return wrapper


def creator_only_handle(func):
    """
    If given user is not a creator, restrict access.
    """

    @functools.wraps(func)
    def wrapper(update: Update, context: CallbackContext):
        if not is_creator(context.bot, update.effective_chat.id, update.effective_user.id):
            raise AccessDenied()
        return func(update, context)

    return wrapper


def creator_only_query(func):
    """
    If given user is not a creator, restrict access.
    """

    @functools.wraps(func)
    def wrapper(update: Update, context: CallbackContext):
        query = update.callback_query
        if not is_creator(context.bot, update.effective_chat.id, query.from_user.id):
            raise QueryAccessDenied()
        return func(update, context)

    return wrapper
