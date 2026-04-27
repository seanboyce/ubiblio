"""Pytest loads this before test modules so env is set before `ubiblio.vars` is imported."""
import os

# Rate limiting uses Redis + FastAPILimiter.init(); tests skip that unless you opt in.
os.environ["USE_REDIS"] = "false"


def pytest_configure(config):
    """
    Ensure the SQLite schema exists before any test runs.

    Tests that go through ``TestClient(app)`` get the schema for free because
    ``ubiblio.main`` calls ``Base.metadata.create_all`` at import time, but tests
    that exercise lower-level helpers (e.g. ``tests/dependencies/test_auth.py``)
    don't import ``ubiblio.main``. On a clean CI checkout there's no ``sql_app.db``,
    so they fail with "no such table: users". Importing the schema here is enough
    to make either path work.
    """
    from ubiblio import models
    from ubiblio.database import engine

    models.Base.metadata.create_all(bind=engine)
