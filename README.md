# DocTask --- Task 1

AI-powered document analysis workflow for ingesting documents,
extracting evidence, analyzing delivery risks, reconciling findings,
supporting review, and committing final results.

## Implementation status

### Implemented

-   Project creation and management
-   PDF, DOCX, and text document upload/parsing
-   Document chunking and persistence
-   PostgreSQL with pgvector
-   Semantic retrieval infrastructure
-   LangGraph staged workflow
-   Persistent runs and stage runs
-   Retry handling with a maximum of 3 attempts
-   Human-review escalation state
-   Findings and reconciliation
-   Run history
-   REST APIs
-   React + TypeScript frontend
-   Dockerized PostgreSQL, backend, frontend, and MCP service
-   Groq LLM integration
-   Structured LLM finding analysis
-   Stage duration tracking
-   Input/output/total token tracking
-   Estimated LLM cost tracking
-   Run-level usage/cost summary
-   Frontend Usage & Cost display
-   Nginx SPA routing

### Not implemented / not fully demonstrated

The MCP server/container exists, but the MCP workflow has not been fully
verified end-to-end as part of the Task 1 acceptance flow. It should
therefore not be presented as a fully demonstrated Task 1 feature.

## Architecture

``` text
React Frontend
      |
      v
FastAPI Backend
   |         |
   v         v
PostgreSQL  LangGraph
 + pgvector    |
               v
             Groq
```

## Workflow

``` text
INGEST
  ↓
EXTRACT
  ↓
ANALYZE
  ↓
RECONCILE
  ↓
REVIEW
  ↓
COMMIT
```

Stage states include `pending`, `running`, `completed`, `failed`,
`skipped`, and `escalated`.

Failed stages can be retried up to three times.

## LLM cost tracking

Configured model:

``` env
GROQ_MODEL=openai/gpt-oss-20b
```

Current cost estimates:

``` text
Input:  $0.075 / 1M tokens
Output: $0.30  / 1M tokens
```

Tracked per stage:

-   Input tokens
-   Output tokens
-   Total tokens
-   Duration
-   Estimated cost in USD

Run-level totals are exposed through the run API and displayed in the
frontend.

Example:

``` json
{
  "usage": {
    "input_tokens": 4210,
    "output_tokens": 387,
    "total_tokens": 4597,
    "estimated_cost_usd": 0.000432
  }
}
```

These are application-level estimates, not billing statements.

## Project structure

``` text
doctask-pritesh-umraniya/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── documents/
│   │   ├── models/
│   │   ├── retrieval/
│   │   ├── schemas/
│   │   └── mcp/
│   ├── alembic/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── .env
├── postgresql/
│   └── init.sql
└── docker-compose.yml
```

## Requirements

-   Docker Desktop
-   Docker Compose
-   Groq API key

Local Python/Node installations are not required for the Docker
workflow.

## Environment

Create `backend/.env` with the variables expected by the application
configuration. At minimum:

``` env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/doctask
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

Never commit real API keys.

## One-command Docker setup

From the repository root:

``` powershell
docker compose up -d --build
```

Check services:

``` powershell
docker compose ps
```

Expected services:

``` text
doctask-postgres
doctask-backend
doctask-frontend
doctask-mcp
```

Ports:

``` text
Frontend:   http://localhost:5173
Backend:    http://localhost:8000
MCP:        http://localhost:8001
PostgreSQL: localhost:5433
```

## Database

PostgreSQL uses:

``` text
Database: doctask
User: postgres
Password: postgres
```

`postgresql/init.sql` enables the vector extension:

``` sql
CREATE EXTENSION IF NOT EXISTS vector;
```

The backend uses the Python `pgvector` package together with
PostgreSQL's vector extension.

The backend container runs Alembic migrations before starting FastAPI.

## Frontend

The frontend uses:

-   React
-   TypeScript
-   Vite
-   Tailwind CSS
-   React Query
-   Lucide icons

Production frontend assets are served by Nginx.

`frontend/nginx.conf` uses:

``` nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

This allows React Router routes such as `/projects` to work after
browser refresh.

## Backend API

Main API groups include:

``` text
/projects
/documents
/projects/{project_id}/runs
/projects/{project_id}/runs/{run_id}
/search
/reviews
```

FastAPI documentation:

``` text
http://localhost:8000/docs
```

## Basic Task 1 test flow

1.  Start the stack:

``` powershell
docker compose up -d --build
```

2.  Confirm all services:

``` powershell
docker compose ps
```

3.  Open:

``` text
http://localhost:5173
```

4.  Create a project.
5.  Upload the required source documents.
6.  Create a workflow run.
7.  Execute the workflow.
8.  Observe stage progression.
9.  Verify findings.
10. Verify reconciliation.
11. Complete review when required.
12. Verify the final run state.
13. Open run details.
14. Verify Usage & Cost.

Expected usage fields:

``` text
Input tokens
Output tokens
Total tokens
Estimated cost
Stage duration
```

## Useful Docker commands

Start:

``` powershell
docker compose up -d
```

Build and start:

``` powershell
docker compose up -d --build
```

Stop:

``` powershell
docker compose down
```

Backend logs:

``` powershell
docker compose logs --tail=50 backend
```

Frontend logs:

``` powershell
docker compose logs --tail=50 frontend
```

PostgreSQL logs:

``` powershell
docker compose logs --tail=50 postgres
```

MCP logs:

``` powershell
docker compose logs --tail=50 mcp
```

Frontend rebuild:

``` powershell
docker compose up -d --build frontend
```

Backend rebuild:

``` powershell
docker compose up -d --build backend
```

## Verification checklist

-   [ ] Docker Compose starts successfully
-   [ ] PostgreSQL is healthy
-   [ ] Backend starts without restart loops
-   [ ] Frontend loads
-   [ ] `/projects` works after refresh
-   [ ] Project creation works
-   [ ] Document upload works
-   [ ] Workflow run creation works
-   [ ] Workflow execution works
-   [ ] Findings are generated
-   [ ] Reconciliation works
-   [ ] Review flow works when required
-   [ ] Final run state is persisted
-   [ ] Run history is visible
-   [ ] Stage duration is recorded
-   [ ] Token usage is recorded
-   [ ] Estimated cost is recorded
-   [ ] Run-level usage is displayed
-   [ ] No secrets are committed
-   [ ] MCP is not claimed as fully demonstrated unless separately
    verified

## Task 1 demo focus

The recommended functional demonstration is:

``` text
Project
  ↓
Documents
  ↓
Run
  ↓
Agent workflow
  ↓
Findings
  ↓
Reconciliation
  ↓
Review
  ↓
Final result
  ↓
Usage & Cost
```

MCP should be omitted from the functional demo unless its
client-to-server workflow is explicitly verified end-to-end.

## Security

Do not commit:

``` text
.env
API keys
Groq credentials
local database credentials
uploaded documents
runtime/generated files
```

Keep runtime upload directories such as `uploads/` in `.gitignore`.

## License

Created as part of the DocTask implementation task.
