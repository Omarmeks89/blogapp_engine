import uvicorn
from fastapi import FastAPI

from settings import TestSettings
from db.sessions import bootstrap_db, engine
from db.tables import metadata
from blog.api import main, author


app = FastAPI()
app.include_router(main)
app.include_router(author)
app_set = TestSettings()


@app.on_event("startup")
async def build_db_tables() -> None:
    await bootstrap_db(engine, metadata)


@app.on_event("shutdown")
async def shutdown_app() -> None:
    """no impl."""
    return None


if __name__ == "__main__":
    uvicorn.run(app_set.app_run_path, reload=app_set.reloading)
