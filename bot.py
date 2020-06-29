import os
from datetime import datetime

from telebot import TeleBot, types

import db
from group import User

if 'BOT_TOKEN' not in os.environ or 'BOT_LOGIN' not in os.environ or 'BOT_NAME' not in os.environ:
    print("Please set env variables: BOT_TOKEN, BOT_LOGIN, BOT_NAME")
    exit(0)

TOKEN = os.environ['BOT_TOKEN']
LOGIN = os.environ['BOT_LOGIN']
NAME = os.environ['BOT_NAME']
bot = TeleBot(TOKEN)
db = db.PinginatorDb()


def is_creator(group_id, user_id):
    status = bot.get_chat_member(group_id, user_id)
    return status.status == 'creator'


def create_quiet_keyboard(is_begin: bool):
    keyboard = types.InlineKeyboardMarkup()
    buttons = ([types.InlineKeyboardButton(text=str(x),
                                           callback_data=('from_' if is_begin else 'to_') + str(x)) for x in
                range(1, 25)])
    for button in buttons:
        keyboard.add(button)
    return keyboard


def try_insert_user(group_id: int, user: types.User, chat_type: str):
    if chat_type != 'private' and user.username is not None:
        db.insert_user(group_id, User(user.username))


@bot.message_handler(commands=['ping', 'all'])
def text_handler(message: types.Message):
    group_id = message.chat.id
    if message.chat.type == 'private':
        bot.send_message(group_id, 'I AM A GROUP BOT :C')
        return

    try_insert_user(group_id, message.from_user, message.chat.type)
    group = db.get_group(group_id)
    if group.is_quiet_hours_enabled(datetime.fromtimestamp(message.date)):
        bot.send_message(group_id, 'Quiet hour politic is enabled now. I can\'t send a message.'
                                   ' Please, use after ' + str(group.quite_hour_ending()) +
                         ', or change politic if you are the creator.')
        return

    text = ''
    for user in group.get_users():
        if user.name != message.from_user.username:
            text += '@' + user.name + ' '
    if len(text) > 0:
        bot.send_message(message.chat.id, text)


@bot.callback_query_handler(func=lambda message: True)
def quiet_hours_parser(query: types.CallbackQuery):
    is_user_a_creator = is_creator(query.message.chat.id, query.from_user.id)
    group_id = query.message.chat.id
    try_insert_user(group_id, query.from_user, query.message.chat.type)
    if 'from' in query.data:
        if not is_user_a_creator:
            bot.answer_callback_query(query.id, 'You are not privileged to configure this.', show_alert=True)
            return
        db.add_beginning_quiet_hour(group_id, int(query.data.split('_')[1]))
        bot.delete_message(group_id, query.message.message_id)
        bot.send_message(group_id, 'Well done. I remember that, but what about the ending?',
                         reply_markup=create_quiet_keyboard(False))
    elif 'to' in query.data:
        if not is_user_a_creator:
            bot.answer_callback_query(query.id, 'You are not privileged to configure this.', show_alert=True)
            return
        db.add_ending_quiet_hour(group_id, int(query.data.split('_')[1]))
        bot.delete_message(group_id, query.message.message_id)
        bot.send_message(group_id, 'Configuration is done. BYE')


@bot.message_handler(commands=['quiet_hours'])
def quiet_handler(message):
    try_insert_user(message.chat.id, message.from_user, message.chat.type)
    if not is_creator(message.chat.id, message.from_user.id):
        bot.send_message(message.chat.id, 'Sorry, you are not privileged to configure this')
        return
    bot.send_message(message.chat.id, 'Let\'s configure quiet hours. Please choose the beginning hour.\n'
                                      'Please, note: only the creator could use a button.',
                     reply_markup=create_quiet_keyboard(True))


@bot.message_handler(commands=['start', 'help'])
def start_handler(message):
    bot.send_message(message.chat.id, 'Hello ' + message.from_user.first_name + ', my name is ' + NAME +
                     '.\nI will ping all user in group, if you use /ping or /all\n' +
                     ('I am useless in private chat. I am group bot.' if message.chat.type == 'private' else ''))
    try_insert_user(message.chat.id, message.from_user, message.chat.type)


@bot.message_handler(content_types=["new_chat_members"])
def handler_new_member(message: types.Message):
    for member in message.new_chat_members:
        try_insert_user(message.chat.id, member, message.chat.type)


@bot.message_handler(content_types=["left_chat_member"])
def handler_left_member(message):
    db.remove_user(message.chat.id, User(message.from_user.username))


@bot.message_handler(content_types=["text"])
def handler_text(message):
    if '@' + LOGIN in message.text:
        bot.send_message(message.chat.id, '@' + message.from_user.username)
    elif NAME in message.text:
        bot.send_message(message.chat.id, 'Am I joke to you?')
    try_insert_user(message.chat.id, message.from_user, message.chat.type)


bot.polling()
