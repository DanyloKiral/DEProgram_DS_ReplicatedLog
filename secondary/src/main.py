from di_container import Container
from secondary_node_api import SecondaryNodeApi
from flask import Flask

if __name__ == "__main__":
    container = Container()
    app = Flask(__name__)
    app.container = container
    app.add_url_rule("/api", view_func=SecondaryNodeApi.as_view("secondary_node_api"))
    app.run(host='0.0.0.0')
