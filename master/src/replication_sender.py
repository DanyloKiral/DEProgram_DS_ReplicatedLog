import asyncio
import json
import os
import threading
from collections import defaultdict
from typing import List

import grpc
from logging import Logger
from grpc.aio import AioRpcError
from shared.replication_receiver_pb2 import ReplicationResponse, ReplicationRequest
from shared import replication_receiver_pb2_grpc


class ReplicationSender:
    def __init__(self, logger):
        self.secondaries = (os.getenv('SECONDARY_ADDRESSES') or 'localhost:50051').split(',')
        self.logger: Logger = logger
        self.message_replications_left: dict = dict()
        self.address_messages_to_retry: dict = defaultdict(lambda: [])
        self.address_retry_delay: dict = defaultdict(lambda: 5)

    def replicate_message_to_secondaries(self, message, message_id, write_concern):
        self.message_replications_left[message_id] = write_concern
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        tasks = []
        for address in self.secondaries:
            current_task = loop.create_task(self.replicate_message_with_retry(address, message, message_id))
            tasks.append(current_task)

        self.run_tasks_in_background(tasks, message_id)

        while self.message_replications_left[message_id] > 0:
            pass

        self.message_replications_left.pop(message_id)

        self.logger.info(f'Message #{message_id}: Completed enough for write concern. Returning')
        return

    def run_tasks_in_background(self, tasks, message_id):
        def loop_in_thread(tasks_to_run, loop):
            asyncio.set_event_loop(loop)
            loop.run_until_complete(asyncio.gather(*tasks_to_run))
            self.logger.info(f'Message #{message_id}: All replication tasks completed')
            loop.close()

        current_loop = asyncio.get_event_loop()
        thread = threading.Thread(target=loop_in_thread, args=(tasks, current_loop))#
        thread.start()

    async def replicate_message_with_retry(self, address, message, message_id):
        data = {'id': message_id, 'content': message}
        success = await self.send_message_replication(address, [data])
        if success:
            self.update_replications_left_for_message(message_id)
            return success
        self.address_messages_to_retry[address].append(data)
        success = await self.retry(address)
        return success

    async def retry(self, address):
        success = False
        while not success:
            await asyncio.sleep(self.address_retry_delay[address])
            if len(self.address_messages_to_retry[address]) == 0:
                return False
            #self.address_retry_delay[address] *= 1.5
            self.logger.info(f'Retry to {address}')

            data_to_retry = self.address_messages_to_retry.pop(address)
            success = await self.send_message_replication(address, data_to_retry)
            if not success:
                self.address_messages_to_retry[address].extend(data_to_retry)

        for record in data_to_retry:
            self.update_replications_left_for_message(record.get('id'))
        self.address_retry_delay.pop(address)
        return True

    async def send_message_replication(self, address, data: List[dict]):
        message_ids = ', '.join([str(m.get('id')) for m in data])
        async with grpc.aio.insecure_channel(address) as channel:
            self.logger.info(f'Messages #{message_ids}: Replicating to secondary {address}')
            try:
                stub = replication_receiver_pb2_grpc.ReplicationReceiverStub(channel)
                message_json = json.dumps(data)
                payload = ReplicationRequest(message=message_json)
                response: ReplicationResponse = await stub.replicate_message(payload)
                if response.success:
                    self.logger.info(f"Messages #{message_ids}: Replication to {address} is successful")
                else:
                    self.logger.error(f"Messages #{message_ids}: Replication to {address} failed")
                return response.success
            except AioRpcError as rpcError:
                self.logger.error(f'gRPC error. Address = {address}. Details: {rpcError}. Messages #{message_ids}')
                return False

    def update_replications_left_for_message(self, message_id):
        if message_id in self.message_replications_left:
            self.message_replications_left[message_id] -= 1
