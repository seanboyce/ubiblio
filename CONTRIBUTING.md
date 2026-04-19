# Contributing to uBiblio

## Local Development Environment

1. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

1. Install dependencies:

```bash
pip install -r requirements.txt
```

On Linux, if Pillow fails to build, install the system headers first:

```bash
# Ubuntu / Debian
sudo apt-get install zlib1g-dev libjpeg-turbo8-dev

# macOS (Homebrew)
brew install zlib libjpeg-turbo
```

1. Create a `.env` file with the minimum configuration needed to run locally:

```text
USE_REDIS=false
CREATE_ADMIN_USER=true
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin
```

1. Start the development server:

```bash
set -a && source .env && set +a && uvicorn ubiblio.main:app --host 0.0.0.0 --port 8000 --reload
```

1. Visit `http://localhost:8000/user-setup/` once to create the admin account, then log in at `http://localhost:8000/`.

See [SETUP.md](SETUP.md) for the full list of environment variables and production deployment options.

## Running Tests

Tests are configured via `pytest.ini` at the project root.

1. Install test dependencies:

```bash
pip install -r requirements-test.txt
```

1. Run the test suite:

```bash
python -m pytest tests/ -v
```
