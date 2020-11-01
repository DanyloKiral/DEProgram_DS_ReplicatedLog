from flask import request, abort, make_response, jsonify
from flask.views import MethodView
from di_container import ServiceProviders
from message_service import MessageService
from replication_sender import ReplicationSender


class MasterNodeApi(MethodView):
    def __init__(self):
        self.__message_service: MessageService = ServiceProviders.message_service_provider()
        self.__replication_sender: ReplicationSender = ServiceProviders.replication_sender_provider()

    def get(self):
        current_messages = self.__message_service.get()
        return make_response(jsonify(current_messages), 200)

    def post(self):
        data: dict = request.get_json()
        if 'message' not in data:
            abort(400)

        message = data.get('message')
        self.__message_service.append(message)
        self.__replication_sender.replicate_message_to_secondaries(message)

        return make_response('', 200)

