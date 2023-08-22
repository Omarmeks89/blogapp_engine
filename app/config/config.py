from blog.storage.uow_units import ModerationUOW
from blog.storage.repositories import PostsRepository
from blog.storage.repositories import ContentRepository
from authors.storage.repositories import AuthorsRepository
from authors.storage.authors_uow import AuthorsUOW
from db.sessions import Session
from db.tables import publications
from db.tables import content
from db.tables import authors
from base_tools.bus import MsgBus

from blog.messages import (
        CreateNewPost,
        AddHeaderForPost,
        AddBodyForPost,
        SaveAllNewPostContent,
        UpdateBody,
        UpdateHeader,
        AddToCache,
        StartModeration,
        ModerateContent,
        ModerationStarted,
        ModerationFailed,
        ModerationDoneSuccess,
        SetModerationResult,
        )
from base_tools.sys_messages import (
        NotifyAuthor,
        PostAccepted,
        PostRejected,
        )
from blog.handlers import (
        CreateNewPostHandler,
        AddHeaderForPostHandler,
        AddBodyForPostHandler,
        SaveAllContentHandler,
        UpdateHeaderHandler,
        UpdateBodyHandler,
        AddToCacheHandler,
        BeginPostModerationHandler,
        SendToModerationHandler,
        StartModerationNotifyHandler,
        ModerationFailedHandler,
        ModerationSuccessHandler,
        SetPostModerationResHandler,
        )
from authors.messages import (
        RegisterNewAuthor,
        ActivateAuthor,
        )
from authors.handlers import (
        CreateNewAuthorHandler,
        ActivateAuthorHandler,
        PostAcceptedHandler,
        PostRejectedHandler,
        NotifyAuthorsHandler,
        )


__all__ = (
        "get_bus",
        "mod_uow",
        "cont_uow",
        "authors_uow",
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
authors_repo = AuthorsRepository(authors, run_test=True)

# init UOW
mod_uow = ModerationUOW(repo, Session)
cont_uow = ModerationUOW(cont_repo, Session)
authors_uow = AuthorsUOW(authors_repo, Session)

# set handlers
creator = CreateNewPostHandler(mod_uow)
header_creator = AddHeaderForPostHandler(cont_uow)
body_creator = AddBodyForPostHandler(cont_uow)
saver = SaveAllContentHandler(cont_uow)
header_upd = UpdateHeaderHandler(cont_uow)
body_upd = UpdateBodyHandler(cont_uow)
cachekeeper = AddToCacheHandler(mod_uow)
mod_starter = BeginPostModerationHandler(mod_uow)
mod_sender = SendToModerationHandler(cont_uow)
mod_st_info = StartModerationNotifyHandler(cont_uow)
mod_success = ModerationSuccessHandler(mod_uow)
mod_failed = ModerationFailedHandler(mod_uow)
mod_res_setter = SetPostModerationResHandler(cont_uow)

# users ctx
authrs_reg = CreateNewAuthorHandler(authors_uow)
au_activator = ActivateAuthorHandler(authors_uow)
post_acc = PostAcceptedHandler(authors_uow)
post_rej = PostRejectedHandler(authors_uow)
notify = NotifyAuthorsHandler(authors_uow)

# setup Bus
Bus.subscribe(CreateNewPost, creator)
Bus.subscribe(AddHeaderForPost, header_creator)
Bus.subscribe(AddBodyForPost, body_creator)
Bus.subscribe(SaveAllNewPostContent, saver)
Bus.subscribe(UpdateHeader, header_upd)
Bus.subscribe(UpdateBody, body_upd)
Bus.subscribe(AddToCache, cachekeeper)
Bus.subscribe(StartModeration, mod_starter)
Bus.subscribe(ModerateContent, mod_sender)
Bus.subscribe(ModerationStarted, mod_st_info)
Bus.subscribe(ModerationDoneSuccess, mod_success)
Bus.subscribe(ModerationFailed, mod_failed)
Bus.subscribe(SetModerationResult, mod_res_setter)

# setup Bus (next ctx -> users)
Bus.subscribe(RegisterNewAuthor, authrs_reg)
Bus.subscribe(ActivateAuthor, au_activator)
Bus.subscribe(PostAccepted, post_acc)
Bus.subscribe(PostRejected, post_rej)
Bus.subscribe(NotifyAuthor, notify)
