import os

import pymongo
from telebot import TeleBot, types

if 'BOT_TOKEN' not in os.environ or 'BOT_LOGIN' not in os.environ or 'BOT_NAME' not in os.environ:
    print("Please set env variables: BOT_TOKEN, BOT_LOGIN, BOT_NAME")
    exit(0)

TOKEN = os.environ['BOT_TOKEN']
LOGIN = os.environ['BOT_LOGIN']
NAME = os.environ['BOT_NAME']
client = pymongo.MongoClient()
db = client['PinginatorDb']
groups = db['groups']
bot = TeleBot(TOKEN)


def add_beginning_quite_hour(chat_id, beginning_quite_hour):
    groups.update_one({'_id': chat_id},
                      {'$set': {'beginning_quite_hour': beginning_quite_hour}}, True)


def add_ending_quite_hour(chat_id, ending_quite_hour):
    groups.update_one({'_id': chat_id},
                      {'$set': {'ending_quite_hour': ending_quite_hour}}, True)


def is_creator(chat_id, user_id):
    status = bot.get_chat_member(chat_id=chat_id, user_id=user_id)
    return status.status == 'creator'


def is_active_quite_hour(chat_id):
    return False


def create_quite_keyboard(is_begin: bool):
    keyboard = types.InlineKeyboardMarkup()
    buttons = ([types.InlineKeyboardButton(text=str(x),
                                           callback_data=('from_' if is_begin else 'to_') + str(x)) for x in
                range(1, 25)])
    for button in buttons:
        keyboard.add(button)
    return keyboard


def insert_user(message, user=None):
    user = message.from_user if user is None else user
    if message.chat.type != 'private' and user.username is not None:
        groups.update_one({'_id': message.chat.id},
                          {'$addToSet': {'users': user.username}}, True)


@bot.message_handler(commands=['ping', 'all'])
def text_handler(message):
    insert_user(message)
    if is_active_quite_hour(message.chat.id):
        return
    chat_id = message.chat.id
    is_private = message.chat.type == 'private'
    if is_private:
        bot.send_message(chat_id, 'I AM A GROUP BOT :C')
    else:
        text = ''
        group = groups.find_one({'_id': chat_id})
        for user in group['users']:
            if user != message.from_user.username:
                text += '@' + user + ' '
        if len(text) > 0:
            bot.send_message(message.chat.id, text)


@bot.callback_query_handler(func=lambda message: True)
def quite_hours_parser(query: types.CallbackQuery):
    is_user_a_creator = is_creator(query.message.chat.id, query.from_user.id)
    if 'from' in query.data:
        if not is_user_a_creator:
            bot.answer_callback_query(query.id, 'You are not privileged to configure this.', show_alert=True)
            return
        add_beginning_quite_hour(query.message.chat.id, query.data.split('_')[1])
        bot.delete_message(query.message.chat.id, query.message.message_id)
        bot.send_message(query.message.chat.id, 'Well done. I remember that, but what about the ending?',
                         reply_markup=create_quite_keyboard(False))
    elif 'to' in query.data:
        if not is_user_a_creator:
            bot.answer_callback_query(query.id, 'You are not privileged to configure this.', show_alert=True)
            return
        add_ending_quite_hour(query.message.chat.id, query.data.split('_')[1])
        bot.delete_message(query.message.chat.id, query.message.message_id)
        bot.send_message(query.message.chat.id, 'Configuration is done. BYE')


@bot.message_handler(commands=['quite_hours'])
def quite_handler(message):
    if not is_creator(message.chat.id, message.from_user.id):
        return
    bot.send_message(message.chat.id, 'Let\'s configure quiet hours. Please choose the beginning hour.\n'
                                      'Please, note: only the creator could use a button.',
                     reply_markup=create_quite_keyboard(True))


@bot.message_handler(commands=['start', 'help'])
def start_handler(message):
    bot.send_message(message.chat.id, 'Hello ' + message.from_user.first_name + ', my name is ' + NAME +
                     '.\nI will ping all user in group, if you use /ping or /all\n' +
                     ('I am useless in private chat. I am group bot.' if message.chat.type == 'private' else ''))
    insert_user(message)


@bot.message_handler(content_types=["new_chat_members"])
def handler_new_member(message):
    for member in message.new_chat_members:
        insert_user(message, member)


@bot.message_handler(content_types=["left_chat_member"])
def handler_left_member(message):
    groups.update_one({'_id': message.chat.id},
                      {'$pull': {'users': message.left_chat_member.username}})


@bot.message_handler(content_types=["text"])
def handler_text(message):
    if '@' + LOGIN in message.text:
        bot.send_message(message.chat.id, '@' + message.from_user.username)
    elif NAME in message.text:
        bot.send_message(message.chat.id, 'Am I joke to you?')
    insert_user(message)


bot.polling()
