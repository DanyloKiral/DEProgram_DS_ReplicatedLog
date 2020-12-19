
class MessageService:
    def __init__(self):
        self.__data_list = []

    def append(self, item, item_id):
        self.__data_list.append(item)

    def get(self):
        return self.__data_list
