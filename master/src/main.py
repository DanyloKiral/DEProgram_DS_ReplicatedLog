from master_node_api import MasterNodeApi
from flask import Flask


def start_http_server():
    app = Flask(__name__)
    app.add_url_rule("/api", view_func=MasterNodeApi.as_view("master_node_api"))
    app.run(host='0.0.0.0')


if __name__ == "__main__":
    start_http_server()
