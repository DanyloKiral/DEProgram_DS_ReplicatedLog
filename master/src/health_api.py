from flask import make_response, jsonify
from flask.views import MethodView
from di_container import ServicesContainer
from nodes_state import NodesState


class HealthApi(MethodView):
    def __init__(self):
        self.nodes_state: NodesState = ServicesContainer.nodes_state_provider()

    def get(self):
        return make_response(jsonify(self.nodes_state.get_node_statuses()), 200)
