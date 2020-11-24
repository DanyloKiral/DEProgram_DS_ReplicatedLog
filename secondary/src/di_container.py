from dependency_injector import containers, providers
from shared.logger import get_module_logger
from message_service import MessageService


class ServicesContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    logger = providers.ThreadSafeSingleton(get_module_logger)
    message_service_provider = providers.ThreadSafeSingleton(MessageService)

