import asyncio
import os
import threading
from asyncio import Task

import grpc
from logging import Logger

from grpc.aio import AioRpcError

from shared.errors import ReplicationNodesError
from shared.replication_receiver_pb2 import ReplicationResponse, ReplicationRequest
from shared import replication_receiver_pb2_grpc


class ReplicationSender:
    def __init__(self, logger):
        self.secondaries = (os.getenv('SECONDARY_ADDRESSES') or 'localhost:50051').split(',')
        self.logger: Logger = logger

    def replicate_message_to_secondaries(self, message, write_concern):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        tasks = []
        for address in self.secondaries:
            current_task = loop.create_task(self.replicate_message(address, message))
            current_task.add_done_callback(self.get_done_callback(address, message))
            tasks.append(current_task)

        unfinished = tasks
        confirmations_before_success = write_concern
        while len(unfinished) >= confirmations_before_success > 0:
            asyncio.set_event_loop(loop)
            finished, unfinished = loop.run_until_complete(
                asyncio.wait(unfinished, return_when=asyncio.FIRST_COMPLETED))

            for task in finished:
                confirmation = task.result()
                if confirmation:
                    confirmations_before_success -= 1
            self.logger.info(f'Sync task completed. Confirmations_before_success = {confirmations_before_success}')

        if confirmations_before_success > 0:
            raise ReplicationNodesError()

        if len(unfinished) > 0:
            self.logger.info(f'Finishing Async tasks. Count = {len(unfinished)}')
            self.run_tasks_in_background(unfinished)
        else:
            self.logger.info(f'No Async tasks to finish')
            loop.close()

        self.logger.info(f'All Sync tasks completed. Returning')
        return

    def run_tasks_in_background(self, tasks):
        def loop_in_thread(tasks_to_run, loop):
            asyncio.set_event_loop(loop)
            loop.run_until_complete(asyncio.gather(*tasks_to_run))
            self.logger.info('All Async tasks completed')
            loop.close()

        current_loop = asyncio.get_event_loop()
        thread = threading.Thread(target=loop_in_thread, args=(tasks, current_loop))
        self.logger.info(f'Running Async tasks in another thread. Tasks count = {len(tasks)}')
        thread.start()

    def get_done_callback(self, address, message):
        def done_callback(result: Task):
            success = result.result()
            if success:
                self.logger.info(f'Task finished successfully!. Address = {address}')
            else:
                self.logger.error(f'Task failed!. Address = {address}; Retry to be implemented...')
        return done_callback

    async def replicate_message(self, address, message):
        async with grpc.aio.insecure_channel(address) as channel:
            self.logger.info(f'Replicating message to secondary {address}')
            try:
                stub = replication_receiver_pb2_grpc.ReplicationReceiverStub(channel)
                response: ReplicationResponse = await stub.replicate_message(ReplicationRequest(message=message))
                if response.success:
                    self.logger.info(f"Replication to {address} is successful")
                else:
                    self.logger.error(f"Replication to {address} failed")
                return response.success
            except AioRpcError as rpcError:
                self.logger.error(f'gRPC error. Address = {address}. Details: {rpcError}')
                return False
