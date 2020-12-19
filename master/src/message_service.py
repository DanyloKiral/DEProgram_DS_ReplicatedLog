
class MessageService:
    def __init__(self):
        self.__id = 0
        self.__data_list = []

    def append(self, item):
        new_item_id = self.__id
        self.__data_list.append(item)
        self.__id += 1
        return new_item_id

    def get(self):
        return self.__data_list
