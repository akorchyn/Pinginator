import telebot
import os.path
import signal
import sys

TOKEN = ""

bot = telebot.TeleBot(TOKEN)
NAME = "pinginatorbot"
users = dict()


def signal_handler(signal, frame):
    for group in users:
        f = open(group, 'w')
        for user in users[group]:
            f.write(user + '\n')
        f.close()
    sys.exit(0)


def check_and_upload(group_id):
    if users.get(group_id) is not None:
        return
    users[group_id] = set()
    if os.path.isfile(group_id):
        f = open(group_id, 'r')
        temp = f.read().splitlines()
        for line in temp:
            users[group_id].add(line)


@bot.message_handler(commands=['ping'])
def text_handler(message):
    chat_id = message.chat.id
    is_private = message.chat.type == 'private'
    if is_private:
        bot.send_message(chat_id, 'I AM A GROUP BOT :C')
    else:
        text = ''
        check_and_upload(str(message.chat.id))
        for a in users[str(message.chat.id)]:
            if a != message.from_user.username and a != NAME:
                text += '@' + a + ' '
        if len(text) > 0:
            bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['start', 'help'])
def start_handler(message):
    bot.send_message(message.chat.id, 'Hello ' + message.from_user.first_name + ', my name is Pinginator.\n'
                                      'I will ping all user in group, if you use /ping\n' +
                                      ('I am useless in private chat. I am group bot.' if message.chat.type == 'private' else ''))


@bot.message_handler(content_types=["new_chat_members"])
def handler_new_member(message):
    key = str(message.chat.id)
    check_and_upload(key)
    users[key].add(message.new_chat_member.username)


@bot.message_handler(content_types=["left_chat_member"])
def handler_left_member(message):
    key = str(message.chat.id)
    check_and_upload(key)
    if message.left_chat_member.username not in users[key]:
        return
    users[key].remove(message.left_chat_member.username)


@bot.message_handler(content_types=["text"])
def handler_text(message):
    key = str(message.chat.id)
    check_and_upload(key)
    if '@' + NAME in message.text:
        bot.send_message(message.chat.id, '@' + message.from_user.username)
    if message.from_user.username not in users[key]:
        users[key].add(message.from_user.username)


signal.signal(signal.SIGINT, signal_handler)
bot.polling()

