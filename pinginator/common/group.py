from datetime import time, datetime


class ScheduledMessage:
    def __init__(self, message: str, period: str, start_day: datetime):
        self.message = message
        self.period = period
        self.start_day = start_day


class User:
    def __init__(self, user_id: int):
        self.id = user_id


class UserInfo:
    def __init__(self, user_id: id, login: str, first_name: str, last_name: str):
        self.user_id = user_id
        self.login = login
        self.first_name = first_name
        self.last_name = last_name


class Group:
    def __init__(self, chat_id: int, users: [User] = [], admin_only: bool = False, messages: [ScheduledMessage] = None,
                 quiet_hours: (int, int) = None):
        if messages is None:
            messages = []
        self.id = chat_id
        self.quiet_hours = quiet_hours
        self.users = users
        self.is_admin_only = admin_only
        self.scheduled_messages = messages

    def is_quiet_hours_enabled(self, message_time: datetime) -> bool:
        if self.quiet_hours is None:
            return False
        begin_hour, end_hour = [time(x, 0) for x in self.quiet_hours]
        check_time = message_time.time()
        if begin_hour < end_hour:
            return begin_hour <= check_time <= end_hour
        else:  # crosses midnight
            return check_time >= begin_hour or check_time <= end_hour
