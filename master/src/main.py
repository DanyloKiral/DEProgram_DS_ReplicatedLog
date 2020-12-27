from di_container import ServicesContainer
from master_node_api import MasterNodeApi
from flask import Flask

from replication_sender import ReplicationSender
from shared.errors import handle_general_error, handle_bad_request_error, BadRequestError, ReplicationNodesError, \
    handle_replication_error


def start_heartbeats():
    replication_sender: ReplicationSender = ServicesContainer.replication_sender_provider()
    replication_sender.schedule_heartbeat_checks()


def start_http_server():
    app = Flask(__name__)
    app.add_url_rule("/api", view_func=MasterNodeApi.as_view("master_node_api"))

    logger = ServicesContainer.logger()
    app.register_error_handler(BadRequestError, handle_bad_request_error(logger))
    app.register_error_handler(ReplicationNodesError, handle_replication_error(logger))
    app.register_error_handler(Exception, handle_general_error(logger))

    app.run(host='0.0.0.0', port=5000)


if __name__ == "__main__":
    start_heartbeats()
    start_http_server()

