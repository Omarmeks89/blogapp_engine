class SerializationError(BaseException):
    """can`t decode json string."""
    pass


class PublicationError(Exception):
    """can`t finish operation with publication object."""
    pass
