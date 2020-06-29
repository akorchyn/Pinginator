import pymongo as db

from group import Group, User


class PinginatorDb:
    def __init__(self, client: db.MongoClient = db.MongoClient()):
        self.__client = client
        self.__db = client['PinginatorDb']
        self.__groups_collection = self.__db['groups']

    def add_beginning_quiet_hour(self, group_id: int, beginning_quiet_hour: int) -> None:
        self.__groups_collection.update_one({'_id': group_id},
                                            {'$set': {'beginning_quiet_hour': beginning_quiet_hour}}, True)

    def add_ending_quiet_hour(self, group_id: int, ending_quiet_hour: int) -> None:
        self.__groups_collection.update_one({'_id': group_id},
                                            {'$set': {'ending_quiet_hour': int(ending_quiet_hour)}}, True)

    def get_group(self, group_id: int) -> Group:
        group_data = self.__groups_collection.find_one({"_id": group_id})
        quiet_hours = (group_data['beginning_quiet_hour'], group_data['ending_quiet_hour']) \
            if 'beginning_quiet_hour' in group_data and 'ending_quiet_hour' in group_data else None
        return Group([User(user['name']) for user in group_data['users']], quiet_hours)

    def insert_user(self, group_id: int, user: User):
        if user.name is not None and user.name is not "":
            self.__groups_collection.update_one({'_id': group_id},
                                                {'$addToSet': {'users': {'name': user.name}}}, True)

    def remove_user(self, group_id: int, user: User):
        self.__groups_collection.update_one({'_id': group_id},
                                            {'$pull': {'users': {'name:', user.name}}})
