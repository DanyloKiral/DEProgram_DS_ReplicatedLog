import asyncio
import threading
from logging import Logger

import grpc
from grpc.aio import AioRpcError

from nodes_state import NodesState
from replication_sender import ReplicationSender
from shared import replication_receiver_pb2_grpc
from shared.replication_receiver_pb2 import Response, Empty


class HeartbeatService:
    def __init__(self, logger: Logger, nodes_state: NodesState, replication_sender):
        self._logger: Logger = logger
        self._nodes_state: NodesState = nodes_state
        self._replication_sender: ReplicationSender = replication_sender
        self._heartbeat_interval_sec = 5

    def schedule_heartbeat_checks(self):
        def loop_in_thread(task_to_run, loop):
            asyncio.set_event_loop(loop)
            loop.run_until_complete(task_to_run)
            loop.close()

        for address in self._nodes_state.get_nodes_addresses():
            current_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(current_loop)
            task = current_loop.create_task(self._run_heartbeat_check(address))
            thread = threading.Thread(target=loop_in_thread, args=(task, current_loop))  #
            thread.start()

    async def _run_heartbeat_check(self, address):
        async with grpc.aio.insecure_channel(address) as channel:
            await channel.channel_ready()
            stub = replication_receiver_pb2_grpc.ReplicationReceiverStub(channel)
            while True:
                self._logger.info(f'Heartbeat to {address}: sending')
                success = False
                try:
                    response: Response = await stub.heartbeat(Empty())
                    success = response.success
                    if success:
                        self._logger.info(f'Heartbeat to {address}: success')
                    else:
                        self._logger.info(f'Heartbeat to {address}: failed')
                except AioRpcError as rpcError:
                    self._logger.info(f'Heartbeat to {address}: failed due to grpc error')
                finally:
                    self._nodes_state.set_node_status(address, success)
                    if success:
                        # trigger retry if needed
                        pass
                    await asyncio.sleep(self._heartbeat_interval_sec)
