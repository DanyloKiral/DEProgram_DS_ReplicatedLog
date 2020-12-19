import asyncio
import json
import os
import threading
from asyncio import Task

import grpc
from logging import Logger

from grpc.aio import AioRpcError

from shared.replication_receiver_pb2 import ReplicationResponse, ReplicationRequest
from shared import replication_receiver_pb2_grpc


class ReplicationSender:
    def __init__(self, logger):
        self.secondaries = (os.getenv('SECONDARY_ADDRESSES') or 'localhost:50051').split(',')
        self.logger: Logger = logger
        self.current_write_concern = 0

    def replicate_message_to_secondaries(self, message, message_id, write_concern):
        self.current_write_concern = write_concern
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        tasks = []
        for address in self.secondaries:
            current_task = loop.create_task(self.replicate_message(address, message, message_id))
            current_task.add_done_callback(self.get_done_callback(address, message, message_id))
            tasks.append(current_task)

        self.run_tasks_in_background(tasks, message_id)

        while self.current_write_concern > 0:
            pass

        self.logger.info(f'Completed enough for write concern. Returning')
        return

    def run_tasks_in_background(self, tasks, message_id):
        def loop_in_thread(tasks_to_run, loop):
            asyncio.set_event_loop(loop)
            loop.run_until_complete(asyncio.gather(*tasks_to_run))
            self.logger.info(f'All Async tasks completed for Message with ID = {message_id}')
            loop.close()

        current_loop = asyncio.get_event_loop()
        thread = threading.Thread(target=loop_in_thread, args=(tasks, current_loop))#
        thread.start()

    def get_done_callback(self, address, message, message_id):
        def done_callback(result: Task):
            success = result.result()
            if success:
                self.current_write_concern -= 1
            else:
                # retrying
                pass
        return done_callback

    async def replicate_message(self, address, message, message_id):
        async with grpc.aio.insecure_channel(address) as channel:
            self.logger.info(f'Replicating message with ID = {message_id} to secondary {address}')
            try:
                await channel.channel_ready()
                stub = replication_receiver_pb2_grpc.ReplicationReceiverStub(channel)
                message_json = json.dumps({'content': message, 'id': message_id})
                payload = ReplicationRequest(message=message_json)
                response: ReplicationResponse = await stub.replicate_message(payload)
                if response.success:
                    self.logger.info(f"Replication message with ID = {message_id} to {address} is successful")
                else:
                    self.logger.error(f"Replication message with ID = {message_id} to {address} failed")
                return response.success
            except AioRpcError as rpcError:
                self.logger.error(f'gRPC error. Address = {address}. Details: {rpcError}. Message with ID = {message_id}')
                return False
