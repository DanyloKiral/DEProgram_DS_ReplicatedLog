import asyncio
import os
import grpc
from logging import Logger
from shared.replication_receiver_pb2 import ReplicationResponse, ReplicationRequest
from shared import replication_receiver_pb2_grpc


class ReplicationSender:
    def __init__(self, logger):
        self.secondaries = (os.getenv('SECONDARY_ADDRESSES') or '').split(',')
        self.logger: Logger = logger

    def replicate_message_to_secondaries(self, message):
        tasks = []
        for address in self.secondaries:
            tasks.append(self.replicate_message(address, message))

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.gather(*tasks))
        loop.close()

    async def replicate_message(self, address, message):
        async with grpc.aio.insecure_channel(address) as channel:
            self.logger.info(f'Replicating message to secondary {address}')
            stub = replication_receiver_pb2_grpc.ReplicationReceiverStub(channel)
            response: ReplicationResponse = await stub.replicate_message(ReplicationRequest(message=message))
            if response.success:
                self.logger.info(f"Replication to {address} is successful")
            else:
                self.logger.error(f"Replication to {address} failed")
