import grpc

from shared.replication_receiver_pb2 import ReplicationResponse, ReplicationRequest
from shared import replication_receiver_pb2_grpc


class ReplicationSender:
    def __init__(self):
        self.secondaries = ["secondary-node1:50051", "secondary-node2:50051"]

    def replicate_message_to_secondaries(self, message):
        for address in self.secondaries:
            channel = grpc.insecure_channel(address)
            stub = replication_receiver_pb2_grpc.ReplicationReceiverStub(channel)
            response: ReplicationResponse = stub.replicate_message(ReplicationRequest(message=message))
            print(f"Replication to {address} is {'successful' if response.success else 'failed'}")
