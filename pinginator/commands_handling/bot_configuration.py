from telegram import Update, CallbackQuery
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler

import pinginator.helpers.helpers as helpers
from pinginator.helpers.inline_keyboard_paginator import InlineKeyboardPaginator

TIME_RANGE = [str(x) for x in range(24)]

from_inline_keyboard_paginator = InlineKeyboardPaginator(TIME_RANGE, 4, "from")
to_inline_keyboard_paginator = InlineKeyboardPaginator(TIME_RANGE, 4, "to")


@helpers.creator_only_query
@helpers.insert_user
def quiet_query_configuration(update: Update, context: CallbackContext):
    query: CallbackQuery = update.callback_query
    db = context.bot_data['db']
    group_id = query.message.chat.id
    is_from_keyboard = from_inline_keyboard_paginator.corresponds_to_keyboard(query.data)
    is_data, data = from_inline_keyboard_paginator.get_content(query.data) if is_from_keyboard \
        else to_inline_keyboard_paginator.get_content(query.data)

    if is_data:
        context.bot.delete_message(group_id, query.message.message_id)

        if is_from_keyboard:
            db.add_beginning_quiet_hour(group_id, int(data))
            context.bot.send_message(group_id, 'Well done. I remember that, but what about the ending?',
                                     reply_markup=to_inline_keyboard_paginator.get(0))
        else:
            db.add_ending_quiet_hour(group_id, int(data))
            context.bot.send_message(group_id, 'Configuration is done. Have a nice day')

    else:
        new_page = from_inline_keyboard_paginator.get(data) if is_from_keyboard \
            else to_inline_keyboard_paginator.get(data)
        context.bot.edit_message_reply_markup(group_id, message_id=query.message.message_id, reply_markup=new_page)


@helpers.creator_only_handle
@helpers.insert_user
def initiate_quiet_configuration(update: Update, context: CallbackContext):
    context.bot.send_message(update.effective_chat.id, 'Let\'s configure quiet hours. Please choose the beginning '
                                                       'hour.\n Please, note: only the creator could use a button.',
                             reply_markup=from_inline_keyboard_paginator.get(0))


@helpers.creator_only_handle
@helpers.insert_user
def admin_only(update: Update, context: CallbackContext):
    db = context.bot_data['db']
    new_value = db.change_admin_only_flag(update.effective_chat.id)
    context.bot.send_message(update.effective_chat.id,
                             "Done. Only the admins could use pings" if new_value else "Done. Anyone could ping. "
                                                                                       "ANARCHY!!!!")


CONFIGURATION_COMMANDS = [
    CommandHandler("admin_only", callback=admin_only),
    CommandHandler("quiet_hours", callback=initiate_quiet_configuration),
    CallbackQueryHandler(quiet_query_configuration, pattern="^((from)|(to)).*")
]
