import uvicorn
from fastapi import FastAPI

from settings import TestSettings
# from blog.api import posts


app = FastAPI()
# app.include_router(posts)
app_set = TestSettings()

if __name__ == "__main__":
    uvicorn.run(app_set.app_run_path, reload=app_set.reloading)
