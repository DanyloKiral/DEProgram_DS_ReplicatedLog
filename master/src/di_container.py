from dependency_injector import containers, providers

from heartbeat_service import HeartbeatService
from nodes_state import NodesState
from shared.logger import get_module_logger
from message_service import MessageService
from replication_sender import ReplicationSender


class ServicesContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    logger = providers.ThreadSafeSingleton(get_module_logger)
    nodes_state_provider = providers.ThreadSafeSingleton(NodesState)
    message_service_provider = providers.ThreadSafeSingleton(MessageService)
    replication_sender_provider = providers.ThreadSafeSingleton(
        ReplicationSender,
        logger=logger,
        nodes_state=nodes_state_provider)

    heartbeat_service_provider = providers.ThreadSafeSingleton(
        HeartbeatService,
        logger=logger,
        nodes_state=nodes_state_provider,
        replication_sender=replication_sender_provider)

