from flask import make_response, jsonify, current_app
from flask.views import MethodView


class SecondaryNodeApi(MethodView):
    def __init__(self):
        self.message_service = current_app.container.message_service_provider()

    def get(self):
        current_messages = self.message_service.get()
        return make_response(jsonify(current_messages), 200)