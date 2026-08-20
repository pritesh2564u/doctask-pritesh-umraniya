# DocTask

DocTask is a document intelligence and reconciliation workflow system that processes multiple project documents, extracts evidence, identifies findings, detects conflicts, and routes uncertain cases through human review before committing the final result.

The system is designed around an explicit staged workflow rather than a single black-box AI call.

---

## Current Status

The core workflow is implemented and working:

- Multi-document project processing
- PDF and DOCX document ingestion
- Document chunking and evidence tracking
- Evidence-backed findings
- Multi-document reconciliation
- Human review gate
- Approve / reject findings
- Reconciliation conflict resolution
- Workflow resume after human decisions
- Persistent workflow stage state
- Retry / failure / escalation handling
- REST API for programmatic workflow execution
- PostgreSQL persistence
- pgvector support
- Docker-based local development
- React frontend with workflow progress and review UI
- Project and document management
- Run history
- Expandable workflow stage details

Additional hardening and observability work remains and will be completed after Task 2.

---

# Architecture

```text
                    ┌─────────────────────┐
                    │      Frontend       │
                    │    React + Vite     │
                    └──────────┬──────────┘
                               │
                               │ REST API
                               ▼
                    ┌─────────────────────┐
                    │      FastAPI        │
                    │      Backend        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Workflow Engine   │
                    │      LangGraph      │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
          Ingest            Extract           Analyze
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                         Reconcile
                               │
                               ▼
                            Review
                               │
                               ▼
                            Commit
                               │
                               ▼
                    ┌─────────────────────┐
                    │     PostgreSQL      │
                    │      + pgvector     │
                    └─────────────────────┘
```
