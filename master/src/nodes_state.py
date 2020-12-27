import os
from collections import defaultdict


class NodesState:
    def __init__(self):
        self._secondaries = (os.getenv('SECONDARY_ADDRESSES') or 'localhost:50051').split(',')
        self._nodes_messages_to_retry: dict = defaultdict(lambda: [])
        self._node_statuses: dict = dict()

    def get_nodes_addresses(self):
        return self._secondaries

    def set_node_status(self, address, status):
        self._node_statuses[address] = status

    def get_node_status(self, address):
        return self._node_statuses[address]

    def get_node_statuses(self):
        return self._node_statuses

    def any_node_messages_to_retry(self, address):
        return len(self._nodes_messages_to_retry[address]) > 0

    def pop_node_messages_to_retry(self, address):
        return self._nodes_messages_to_retry.pop(address)

    def append_node_message_to_retry(self, address, message):
        self._nodes_messages_to_retry[address].append(message)

