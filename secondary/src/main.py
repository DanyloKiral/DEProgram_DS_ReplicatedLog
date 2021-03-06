import asyncio
import os
from threading import Thread

from di_container import ServicesContainer
from replication_receiver import ReplicationReceiver
from secondary_node_api import SecondaryNodeApi
from flask import Flask
import grpc

from shared import replication_receiver_pb2_grpc
from shared.errors import handle_general_error


def start_http_server():
    api_port = os.getenv('API_PORT') or 5000
    app = Flask(__name__)
    app.add_url_rule("/api", view_func=SecondaryNodeApi.as_view("secondary_node_api"))

    logger = ServicesContainer.logger()
    app.register_error_handler(Exception, handle_general_error(logger))

    app.run(host='0.0.0.0', port=api_port)


async def start_grpc_server():
    grpc_port = os.getenv('GRPC_PORT') or 50051
    server = grpc.aio.server()
    replication_receiver_pb2_grpc.add_ReplicationReceiverServicer_to_server(
        ReplicationReceiver(), server)
    server.add_insecure_port(f'[::]:{grpc_port}')
    await server.start()
    await server.wait_for_termination()


def run_grpc():
    asyncio.run(start_grpc_server())


def main():
    task1 = Thread(target=start_http_server, args=[])
    task2 = Thread(target=run_grpc, args=[])
    task1.start()
    task2.start()


if __name__ == "__main__":
    main()
