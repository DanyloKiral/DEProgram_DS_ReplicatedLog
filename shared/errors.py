from logging import Logger


class BadRequestError(Exception):
    pass


class ReplicationNodesError(Exception):
    def __str__(self):
        return 'ReplicationNodesError: Cannot replicate to enough number of nodes'


def handle_bad_request_error(logger: Logger):
    def handler(exc: BadRequestError):
        error_message = f'Error details: {exc}'
        logger.error(f'BAD REQUEST. {error_message}')
        return error_message, 400
    return handler


def handle_replication_error(logger: Logger):
    def handler(exc: ReplicationNodesError):
        error_message = f'Error details: {exc}'
        logger.error(f'REPLICATION ERROR. {error_message}')
        return error_message, 503
    return handler


def handle_general_error(logger: Logger):
    def handler(exc: Exception):
        error_message = f'Error details: {exc}'
        logger.error(f'UNKNOWN ERROR. {error_message}')
        return error_message, 500
    return handler
