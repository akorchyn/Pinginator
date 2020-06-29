from datetime import datetime, time


class User:
    def __init__(self, user_id: int):
        self.id = user_id


class Group:
    def __init__(self, users: [User], admin_only, quiet_hours: (int, int) = None):
        self.quiet_hours = quiet_hours
        self.users = users
        self.is_admin_only = admin_only

    def is_quiet_hours_enabled(self, message_time: datetime) -> bool:
        if self.quiet_hours is None:
            return False
        begin_hour, end_hour = [time(x, 0) for x in self.quiet_hours]
        check_time = message_time.time()
        if begin_hour < end_hour:
            return begin_hour <= check_time <= end_hour
        else:  # crosses midnight
            return check_time >= begin_hour or check_time <= end_hour
