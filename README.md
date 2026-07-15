# Multi-Agent Academic Research Platform

Production platform for **multi-agent academic literature reviews**.  
Specialized agents search **arXiv** and **Semantic Scholar**, extract findings, critique coverage, and produce a **cited literature review** — exposed through a FastAPI backend and a polished Next.js workspace UI.

---

## Features

- **Beautiful workspace UI** (Next.js) to launch jobs, watch agent progress, and read reports
- **Multi-agent orchestration** with LangGraph (planner → searcher → reader → critic → writer)
- **Academic search** across arXiv and Semantic Scholar, with paper deduplication
- **Async jobs** via Redis + ARQ
- **PostgreSQL persistence** for jobs, papers, agent events, and reports
- **OpenAI-compatible LLM** (OpenAI, Azure, or local gateways)
- **API key auth** (`X-API-Key`)
- **Docker Compose** for full stack (API, worker, web, Postgres, Redis)
- **CI/CD** with GitHub Actions

---

## Architecture

```text
Browser (Next.js :3000)
        │
        ▼
   FastAPI (:8000) ──enqueue──► Redis / ARQ Worker
                                      │
                                      ▼
                            LangGraph agent pipeline
                           (arXiv + Semantic Scholar)
                                      │
                                      ▼
                                 PostgreSQL
```

---

## Repository structure

```text
Multi-Agent-Research-Platform/
├── .github/workflows/     # CI + CD
├── backend/               # FastAPI + LangGraph + ARQ
├── frontend/              # Next.js App Router UI
├── LICENSE
└── README.md
```

---

## Quick start (Docker)

```bash
git clone https://github.com/Mayurgohane/Multi-Agent-Research-Platform.git
cd Multi-Agent-Research-Platform/backend

# PowerShell
$env:OPENAI_API_KEY = "sk-your-key"

docker compose up --build
```

| Service | URL |
|---------|-----|
| **Web UI** | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |

---

## Local development

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
cp .env.example .env            # set OPENAI_API_KEY

docker compose up postgres redis -d
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# other terminal
arq app.workers.research_worker.WorkerSettings
```

### Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

`NEXT_PUBLIC_API_BASE_URL` should point at the API (default `http://localhost:8000`).  
`NEXT_PUBLIC_API_KEY` must match backend `API_KEY` when auth is enabled.

---

## UI map

| Route | Purpose |
|-------|---------|
| `/` | Brand landing + pipeline overview |
| `/research` | Launch a review + recent jobs |
| `/research/[id]` | Live agent timeline + final report |

---

## API (summary)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/research` | Start job |
| `GET` | `/api/v1/research` | List jobs (`?status=` optional filter) |
| `GET` | `/api/v1/research/{id}` | Status + events |
| `GET` | `/api/v1/research/{id}/report` | Final report |
| `POST` | `/api/v1/research/{id}/retry` | Re-queue failed/cancelled job |
| `DELETE` | `/api/v1/research/{id}` | Cancel |
| `GET` | `/health` | Liveness |

Full backend details: [backend/README.md](backend/README.md)

---

## Configuration

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | LLM provider key |
| `API_KEY` | Required `X-API-Key` when set |
| `CORS_ORIGINS` | Allowed origins in production (comma-separated) |
| `DATABASE_URL` | `postgresql+asyncpg://...` |
| `REDIS_URL` | ARQ broker |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | Backend base URL |
| `NEXT_PUBLIC_API_KEY` | Sent as `X-API-Key` |

---

## Testing & quality

```bash
# backend
cd backend && pytest -q && ruff check app tests

# frontend
cd frontend && npm run build
```

---

## CI/CD

Same pipelines cover **backend + frontend**.

| Workflow | Trigger | Backend | Frontend |
|----------|---------|---------|----------|
| **CI** (`ci.yml`) | Push / PR | Ruff, pytest, Docker build | `npm run build`, Docker build |
| **CD** (`cd.yml`) | `main` / `v*` tags | Push `ghcr.io/<owner>/marp-backend` | Push `ghcr.io/<owner>/marp-frontend` |

Optional CD secrets/vars for the frontend image build:
- `vars.NEXT_PUBLIC_API_BASE_URL`
- `secrets.NEXT_PUBLIC_API_KEY`


---

## Tech stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js 15, React 19, Fraunces + Manrope |
| API | FastAPI, Uvicorn, Pydantic v2 |
| Agents | LangGraph |
| Search | arXiv, Semantic Scholar |
| Data / jobs | PostgreSQL, Redis, ARQ |

---

## License

MIT — see [LICENSE](LICENSE).
