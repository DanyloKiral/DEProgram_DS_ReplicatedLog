import asyncio
import threading
from asyncio import AbstractEventLoop
from collections import defaultdict
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
        self._address_channels: dict = dict()
        self._address_messages_to_retry: dict = defaultdict(lambda: [])
        self.loop = asyncio.new_event_loop()
        self._run_event_loop_in_another_thread()

    def replicate_message_to_secondaries(self, message, message_id, write_concern):
        self._message_replications_left[message_id] = write_concern

        for address in self._nodes_state.get_nodes_addresses():
            asyncio.run_coroutine_threadsafe(self._replicate_message(address, message, message_id), self.loop)

        while self._message_replications_left[message_id] > 0:
            pass

        self._message_replications_left.pop(message_id)

        self._logger.info(f'Message #{message_id}: Completed enough for write concern. Returning')
        return

    def trigger_retry_if_needed(self, address):
        messages_to_retry = self._pop_messages_for_retry_if_exist(address)
        if len(messages_to_retry) > 0:
            message_ids = ', '.join([str(m.id) for m in messages_to_retry])
            self._logger.info(f'Retrying messages = {message_ids} for {address}')
            asyncio.run_coroutine_threadsafe(self._send_message_replication(address, messages_to_retry), self.loop)

    async def _replicate_message(self, address, message, message_id):
        message_model = ReplicateMessageModel(id=message_id, content=message)
        data_to_retry = self._pop_messages_for_retry_if_exist(address)
        data = [*data_to_retry, message_model]
        success = await self._send_message_replication(address, data)
        return success

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
        return success

    async def _send_message_replication(self, address, messages: List[ReplicateMessageModel]):
        message_ids = ', '.join([str(m.id) for m in messages])
        self._logger.info(f'Messages #{message_ids}: Replicating to secondary {address}')
        channel = self._get_channel_for_address(address)
        success = False
        try:
            stub = replication_receiver_pb2_grpc.ReplicationReceiverStub(channel)
            payload = ReplicationRequest(messages=messages)
            response: Response = await stub.replicate_message(payload)
            success = response.success
            if success:
                self._logger.info(f"Messages #{message_ids}: Replication to {address} is successful")
            else:
                self._logger.error(f"Messages #{message_ids}: Replication to {address} failed")
        except AioRpcError as rpcError:
            code = rpcError.code() if hasattr(rpcError, 'code') else None
            self._logger.error(f'gRPC error. Address = {address}. Status: {code}. Messages #{message_ids}')
            success = False
        finally:
            if success:
                for message in messages:
                    self._update_replications_left_for_message(message.id)
            else:
                self._address_messages_to_retry[address].extend(messages)
            return success

    def _run_event_loop_in_another_thread(self):
        def run_event_loop_in_thread(loop: AbstractEventLoop):
            asyncio.set_event_loop(loop)
            loop.run_forever()
        thread = threading.Thread(target=run_event_loop_in_thread, args=(self.loop,))
        thread.start()

    def _update_replications_left_for_message(self, message_id):
        if message_id in self._message_replications_left:
            self._message_replications_left[message_id] -= 1

    def _get_channel_for_address(self, address):
        channel = self._address_channels.get(address, grpc.aio.insecure_channel(address))
        self._address_channels[address] = channel
        return channel

    def _pop_messages_for_retry_if_exist(self, address):
        if address in self._address_messages_to_retry:
            return self._address_messages_to_retry.pop(address)
        return []
