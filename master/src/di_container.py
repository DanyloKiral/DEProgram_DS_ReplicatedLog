from dependency_injector import containers, providers
from message_service import MessageService


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    message_service_provider = providers.Singleton(MessageService)
