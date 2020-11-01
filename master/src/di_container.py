from dependency_injector import containers, providers
from message_service import MessageService
from replication_sender import ReplicationSender


class ServiceProviders(containers.DeclarativeContainer):
    config = providers.Configuration()
    message_service_provider = providers.Singleton(MessageService)
    replication_sender_provider = providers.Singleton(ReplicationSender)
