from concurrent import futures
from threading import Thread
from replication_receiver import ReplicationReceiver
from secondary_node_api import SecondaryNodeApi
from flask import Flask
import grpc

from shared import replication_receiver_pb2_grpc


def start_http_server():
    app = Flask(__name__)
    app.add_url_rule("/api", view_func=SecondaryNodeApi.as_view("secondary_node_api"))
    app.run(host='0.0.0.0')


def start_grpc_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    replication_receiver_pb2_grpc.add_ReplicationReceiverServicer_to_server(
        ReplicationReceiver(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


def main():
    task1 = Thread(target=start_http_server, args=[])
    task2 = Thread(target=start_grpc_server, args=[])
    task1.start()
    task2.start()


if __name__ == "__main__":
    main()
