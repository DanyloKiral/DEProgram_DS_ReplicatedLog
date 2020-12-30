import threading
from logging import Logger
from time import sleep
import grpc
from nodes_state import NodesState
from replication_sender import ReplicationSender
from shared import replication_receiver_pb2_grpc
from shared.replication_receiver_pb2 import Response, Empty


class HeartbeatService:
    def __init__(self, logger: Logger, nodes_state: NodesState, replication_sender):
        self._logger: Logger = logger
        self._nodes_state: NodesState = nodes_state
        self._replication_sender: ReplicationSender = replication_sender
        self._heartbeat_interval_sec = 10
        self._heartbeat_timeout_sec = 0.5

    def schedule_heartbeat_checks(self):
        for address in self._nodes_state.get_nodes_addresses():
            thread = threading.Thread(target=lambda: self._run_heartbeat_check(address))
            thread.start()

    def _run_heartbeat_check(self, address):
        with grpc.insecure_channel(address) as channel:
            stub = replication_receiver_pb2_grpc.ReplicationReceiverStub(channel)
            while True:
                success = False
                try:
                    #self._logger.info(f'Sending heartbeat to {address}')
                    response: Response = stub.heartbeat(Empty(), timeout=self._heartbeat_timeout_sec)
                    success = response.success
                    if not success:
                        self._logger.error(f'Heartbeat to {address}: failed')
                    else:
                        self._logger.info(f'Heartbeat to {address}: success')
                except grpc.RpcError as rpcError:
                    code = rpcError.code() if hasattr(rpcError, 'code') else None
                    self._logger.error(f'Heartbeat to {address}: failed due to grpc error. Status = {code}')
                finally:
                    self._nodes_state.set_node_status(address, success)
                    if success:
                        self._replication_sender.trigger_retry_if_needed(address)
                        pass
                    sleep(self._heartbeat_interval_sec)
