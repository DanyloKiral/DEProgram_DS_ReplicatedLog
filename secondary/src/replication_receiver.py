import json
import os
import random
import time
from logging import Logger

from di_container import ServicesContainer
from shared.replication_receiver_pb2 import ReplicationRequest, ReplicationResponse
from shared import replication_receiver_pb2_grpc
from message_service import MessageService


class ReplicationReceiver(replication_receiver_pb2_grpc.ReplicationReceiverServicer):
    def __init__(self):
        self.message_service: MessageService = ServicesContainer.message_service_provider()
        self.logger: Logger = ServicesContainer.logger()

    def replicate_message(self, request: ReplicationRequest, context):
        if self.should_simulate_error():
            self.logger.error(f'Simulating error')
            return ReplicationResponse(success=False)

        messages: list[dict] = sorted(json.loads(request.message), key=lambda v: v.get('id'))
        for message in messages:
            message_content = message.get('content')
            message_id = message.get('id')
            self.logger.info(f'Received replication message from master. Message = "{message_content}"; Message ID = {message_id}')
            self.simulate_delay()
            added = self.message_service.append(message_content, message_id)
            if added:
                self.logger.info(f'Replication is successful. Message ID = {message_id}')
            else:
                self.logger.info(f'Message with ID = {message_id} was already replicated')
        return ReplicationResponse(success=True)

    def simulate_delay(self):
        delay_ms = int(os.getenv('DELAY'))
        if delay_ms < 0:
            delay_ms = random.randrange(3000, 15000, 50)
        self.logger.info(f'Simulated delay = {delay_ms}ms')
        time.sleep(delay_ms / 1000)

    @staticmethod
    def should_simulate_error():
        return random.randrange(0, 5, 1) == 0
