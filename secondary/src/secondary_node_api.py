from logging import Logger

from flask import make_response, jsonify
from flask.views import MethodView

from di_container import ServicesContainer
from message_service import MessageService


class SecondaryNodeApi(MethodView):
    def __init__(self):
        self.message_service: MessageService = ServicesContainer.message_service_provider()
        self.logger: Logger = ServicesContainer.logger()

    def get(self):
        self.logger.info('GET request')
        current_messages = self.message_service.get()
        return make_response(jsonify(current_messages), 200)
