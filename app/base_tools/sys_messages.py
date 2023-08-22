from base_tools.base_types import Command, Event


class PostAccepted(Event):
    title: str
    author: str


class PostRejected(Event):
    title: str
    author: str
    reasons: list[str]


class PostDeleted(Event):
    pub_id: str


class PostRolledToDraft(Event):
    pub_id: str


class PostPublished(Event):
    pub_id: str


class ActivateLater(Command):
    pub_id: str


class NotifyAuthor(Command):
    email: str
    msg: str
