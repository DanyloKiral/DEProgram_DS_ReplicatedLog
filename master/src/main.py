from di_container import ServicesContainer
from health_api import HealthApi
from heartbeat_service import HeartbeatService
from message_api import MessageApi
from flask import Flask
from shared.errors import handle_general_error, handle_bad_request_error, BadRequestError, ReplicationNodesError, \
    handle_replication_error


def start_heartbeats():
    heartbeat_service: HeartbeatService = ServicesContainer.heartbeat_service_provider()
    heartbeat_service.schedule_heartbeat_checks()


def start_http_server():
    app = Flask(__name__)
    app.add_url_rule("/api/health", view_func=HealthApi.as_view("health_api"))
    app.add_url_rule("/api", view_func=MessageApi.as_view("message_api"))

    logger = ServicesContainer.logger()
    app.register_error_handler(BadRequestError, handle_bad_request_error(logger))
    app.register_error_handler(ReplicationNodesError, handle_replication_error(logger))
    app.register_error_handler(Exception, handle_general_error(logger))

    app.run(host='0.0.0.0', port=5000)


if __name__ == "__main__":
    start_heartbeats()
    start_http_server()

