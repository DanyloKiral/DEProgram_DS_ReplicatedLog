from flask import make_response, jsonify
from flask.views import MethodView
from di_container import ServiceProviders


class SecondaryNodeApi(MethodView):
    def __init__(self):
        self.message_service = ServiceProviders.message_service_provider()

    def get(self):
        current_messages = self.message_service.get()
        return make_response(jsonify(current_messages), 200)