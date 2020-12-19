from logging import Logger
from flask import request, abort, make_response, jsonify, current_app
from flask.views import MethodView

from di_container import ServicesContainer
from message_service import MessageService
from replication_sender import ReplicationSender


class MasterNodeApi(MethodView):
    def __init__(self):
        self.message_service: MessageService = ServicesContainer.message_service_provider()
        self.replication_sender: ReplicationSender = ServicesContainer.replication_sender_provider()
        self.logger: Logger = ServicesContainer.logger()

    def get(self):
        self.logger.info('GET request')
        current_messages = self.message_service.get()
        return make_response(jsonify(current_messages), 200)

    def post(self):
        data: dict = request.get_json()
        if 'message' not in data:
            self.logger.error('No message provided')
            abort(400)

        message = data.get('message')
        write_concern = data.get('write_concern') or 1
        self.logger.info(f'POST request. Message = {message}; Write concern = {write_concern}')

        message_id = self.message_service.append(message)
        self.replication_sender.replicate_message_to_secondaries(message, message_id, write_concern - 1)

        return make_response('', 200)


