# DocTask — Task 1

AI-powered document analysis workflow for ingesting documents, extracting evidence, analyzing delivery risks, reconciling findings, supporting review, and committing final results.

## Implementation status

### Implemented

- Project creation and management
- PDF, DOCX, and text document upload/parsing
- Document chunking and persistence
- PostgreSQL with pgvector
- Semantic retrieval infrastructure
- LangGraph staged workflow
- Persistent runs and stage runs
- Retry handling with a maximum of 3 attempts
- Human-review escalation state
- Findings and reconciliation
- Run history
- REST APIs
- React + TypeScript frontend
- Dockerized PostgreSQL, backend, frontend, and MCP service
- Groq LLM integration
- Structured LLM finding analysis
- Stage duration tracking
- Input/output/total token tracking
- Estimated LLM cost tracking
- Run-level usage/cost summary
- Frontend Usage & Cost display
- Nginx SPA routing
- MCP Streamable HTTP server
- Six MCP tools for run management and reconciliation
- MCP integration test covering the clean workflow path
- MCP conflict/reconciliation flow manually verified end-to-end

### MCP implementation

The MCP server is implemented and verified through the MCP client over Streamable HTTP.

Endpoint:

```text
http://localhost:8001/mcp
```

Available tools:

```text
create_run
get_run_status
execute_run
get_reconciliation
resolve_reconciliation
list_project_runs
```

The MCP integration test verifies:

- MCP server connectivity
- MCP tool discovery
- Run creation
- Run status retrieval
- Workflow execution
- Reconciliation retrieval
- Project run history

The reconciliation path was also verified with conflicting evidence. Multiple open conflicts were resolved individually, the workflow remained paused while conflicts remained, and resumed once all reconciliation conflicts were resolved. The workflow then correctly escalated to human review when findings still required approval.

## Architecture

```text
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

MCP Client
    |
    v
MCP Streamable HTTP Server
    |
    v
DocTask workflow/services
```

## Workflow

```text
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

Stage states include `pending`, `running`, `completed`, `failed`, `skipped`, and `escalated`.

Failed stages can be retried up to three times.

The workflow can automatically complete when no human review is required. When evidence conflicts or findings require human approval, the workflow pauses/escalates instead of silently committing a result.

## MCP workflow

```text
MCP Client
    |
    | create_run
    v
Create Run
    |
    | get_run_status
    v
Track Run
    |
    | execute_run
    v
Execute Workflow
    |
    | get_reconciliation
    v
Inspect Conflicts
    |
    | resolve_reconciliation
    v
Resolve Human Conflicts
    |
    | get_run_status
    v
Continue / Escalate
    |
    | list_project_runs
    v
Run History
```

### MCP tool summary

| Tool | Purpose |
|---|---|
| `create_run` | Create a workflow run for a project |
| `get_run_status` | Retrieve run status, stage state, and workflow progress |
| `execute_run` | Execute or continue the staged workflow |
| `get_reconciliation` | Retrieve reconciliation conflicts for a run |
| `resolve_reconciliation` | Resolve one reconciliation conflict and resume the workflow when appropriate |
| `list_project_runs` | Retrieve recent runs for a project |

### MCP integration test

The integration test is located at:

```text
backend/tests/mcp/test_client.py
```

Run it from the repository root:

```powershell
docker compose exec mcp python /app/tests/mcp/test_client.py
```

Expected result:

```text
MCP integration test passed.
```

## LLM cost tracking

Configured model:

```env
GROQ_MODEL=openai/gpt-oss-20b
```

Current cost estimates:

```text
Input:  $0.075 / 1M tokens
Output: $0.30  / 1M tokens
```

Tracked per stage:

- Input tokens
- Output tokens
- Total tokens
- Duration
- Estimated cost in USD

Run-level totals are exposed through the run API and displayed in the frontend.

Example:

```json
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

```text
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
│   ├── tests/
│   │   └── mcp/
│   │       └── test_client.py
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

- Docker Desktop
- Docker Compose
- Groq API key

Local Python/Node installations are not required for the Docker workflow.

## Environment

Create `backend/.env` with the variables expected by the application configuration. At minimum:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/doctask
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

Never commit real API keys.

## One-command Docker setup

From the repository root:

```powershell
docker compose up -d --build
```

Check services:

```powershell
docker compose ps
```

Expected services:

```text
doctask-postgres
doctask-backend
doctask-frontend
doctask-mcp
```

Ports:

```text
Frontend:   http://localhost:5173
Backend:    http://localhost:8000
MCP:        http://localhost:8001
PostgreSQL: localhost:5433
```

The MCP container listens on port `8000` internally and is exposed as port `8001` on the host.

## Database

PostgreSQL uses:

```text
Database: doctask
User: postgres
Password: postgres
```

`postgresql/init.sql` enables the vector extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

The backend uses the Python `pgvector` package together with PostgreSQL's vector extension.

The backend container runs Alembic migrations before starting FastAPI.

## Frontend

The frontend uses:

- React
- TypeScript
- Vite
- Tailwind CSS
- React Query
- Lucide icons

Production frontend assets are served by Nginx.

`frontend/nginx.conf` uses:

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

This allows React Router routes such as `/projects` to work after browser refresh.

## Backend API

Main API groups include:

```text
/projects
/documents
/projects/{project_id}/runs
/projects/{project_id}/runs/{run_id}
/search
/reviews
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

## Basic Task 1 test flow

1. Start the stack:

```powershell
docker compose up -d --build
```

2. Confirm all services:

```powershell
docker compose ps
```

3. Open:

```text
http://localhost:5173
```

4. Create a project.
5. Upload the required source documents.
6. Create a workflow run.
7. Execute the workflow.
8. Observe stage progression.
9. Verify findings.
10. Verify reconciliation.
11. Complete review when required.
12. Verify the final run state.
13. Open run details.
14. Verify Usage & Cost.

Expected usage fields:

```text
Input tokens
Output tokens
Total tokens
Estimated cost
Stage duration
```

## MCP test flow

After the Docker stack is running:

```powershell
docker compose exec mcp python /app/tests/mcp/test_client.py
```

For MCP logs:

```powershell
docker compose logs --tail=50 mcp
```

The MCP endpoint is:

```text
http://localhost:8001/mcp
```

The integration test connects to the server from inside the MCP container using:

```text
http://127.0.0.1:8000/mcp
```

This avoids depending on host port mappings during the container-level integration test.

## Useful Docker commands

Start:

```powershell
docker compose up -d
```

Build and start:

```powershell
docker compose up -d --build
```

Stop:

```powershell
docker compose down
```

Backend logs:

```powershell
docker compose logs --tail=50 backend
```

Frontend logs:

```powershell
docker compose logs --tail=50 frontend
```

PostgreSQL logs:

```powershell
docker compose logs --tail=50 postgres
```

MCP logs:

```powershell
docker compose logs --tail=50 mcp
```

Frontend rebuild:

```powershell
docker compose up -d --build frontend
```

Backend rebuild:

```powershell
docker compose up -d --build backend
```

MCP rebuild:

```powershell
docker compose up -d --build mcp
```

## Verification checklist

- [ ] Docker Compose starts successfully
- [ ] PostgreSQL is healthy
- [ ] Backend starts without restart loops
- [ ] Frontend loads
- [ ] `/projects` works after refresh
- [ ] Project creation works
- [ ] Document upload works
- [ ] Workflow run creation works
- [ ] Workflow execution works
- [ ] Findings are generated
- [ ] Reconciliation works
- [ ] Review flow works when required
- [ ] Final run state is persisted
- [ ] Run history is visible
- [ ] Stage duration is recorded
- [ ] Token usage is recorded
- [ ] Estimated cost is recorded
- [ ] Run-level usage is displayed
- [ ] MCP server is reachable through Streamable HTTP
- [ ] MCP tools are discoverable
- [ ] MCP integration test passes
- [ ] MCP reconciliation flow has been verified
- [ ] No secrets are committed

## Task 1 demo focus

The recommended functional demonstration is:

```text
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

The MCP implementation can additionally be demonstrated with the MCP integration test and the Streamable HTTP endpoint.

## Security

Do not commit:

```text
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
