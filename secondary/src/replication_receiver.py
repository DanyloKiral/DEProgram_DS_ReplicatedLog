from shared.replication_receiver_pb2 import ReplicationRequest, ReplicationResponse
from shared import replication_receiver_pb2_grpc
from di_container import ServiceProviders
from message_service import MessageService


class ReplicationReceiver(replication_receiver_pb2_grpc.ReplicationReceiverServicer):
    def __init__(self):
        self.__message_service: MessageService = ServiceProviders.message_service_provider()

    def replicate_message(self, request: ReplicationRequest, context):
        self.__message_service.append(request.message)
        return ReplicationResponse(success=True)
