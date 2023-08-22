class SerializationError(BaseException):
    """can`t decode json string."""
    pass


class PublicationError(Exception):
    """can`t finish operation with publication object."""
    pass


class BusError(Exception):
    """bus can`t operate."""
    pass


class RepositoryError(BaseException):
    """repository can`t continue."""
    pass


class DBError(Exception):
    """error in db operation."""
    pass


class HandlerError(Exception):
    """handler can`t operate."""
    pass


class ModerationError(Exception):
    """moderation process failed."""
    pass


class BootstrapError(Exception):
    """fail on app bootstrap."""
    pass


class BodyFetchingError(Exception):
    """error on API connection."""
    pass


class InvalidCredentials(Exception):
    """invalid api_secret or api_num."""
    pass
