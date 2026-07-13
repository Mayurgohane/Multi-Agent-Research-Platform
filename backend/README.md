# Backend

Canonical project documentation lives in the [root README](../README.md).  
This file is a short backend-focused cheat sheet.

## Run with Docker

```bash
$env:OPENAI_API_KEY = "sk-your-key"   # PowerShell
docker compose up --build
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  

## Local run

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -e ".[dev]"
cp .env.example .env            # set OPENAI_API_KEY

docker compose up postgres redis -d
alembic upgrade head

uvicorn app.main:app --reload --port 8000
# other terminal:
arq app.workers.research_worker.WorkerSettings
```

## Useful commands

```bash
pytest -q
ruff check app tests
ruff format app tests
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

## Package layout

```text
app/
  api/v1/      REST endpoints
  agents/      LangGraph pipeline
  services/   External clients + research runner
  models/     SQLAlchemy ORM
  schemas/    Pydantic models
  workers/    ARQ worker
  core/       Settings, logging, auth
  db/         Engine / session
```

See [`.env.example`](.env.example) for all configuration knobs.
