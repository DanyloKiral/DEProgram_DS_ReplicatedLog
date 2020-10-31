from flask import request, abort, make_response, jsonify, current_app
from flask.views import MethodView


class MasterNodeApi(MethodView):
    def __init__(self):
        self.message_service = current_app.container.message_service_provider()

    def get(self):
        current_messages = self.message_service.get()
        return make_response(jsonify(current_messages), 200)

    def post(self):
        data: dict = request.get_json()
        if 'message' not in data:
            abort(400)

        self.message_service.append(data.get('message'))

        return make_response('', 200)

