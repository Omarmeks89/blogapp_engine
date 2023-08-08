from blog.storage.uow_units import ModerationUOW
from blog.storage.repositories import PostsRepository
from blog.storage.repositories import ContentRepository
from db.sessions import Session
from db.tables import publications
from db.tables import content
from base_tools.bus import MsgBus

from blog.messages import (
        CreateNewPost,
        NotifyAuthor,
        )
from blog.handlers import (
        NotifyAuthorsCmdHandler,
        CreateNewPostHandler,
        )


Bus = MsgBus


async def get_bus() -> MsgBus:
    if Bus.is_set():
        return Bus.get_bus()
    else:
        raise Exception("BootstrapError")


# init Repo
repo = PostsRepository(publications, run_test=True)
cont_repo = ContentRepository(content, run_test=True)

# init UOW
uow = ModerationUOW(repo, Session)

# set handlers
notifyer = NotifyAuthorsCmdHandler(uow)
creator = CreateNewPostHandler(uow)

# setup Bus
Bus.subscribe(CreateNewPost, creator)
Bus.subscribe(NotifyAuthor, notifyer)
