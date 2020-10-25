from telegram import Bot

from pinginator.common.group import UserInfo

import os

telethon_client = None
TELETHON_ENABLED = False

if 'TELETHON_OPTIMIZATION' in os.environ and 'BOT_ID' in os.environ and 'BOT_HASH_ID' in os.environ:
    if os.environ['TELETHON_OPTIMIZATION'] == "On":
        try:
            from telethon import TelegramClient
            from telethon.tl.types import InputPeerChat
            api_hash = os.environ['BOT_HASH_ID']
            api_id = os.environ['BOT_ID']
            token = os.environ['BOT_TOKEN']

            telethon_client = TelegramClient('session_name', api_id, api_hash).start(bot_token=token)
            TELETHON_ENABLED = True
        except ModuleNotFoundError:
            print("Telethon is not available. Fallback to default one")
            pass


def __load_users_from_mtproto(chat_id: int) -> [UserInfo]:
    """
    Loading from the mtproto means that telethon available on system, and we can load list of users from the channel.
    """
    if not TELETHON_ENABLED:
        return []
    users = telethon_client.iter_participants(InputPeerChat(chat_id))
    result = []
    for user in users:
        if user.bot:
            continue
        result.append(UserInfo(user.id, user.username, user.first_name, user.last_name))
    return result


def load_users_info_from_group(bot: Bot, group) -> [UserInfo]:
    result = __load_users_from_mtproto(group.id)
    if not result:
        for user_id in group.users:
            user = bot.get_chat_member(group.id, user_id.id).user
            result.append(UserInfo(user.id, user.username, user.first_name, user.last_name))
    return result
