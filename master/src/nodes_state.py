import os
from collections import defaultdict
import constants


class NodesState:
    def __init__(self):
        self._secondaries = (os.getenv('SECONDARY_ADDRESSES') or 'localhost:50051').split(',')
        self._nodes_messages_to_retry: dict = defaultdict(lambda: [])
        self._node_statuses: dict = defaultdict(lambda: constants.NODE_HEALTH_UNHEALTHY)

    def get_nodes_addresses(self):
        return self._secondaries

    def set_node_status(self, address, heartbeat_success):
        current_status = self._node_statuses[address]

        if heartbeat_success:
            new_status = constants.NODE_HEALTH_HEALTHY
        elif current_status == constants.NODE_HEALTH_HEALTHY:
            new_status = constants.NODE_HEALTH_SUSPECTED
        else:
            new_status = constants.NODE_HEALTH_UNHEALTHY

        self._node_statuses[address] = new_status

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

    def number_of_nodes(self):
        return len(self._secondaries) + 1

    def number_of_unavailable_nodes(self):
        return len([status for status in self._node_statuses.values() if status != constants.NODE_HEALTH_HEALTHY])

    def has_master_quorum(self):
        return (self.number_of_nodes() // 2) >= self.number_of_unavailable_nodes()

