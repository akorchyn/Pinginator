import pymongo as db

from group import Group, User


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

    def get_group(self, group_id: int) -> Group:
        group_data = self.__groups_collection.find_one({"_id": group_id})
        quiet_hours = (group_data['beginning_quiet_hour'], group_data['ending_quiet_hour']) \
            if 'beginning_quiet_hour' in group_data and 'ending_quiet_hour' in group_data else None
        is_admin_only = group_data['admin_only'] if 'admin_only' in group_data else False
        return Group([User(user['user_id']) for user in group_data['users']], is_admin_only, quiet_hours)

    def insert_user(self, group_id: int, user: User):
        self.__groups_collection.update_one({'_id': group_id},
                                            {'$addToSet': {'users': {'user_id': user.id}}},
                                            upsert=True)

    def remove_user(self, group_id: int, user: User):
        self.__groups_collection.update_one({'_id': group_id},
                                            {'$pull': {'users': {'user_id': user.id}}})
