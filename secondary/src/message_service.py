from collections import OrderedDict


class MessageService:
    def __init__(self):
        self.data = OrderedDict()
        self.pending_data = dict()
        self.last_inserted_id = -1

    def append(self, item, item_id):
        # deduplication
        if item_id > self.last_inserted_id and item_id not in self.pending_data:
            # new item id is a next int
            if item_id == self.last_inserted_id + 1:
                self.__insert_to_data(item_id, item)
                next_item_id = item_id + 1
                while next_item_id in self.pending_data:
                    data = self.pending_data.pop(next_item_id)
                    self.__insert_to_data(next_item_id, data)
                    next_item_id += 1
            else:
                self.pending_data[item_id] = item
            return True
        return False

    def get(self):
        return list(self.data.values())

    def __insert_to_data(self, item_id, item):
        self.data[item_id] = item
        self.last_inserted_id = item_id
