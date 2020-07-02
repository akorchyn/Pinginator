import os
from datetime import datetime, time

from pymongo import MongoClient
from telebot import TeleBot, types

import db
from group import User
from inline_keyboard_paginator import InlineKeyboardPaginator

if 'BOT_TOKEN' not in os.environ or 'BOT_LOGIN' not in os.environ or 'BOT_NAME' not in os.environ:
    print("Please set env variables: BOT_TOKEN, BOT_LOGIN, BOT_NAME")
    exit(0)

TOKEN = os.environ['BOT_TOKEN']
LOGIN = os.environ['BOT_LOGIN']
NAME = os.environ['BOT_NAME']
TIME_RANGE = [str(x) for x in range(24)]

from_inline_keyboard_paginator = InlineKeyboardPaginator(TIME_RANGE, 4, "from")
to_inline_keyboard_paginator = InlineKeyboardPaginator(TIME_RANGE, 4, "to")

db = db.PinginatorDb(MongoClient(os.environ['MONGODB_URI']), os.environ['DB'])
bot = TeleBot(TOKEN)


def is_creator(group_id, user_id):
    status = bot.get_chat_member(group_id, user_id)
    return status.status == 'creator'


def is_administrator(group_id: int, user_id: int) -> bool:
    administrators = bot.get_chat_administrators(group_id)
    return True in [adm.user.id == user_id for adm in administrators]


def try_insert_user(group_id: int, user: types.User, chat_type: str):
    if chat_type != 'private' and not user.is_bot:
        db.insert_user(group_id, User(user.id))


@bot.message_handler(commands=['ping', 'all'], func=lambda message: message.chat.type == 'private')
def private_message_text_handler(message: types.Message):
    bot.send_message(message.chat.id, 'I AM A GROUP BOT :C')


@bot.message_handler(commands=['ping', 'all'])
def text_handler(message: types.Message):
    group_id = message.chat.id
    try_insert_user(group_id, message.from_user, message.chat.type)
    group = db.get_group(group_id)
    if group.is_quiet_hours_enabled(datetime.fromtimestamp(message.date)):
        bot.send_message(group_id, 'Quiet hour politic is enabled now. I can\'t send a message.'
                                   ' Please, use after ' + str(time(group.quiet_hours[1], 0)) +
                         ', or change politic if you are the creator.')
        return
    elif group.is_admin_only and not is_administrator(group_id, message.from_user.id):
        bot.send_message(group_id, 'Sorry, only administrator could use this functionality')
        return
    text = ''
    for user in group.users:
        if user.id == message.from_user.id:
            continue
        user_info: types.User = bot.get_chat_member(group_id, user.id).user
        if user_info is not None:
            text += '[{}](tg://user?id={}), '.format(
                user_info.first_name if user_info.username is None else '@' + user_info.username, user_info.id)
    if len(text) > 0:
        bot.send_message(message.chat.id, text[:-2], parse_mode='markdown')


@bot.callback_query_handler(func=lambda query: not is_creator(query.message.chat.id, query.from_user.id))
def restricted_quiet_hours_callback(query: types.CallbackQuery):
    try_insert_user(query.message.chat.id, query.from_user, query.message.chat.type)
    bot.answer_callback_query(query.id, 'You are not privileged to configure this.', show_alert=True)


@bot.callback_query_handler(func=lambda query: from_inline_keyboard_paginator.corresponds_to_keyboard(query.data))
def quiet_beginning_hours_callback(query: types.CallbackQuery):
    group_id = query.message.chat.id
    is_data, data = from_inline_keyboard_paginator.get_content(query.data)
    if is_data:
        db.add_beginning_quiet_hour(group_id, int(data))
        bot.delete_message(group_id, query.message.message_id)
        bot.send_message(group_id, 'Well done. I remember that, but what about the ending?',
                         reply_markup=to_inline_keyboard_paginator.get(0))
    else:
        bot.edit_message_reply_markup(group_id, message_id=query.message.message_id,
                                      reply_markup=from_inline_keyboard_paginator.get(data))


@bot.callback_query_handler(func=lambda query: to_inline_keyboard_paginator.corresponds_to_keyboard(query.data))
def quiet_ending_hours_callback(query: types.CallbackQuery):
    group_id = query.message.chat.id
    is_data, data = to_inline_keyboard_paginator.get_content(query.data)
    if is_data:
        db.add_ending_quiet_hour(group_id, int(data))
        bot.delete_message(group_id, query.message.message_id)
        bot.send_message(group_id, 'Configuration is done. Have a nice day')
    else:
        bot.edit_message_reply_markup(group_id, message_id=query.message.message_id,
                                      reply_markup=to_inline_keyboard_paginator.get(data))


@bot.message_handler(commands=['quiet_hours'], func=lambda message: is_creator(message.chat.id, message.from_user.id))
def admin_configuration_quiet_handler(message: types.Message):
    try_insert_user(message.chat.id, message.from_user, message.chat.type)
    bot.send_message(message.chat.id, 'Let\'s configure quiet hours. Please choose the beginning hour.\n'
                                      'Please, note: only the creator could use a button.',
                     reply_markup=from_inline_keyboard_paginator.get(0))


@bot.message_handler(commands=['quiet_hours'])
def guest_quiet_handler(message):
    try_insert_user(message.chat.id, message.from_user, message.chat.type)
    bot.send_message(message.chat.id, 'Sorry, you are not privileged to configure this')


@bot.message_handler(commands=['start', 'help'])
def start_handler(message):
    bot.send_message(message.chat.id, 'Hi ' + message.from_user.first_name + ',\n\nI am '
                     + NAME + ', a bot which would help you to notify all people in a group.\n\n'
                              'Use /ping or /all in a chat to take attention\n\n'
                              'Also, you could configure me:\nUse /quiet_hours to set a time range '
                              'in which I won\'t ping anyone\nWrite /admin_only to introduce a dictatorship of '
                              'administrators into your chat.\n')
    try_insert_user(message.chat.id, message.from_user, message.chat.type)


@bot.message_handler(commands=['admin_only'], func=lambda message: is_creator(message.chat.id, message.from_user.id))
def set_admin_only(message: types.Message):
    new_value = db.change_admin_only_flag(message.chat.id)
    bot.send_message(message.chat.id,
                     "Done. Only the admins could use pings" if new_value else "Done. Anyone could ping. ANARCHY!!!!")


@bot.message_handler(commands=['admin_only'])
def restricted_admin_change(message: types.Message):
    bot.send_message(message.chat.id, "Only the creator of the group could configure it.")


@bot.message_handler(content_types=["new_chat_members"])
def handler_new_member(message: types.Message):
    for member in message.new_chat_members:
        try_insert_user(message.chat.id, member, message.chat.type)


@bot.message_handler(content_types=["left_chat_member"])
def handler_left_member(message: types.Message):
    if message.left_chat_member.username == LOGIN:  # Bot kicked from the chat, delete collected users
        db.remove_chat(message.chat.id)
    else:
        db.remove_user(message.chat.id, User(message.left_chat_member.id))


@bot.message_handler(content_types=["text"])
def handler_text(message):
    if '@' + LOGIN in message.text:
        bot.send_message(message.chat.id, '@' + message.from_user.username)
    elif NAME in message.text:
        bot.send_message(message.chat.id, 'Am I joke to you?')
    try_insert_user(message.chat.id, message.from_user, message.chat.type)


bot.polling()
