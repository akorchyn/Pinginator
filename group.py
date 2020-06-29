from datetime import datetime, time


class User:
    name = ""

    def __init__(self, username: str):
        self.name = username


class Group:
    def __init__(self, users: [User], quiet_hours: (int, int) = None):
        self._quiet_hours = quiet_hours
        self._users = users

    def get_users(self) -> [str]:
        return self._users

    def is_quiet_hours_enabled(self, message_time: datetime) -> bool:
        if self._quiet_hours is None:
            return False
        begin_hour, end_hour = [time(x, 0) for x in self._quiet_hours]
        check_time = message_time.time()
        if begin_hour < end_hour:
            return begin_hour <= check_time <= end_hour
        else:  # crosses midnight
            return check_time >= begin_hour or check_time <= end_hour
