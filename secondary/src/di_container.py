from dependency_injector import containers, providers
from message_service import MessageService


class ServiceProviders(containers.DeclarativeContainer):
    config = providers.Configuration()

    message_service_provider = providers.ThreadSafeSingleton(MessageService)

