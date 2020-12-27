import asyncio
import threading
from typing import List

import grpc
from logging import Logger
from grpc.aio import AioRpcError

from nodes_state import NodesState
from shared.replication_receiver_pb2 import ReplicationRequest, ReplicateMessageModel, Response, Empty
from shared import replication_receiver_pb2_grpc


class ReplicationSender:
    def __init__(self, logger, nodes_state):
        self._logger: Logger = logger
        self._nodes_state: NodesState = nodes_state
        self._message_replications_left: dict = dict()

    def replicate_message_to_secondaries(self, message, message_id, write_concern):
        self._message_replications_left[message_id] = write_concern
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        tasks = []
        for address in self._nodes_state.get_nodes_addresses():
            current_task = loop.create_task(self._replicate_message_with_retry(address, message, message_id))
            tasks.append(current_task)

        self._run_tasks_in_background(tasks, message_id)

        while self._message_replications_left[message_id] > 0:
            pass

        self._message_replications_left.pop(message_id)

        self._logger.info(f'Message #{message_id}: Completed enough for write concern. Returning')
        return

    def _run_tasks_in_background(self, tasks, message_id):
        def loop_in_thread(tasks_to_run, loop):
            asyncio.set_event_loop(loop)
            loop.run_until_complete(asyncio.gather(*tasks_to_run))
            self._logger.info(f'Message #{message_id}: All replication tasks completed')
            loop.close()

        current_loop = asyncio.get_event_loop()
        thread = threading.Thread(target=loop_in_thread, args=(tasks, current_loop))
        thread.start()

    async def _replicate_message_with_retry(self, address, message, message_id):
        data = ReplicateMessageModel(id=message_id, content=message)
        success = await self._send_message_replication(address, [data])
        retry_number = 0
        while not success:
            retry_number += 1
            await asyncio.sleep(((retry_number // 5) + 1) * 3)
            self._logger.info(f'Message #{message_id}: Retry #{retry_number} to {address}')
            success = await self._send_message_replication(address, [data])
        self._update_replications_left_for_message(message_id)
        # if success:
        #     self.update_replications_left_for_message(message_id)
        #     return success
        # self.address_messages_to_retry[address].append(data)
        # success = await self.retry(address)
        return success

    # async def retry(self, address):
    #     success = False
    #     while not success:
    #         await asyncio.sleep(self.address_retry_delay[address])
    #         if len(self.address_messages_to_retry[address]) == 0:
    #             return False
    #         self.address_retry_delay[address] *= 1.2
    #         self.logger.info(f'Retry to {address}')
    #
    #         data_to_retry = self.address_messages_to_retry.pop(address)
    #         success = await self.send_message_replication(address, data_to_retry)
    #         if not success:
    #             self.address_messages_to_retry[address].extend(data_to_retry)
    #
    #     for record in data_to_retry:
    #         self.update_replications_left_for_message(record.get('id'))
    #     self.address_retry_delay.pop(address)
    #     return True

    async def _send_message_replication(self, address, messages: List[ReplicateMessageModel]):
        message_ids = ', '.join([str(m.id) for m in messages])
        self._logger.info(f'Messages #{message_ids}: Replicating to secondary {address}')
        async with grpc.aio.insecure_channel(address) as channel:
            try:
                stub = replication_receiver_pb2_grpc.ReplicationReceiverStub(channel)
                payload = ReplicationRequest(messages=messages)
                response: Response = await stub.replicate_message(payload)
                if response.success:
                    self._logger.info(f"Messages #{message_ids}: Replication to {address} is successful")
                else:
                    self._logger.error(f"Messages #{message_ids}: Replication to {address} failed")
                return response.success
            except AioRpcError as rpcError:
                self._logger.error(f'gRPC error. Address = {address}. Details: {rpcError}. Messages #{message_ids}')
                return False

    def _update_replications_left_for_message(self, message_id):
        if message_id in self._message_replications_left:
            self._message_replications_left[message_id] -= 1
