"""Pytest loads this before test modules so env is set before `ubiblio.vars` is imported."""
import os

# Rate limiting uses Redis + FastAPILimiter.init(); tests skip that unless you opt in.
os.environ["USE_REDIS"] = "false"
