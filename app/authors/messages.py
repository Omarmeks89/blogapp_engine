from base_tools.base_types import Command


class RegisterNewAuthor(Command):
    """internal cmd impl."""
    uid: str
    login: str
    email: str
    passwd: str


class ActivateAuthor(Command):
    """activate user after email confirmation."""
    uid: str
