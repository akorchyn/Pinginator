from datetime import time

from telegram import Update, User, TelegramError
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler

import pinginator.helpers.helpers as helpers
from pinginator.common.db import PinginatorDb
from pinginator.common.exceptions import AccessDenied


def private_message_text_handler(update: Update, context: CallbackContext):
    context.bot.send_message(update.effective_chat.id, 'Group only feature')


@helpers.insert_user
def text_handler(update: Update, context: CallbackContext):
    if '@' + context.bot.username in update.effective_message.text:
        context.bot.send_message(update.effective_chat.id, '@' + update.effective_user.username)
    elif context.bot.first_name in update.effective_message.text:
        context.bot.send_message(update.effective_chat.id, 'Am I joke to you?')


@helpers.insert_user
def ping(update: Update, context: CallbackContext):
    db: PinginatorDb = context.bot_data['db']
    group_id = update.effective_chat.id
    group = db.get_group(group_id)
    if group.is_admin_only and not helpers.is_administrator(context.bot, group_id, update.effective_user.id):
        raise AccessDenied()
    elif group.is_quiet_hours_enabled(update.message.date):
        context.bot.send_message(group_id, 'Quiet hours policy is active now. I can\'t send a message. '
                                           'Please, use after ' + str(time(group.quiet_hours[1], 0)) + ', '
                                                                                                       'or change the policy if you have rights.')
        return
    text = ''
    for user in group.users:
        try:
            if user.id == update.effective_user.id:
                continue
            user_info: User = context.bot.get_chat_member(group_id, user.id).user
            if user_info is not None:
                text += '[{}](tg://user?id={}), '.format(
                    user_info.first_name if user_info.username is None else '@' + user_info.username, user_info.id)
        except TelegramError:
            """ The user is no more in the group and we didn't remove it for some reason
                (maybe, the bot was disabled when the user left)
            """
            db.remove_user(group_id, user)
    if len(text) > 0:
        context.bot.send_message(group_id, text[:-2], parse_mode='markdown')
    else:
        context.bot.send_message(group_id, "Sorry, I haven't parse anyone except you. Try again later.\n")


@helpers.insert_user
def start_handler(update: Update, context: CallbackContext):
    db: PinginatorDb = context.bot_data['db']
    message_str = 'Hi ' + update.effective_user.first_name + ',\n\n' \
                                                             'I am ' + context.bot.first_name + \
                  ', a bot which would help you to notify all people in a group.\n\n' \
                  'Use /ping or /all in a chat to take attention\n\n' \
                  'Also, you could configure me:\n' \
                  'Use /quiet_hours to set a time range in which I won\'t ping anyone\n' \
                  'Write /admin_only to introduce a dictatorship of administrators into your chat.\n' \
                  'You could schedule reapeted messages by /schedule and /unschedule commands\n'

    if update.effective_chat.type == 'group':
        group = db.get_group(group_id=update.effective_chat.id)
        message_str += '\nHere is the current configuration:\n' \
                       'May any user pings all? --> ' + str(not group.is_admin_only) + '\n' \
                                                                                       'Were quiet hours enabled? --> ' + \
                       str(False if group.quiet_hours is None else 'Yes, It is on from {} to {}'.format(
                           group.quiet_hours[0], group.quiet_hours[1]))

    context.bot.send_message(update.effective_chat.id, message_str)


DISPATCHER_HANDLERS = [CommandHandler(['start', 'help'], start_handler),
                       MessageHandler(Filters.command(['ping', 'all', 'quiet_hours', 'admin_only']) & Filters.private,
                                      private_message_text_handler),
                       CommandHandler(['all', 'ping'], ping, filters=Filters.group),
                       MessageHandler(Filters.text & (~Filters.command), text_handler)
                       ]
