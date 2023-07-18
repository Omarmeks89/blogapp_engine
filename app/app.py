from fastapi import FastAPI

from moderation.api import posts


app = FastAPI()
app.include_router(posts)
