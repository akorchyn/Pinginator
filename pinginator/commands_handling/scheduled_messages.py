import calendar
import datetime

from telegram import Update, InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler, JobQueue, Job
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

import pinginator.helpers.helpers as helpers
from pinginator.common.db import PinginatorDb
from pinginator.common.group import ScheduledMessage, Group
from pinginator.helpers.inline_keyboard_paginator import InlineKeyboardPaginator
from pinginator.helpers.user_loading import prepare_ping_message, load_users_info_from_group

jobs = {}
separator = "%id.*"
prefix_to_date = "schedtodate"
prefix_to_unschedule = 'unschedule'
prefix_to_ping = "schedtoping"
prefix_to_tmp = "tmp"


def insert_job_to_jobs(chat_id, job):
    if chat_id in jobs:
        jobs[chat_id].append(job)
    else:
        jobs[chat_id] = [job]


def create_scheduled_message_callback(chat_id: int, message: ScheduledMessage):
    def callback(context: CallbackContext):
        if message.should_ping:
            db: PinginatorDb = context.bot_data['db']
            group = db.get_group(chat_id)
            users = load_users_info_from_group(context.bot, group, db)
            text = prepare_ping_message(users, [])
            context.bot.send_message(chat_id, text if len(text) > 0 else "Haven't parse anyone:C",
                                     parse_mode='markdown')
        context.bot.send_message(chat_id, message.message)

    return callback


def add_one_month(orig_date) -> datetime:
    # advance year and month by one month
    new_year = orig_date.year
    new_month = orig_date.month + 1
    # note: in datetime.date, months go from 1 to 12
    if new_month > 12:
        new_year += 1
        new_month -= 12

    last_day_of_month = calendar.monthrange(new_year, new_month)[1]
    new_day = min(orig_date.day, last_day_of_month)

    return orig_date.replace(year=new_year, month=new_month, day=new_day)


def run_job(queue: JobQueue, message: ScheduledMessage, chat_id: int):
    if message.period == 'daily':
        insert_job_to_jobs(chat_id, queue.run_daily(create_scheduled_message_callback(chat_id, message),
                                                    message.start_day.time()))
    elif message.period == 'monthly':
        insert_job_to_jobs(chat_id, queue.run_monthly(create_scheduled_message_callback(chat_id, message),
                                                      message.start_day.time(), message.start_day.date().day,
                                                      day_is_strict=False))
    elif message.period == 'once':
        insert_job_to_jobs(chat_id, queue.run_once(create_scheduled_message_callback(chat_id, message),
                                                   message.start_day))
    else:
        raise RuntimeError("Something strange happen")


def adjust_message(msg: ScheduledMessage, current_date: datetime):
    while current_date > msg.start_day:
        msg.start_day = add_one_month(msg.start_day)
    return msg


def load_jobs(queue: JobQueue, db: PinginatorDb):
    groups = db.get_all_groups()
    date = datetime.datetime.now()
    for group in groups:
        for (index, message) in enumerate(group.scheduled_messages):
            if date > message.start_day:
                db.remove_scheduled_message(group.id, index)
                if message.period != 'once':
                    message = adjust_message(message, date)
                    db.add_scheduled_message(group.id, message)
                else:
                    # we shouldn't run job that is finished
                    continue
            run_job(queue, message, group.id)


@helpers.creator_only_query
@helpers.insert_user
def query_to_result(update: Update, context: CallbackContext):
    query: CallbackQuery = update.callback_query
    date, key, step = DetailedTelegramCalendar().process(query.data)
    if not date and key:
        query.edit_message_text(f"Please, select {LSTEP[step]}", reply_markup=key)
        return
    if date is None:
        return
    datetime_now = datetime.datetime.now()
    if date < datetime_now.date():
        context.bot.answer_callback_query(query.id, "Start date cannot be in the past.", show_alert=True)
        return
    elif date > add_one_month(datetime_now).date():
        context.bot.answer_callback_query(query.id, "Start date should be more than one month from now.",
                                          show_alert=True)
        return
    period = context.chat_data['period']
    msg = context.chat_data['scheduled_msg']
    should_ping = context.chat_data['ping']
    message = ScheduledMessage(msg, period, datetime.datetime.combine(date, update.effective_message.date.time()),
                               should_ping)
    context.bot_data['db'].add_scheduled_message(update.effective_chat.id, message)
    run_job(context.job_queue, message, update.effective_chat.id)
    query.edit_message_text("Done. Message successfully scheduled")


@helpers.creator_only_query
@helpers.insert_user
def query_to_date(update: Update, context: CallbackContext):
    query: CallbackQuery = update.callback_query
    should_ping = query.data[len(prefix_to_date):]
    context.chat_data['ping'] = should_ping == "True"
    calendar, step = DetailedTelegramCalendar().build()
    query.edit_message_text("Please, select a " + LSTEP[step], reply_markup=calendar)


@helpers.creator_only_handle
@helpers.insert_user
def query_to_ping(update: Update, context: CallbackContext):
    query: CallbackQuery = update.callback_query
    period = query.data[len(prefix_to_ping):]
    context.chat_data['period'] = period

    keyboard = [[InlineKeyboardButton("Yes", callback_data=prefix_to_date + 'True'),
                 InlineKeyboardButton("No", callback_data=prefix_to_date + 'False')]]
    query.edit_message_text('Ok, I got it. Should I ping?', reply_markup=InlineKeyboardMarkup(keyboard))


@helpers.creator_only_query
@helpers.insert_user
def query_to_unschedule(update: Update, context: CallbackContext):
    query: CallbackQuery = update.callback_query
    db = context.bot_data['db']
    group = db.get_group(update.effective_chat.id)
    indexes = [str(x) for x in range(len(group.scheduled_messages))]
    keyboard_paginator = InlineKeyboardPaginator(indexes, 4, prefix_to_unschedule)
    is_data, data = keyboard_paginator.get_content(query.data)
    if is_data:
        index = int(data)
        db.remove_scheduled_message(update.effective_chat.id, index)
        group_jobs = jobs[update.effective_chat.id]
        active_job: Job = group_jobs.pop(index)
        active_job.schedule_removal()
        query.edit_message_text("Done. Message successfully unscheduled")
    else:
        query.edit_message_reply_markup(reply_markup=keyboard_paginator.get(int(data)))


@helpers.creator_only_handle
@helpers.insert_user
def remove_scheduled_message(update: Update, context: CallbackContext):
    db = context.bot_data['db']
    group: Group = db.get_group(update.effective_chat.id)
    if not group.scheduled_messages:
        context.bot.send_message(update.effective_chat.id, 'Group hasn\'t any scheduled messages')
        return
    prepared_message = 'Currently, group has these scheduled messages:\n'
    for (index, message) in enumerate(group.scheduled_messages):
        prepared_message += str(index) + '. ' + message.message
        if message.period == 'daily':
            prepared_message += '. [Daily at '
        elif message.period == 'monthly':
            prepared_message += '. [Each ' + str(message.start_day.date().day) + ' day of the month at '
        elif message.period == 'once':
            prepared_message += '. [Planned for ' + str(message.start_day.date()) + ' at '
        prepared_message += (message.start_day.strftime('%H:%M') +
                             (". Pings everyone]\n" if message.should_ping else ']\n'))
    indexes = [str(x) for x in range(len(group.scheduled_messages))]
    keyboard_paginator = InlineKeyboardPaginator(indexes, 4, prefix_to_unschedule)
    context.bot.send_message(update.effective_chat.id, prepared_message, reply_markup=keyboard_paginator.get(0))


def query_to_tmp(update: Update, context: CallbackContext):
    query: CallbackQuery = update.callback_query
    data = query.data
    array = data.split("%")
    index = int(array[2])
    should_ping = array[1] == "True"

    db = context.bot_data['db']
    group = db.get_group(update.effective_chat.id)
    message = group.scheduled_messages[index]
    db.remove_scheduled_message(update.effective_chat.id, index)
    group_jobs = jobs[update.effective_chat.id]
    active_job: Job = group_jobs.pop(index)
    active_job.schedule_removal()

    message.should_ping = should_ping
    context.bot_data['db'].add_scheduled_message(update.effective_chat.id, message)
    run_job(context.job_queue, message, update.effective_chat.id)

    query.edit_message_text("Thank you")


def temporary_schedule_migration(bot, db: PinginatorDb):
    groups = db.get_all_groups()
    for group in groups:
        for (index, message) in enumerate(group.scheduled_messages):
            prepared_message = message.message
            if message.period == 'daily':
                prepared_message += '. [Daily at '
            elif message.period == 'monthly':
                prepared_message += '. [Each ' + str(message.start_day.date().day) + ' day of the month at '
            elif message.period == 'once':
                prepared_message += '. [Planned for ' + str(message.start_day.date()) + ' at '
            prepared_message += (message.start_day.strftime('%H:%M') +
                                 (". Pings everyone]\n" if message.should_ping else ']\n'))

            keyboard = [[InlineKeyboardButton("Yes", callback_data=prefix_to_tmp + '%True%' + str(index)),
                         InlineKeyboardButton("No", callback_data=prefix_to_tmp + '%False%' + str(index))]]
            try:
                bot.send_message(group.id, "Message: " + prepared_message + "Should I ping?",
                                 reply_markup=InlineKeyboardMarkup(keyboard))
            except:
                db.remove_group(group.id)


@helpers.creator_only_handle
@helpers.insert_user
def schedule_message(update: Update, context: CallbackContext):
    msg_text = "Please, provide text of the scheduled message:\n"
    msg_id = context.bot.send_message(update.effective_chat.id, msg_text).message_id

    def input_callback(message: str):
        keyboard = [[InlineKeyboardButton("Once", callback_data=prefix_to_ping + 'once'),
                     InlineKeyboardButton("Daily", callback_data=prefix_to_ping + 'daily'),
                     InlineKeyboardButton("Monthly", callback_data=prefix_to_ping + 'monthly')]]
        context.chat_data['scheduled_msg'] = message
        context.bot.edit_message_text('Ok, I got it. The message is `' + message + '`. How often should I ping?',
                                      parse_mode="Markdown", message_id=msg_id, chat_id=update.effective_chat.id,
                                      reply_markup=InlineKeyboardMarkup(keyboard))

    context.bot_data['waiting_input'].append((update.effective_chat.id, update.effective_user.id, input_callback))


SCHEDULED_MESSAGE_COMMANDS = [CommandHandler("schedule", schedule_message, pass_args=True),
                              CallbackQueryHandler(query_to_date, pattern="^" + prefix_to_date + ".*"),
                              CallbackQueryHandler(query_to_ping, pattern="^" + prefix_to_ping + ".*"),
                              CallbackQueryHandler(query_to_tmp, pattern="^" + prefix_to_tmp + ".*"),
                              CommandHandler("unschedule", remove_scheduled_message),
                              CallbackQueryHandler(query_to_unschedule, pattern='^' + prefix_to_unschedule + '.*'),
                              CallbackQueryHandler(query_to_result)]  # should be the last
