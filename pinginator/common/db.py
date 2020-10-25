from datetime import datetime

import pymongo as db

from pinginator.common.group import Group, User, ScheduledMessage


class PinginatorDb:
    def __init__(self, client: db.MongoClient = db.MongoClient(), database: str = 'PinginatorDb'):
        self.__client = client
        self.__db = client[database]
        self.__groups_collection = self.__db['groups']

    def add_beginning_quiet_hour(self, group_id: int, beginning_quiet_hour: int) -> None:
        self.__groups_collection.update_one({'_id': group_id},
                                            {'$set': {'beginning_quiet_hour': beginning_quiet_hour}}, upsert=True)

    def add_ending_quiet_hour(self, group_id: int, ending_quiet_hour: int) -> None:
        self.__groups_collection.update_one({'_id': group_id},
                                            {'$set': {'ending_quiet_hour': int(ending_quiet_hour)}}, upsert=True)

    def is_admin_only(self, group_id: int) -> bool:
        data = self.__groups_collection.find_one({'_id': group_id})
        return 'admin_only' in data and data['admin_only']

    def change_admin_only_flag(self, group_id: int):
        current_value = self.is_admin_only(group_id)
        self.__groups_collection.update_one({'_id': group_id},
                                            {'$set': {'admin_only': not current_value}}, upsert=True)
        return not current_value

    def __get_group_from_cursor(self, group_data):
        quiet_hours = (group_data['beginning_quiet_hour'], group_data['ending_quiet_hour']) \
            if 'beginning_quiet_hour' in group_data and 'ending_quiet_hour' in group_data else None
        is_admin_only = group_data['admin_only'] if 'admin_only' in group_data else False
        users = [User(user['user_id']) for user in group_data['users']]
        messages = []
        if 'scheduled_messages' in group_data:
            for msg_info in group_data['scheduled_messages']:
                if 'message' in msg_info and 'period' in msg_info and 'date' in msg_info:
                    messages.append(ScheduledMessage(msg_info['message'], msg_info['period'],
                                                     datetime.fromtimestamp(msg_info['date'])))
        return Group(group_data['_id'], users, is_admin_only, messages, quiet_hours)

    def get_group(self, group_id: int) -> Group:
        group_data = self.__groups_collection.find_one({"_id": group_id})
        if group_data is None:
            return Group(group_id)
        return self.__get_group_from_cursor(group_data)

    def insert_user(self, group_id: int, user: User):
        self.__groups_collection.update_one({'_id': group_id},
                                            {'$addToSet': {'users': {'user_id': user.id}}},
                                            upsert=True)

    def remove_user(self, group_id: int, user: User):
        self.__groups_collection.update_one({'_id': group_id},
                                            {'$pull': {'users': {'user_id': user.id}}})

    def get_all_groups(self) -> [Group]:
        return [self.__get_group_from_cursor(cursor) for cursor in self.__groups_collection.find({})]

    def remove_group(self, group_id: int):
        self.__groups_collection.remove({'_id': group_id})

    def migrate_group(self, previous_chat_id, new_chat_id):
        group = self.__groups_collection.find_one({'_id': previous_chat_id})
        group['_id'] = new_chat_id
        self.__groups_collection.insert(group)
        self.__groups_collection.remove(previous_chat_id)

    def remove_scheduled_message(self, group_id: int, message_index: int):
        self.__groups_collection.update_one({'_id': group_id},
                                            {'$unset': {'scheduled_messages.' + str(message_index): 1}})
        self.__groups_collection.update_one({'_id': group_id},
                                            {'$pull': {'scheduled_messages': None}})

    def add_scheduled_message(self, group_id: int, msg: ScheduledMessage):
        self.__groups_collection.update_one({'_id': group_id},
                                            {'$push': {'scheduled_messages': {
                                                               'message': msg.message,
                                                               'period': msg.period,
                                                               'date': msg.start_day.timestamp()}}},
                                            upsert=True)
