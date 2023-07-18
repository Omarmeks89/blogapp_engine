import uvicorn

from settings import TestSettings


app_set = TestSettings()
uvicorn.run(app_set.app_run_path, reload=app_set.reloading)
