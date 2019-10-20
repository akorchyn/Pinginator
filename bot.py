import telebot
import pymongo
import os

if 'BOT_TOKEN' not in os.environ:
    print("Please set env variable: BOT_TOKEN")
    exit(0)

TOKEN = os.environ['BOT_TOKEN']
LOGIN = os.environ.get('BOT_LOGIN', "pinginatorbot")
NAME = os.environ.get('BOT_NAME', "Pinginator")
client = pymongo.MongoClient()
groups = client.botDb
bot = telebot.TeleBot(TOKEN)


def insert_user(message, user=None):
    user = message.from_user if user is None else user
    if message.chat.type != 'private' and not user.is_bot:
        groups[str(message.chat.id)].update_one({'name': user.username},
                                                {'$set': {'name': user.username}}, True)


@bot.message_handler(commands=['ping', 'all'])
def text_handler(message):
    chat_id = message.chat.id
    is_private = message.chat.type == 'private'
    if is_private:
        bot.send_message(chat_id, 'I AM A GROUP BOT :C')
    else:
        text = ''
        users = groups[str(message.chat.id)].find({})
        for user in users:
            if user['name'] != message.from_user.username:
                text += '@' + user['name'] + ' '
        if len(text) > 0:
            bot.send_message(message.chat.id, text)
    insert_user(message)


@bot.message_handler(commands=['start', 'help'])
def start_handler(message):
    bot.send_message(message.chat.id, 'Hello ' + message.from_user.first_name + ', my name is ' + NAME + '.\n'
                                      'I will ping all user in group, if you use /ping or /all\n' +
                                      ('I am useless in private chat. I am group bot.' if message.chat.type == 'private' else ''))
    insert_user(message)


@bot.message_handler(content_types=["new_chat_members"])
def handler_new_member(message):
    insert_user(message, message.new_chat_member)


@bot.message_handler(content_types=["left_chat_member"])
def handler_left_member(message):
    groups[str(message.chat.id)].delete_many({'name': message.left_chat_member.username})


@bot.message_handler(content_types=["text"])
def handler_text(message):
    if '@' + LOGIN in message.text:
        bot.send_message(message.chat.id, '@' + message.from_user.username)
    elif NAME in message.text:
        bot.send_message(message.chat.id, 'Am i joke to you?')
    insert_user(message)


bot.polling()

