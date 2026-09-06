"""FastAPI entrypoint with filtered query routes mounted."""

from .app_legacy import *  # noqa: F401,F403
from .api_filters import router as query_router
from .full_api import router as full_router

app.include_router(query_router)
app.include_router(full_router)
