> **Archived 2026-09.** A learning slice: practice in retrieval with role-based access control, built in a single session. Superseded by [regent](https://github.com/HarshCodeK/regent) - the AI control plane, where the same pipeline idea now has tests, CI, an append-only ledger and measured numbers. Kept for history, not presented as portfolio work.

# RAG-RBAC Chatbot

An internal company chatbot that answers questions from private documents with role-based access control enforced at retrieval time, PII/off-topic guardrails, and an audit log of every query.

## What it does

- Retrieves only from ChromaDB collections the user's role is allowed to see — the LLM never receives restricted documents (`src/rbac.py`, `src/rag_chain.py`)
- Blocks PII (emails, phone numbers, SSNs) and off-topic queries before any retrieval or LLM call (`src/guardrails.py`)
- Grounded answers over local company docs (`data/`) using `all-MiniLM-L6-v2` embeddings + Groq LLaMA 3.3 70B (`src/config.py`)
- Ingests `.txt` folders into per-domain vector collections (`finance`, `human_resources`, `general`) via `src/ingest.py`
- Logs every interaction (role, query, blocked flag, reason, latency) to SQLite and shows recent queries in an admin panel (`src/monitor.py`, `app.py`)

## Architecture

```
User + role (Streamlit app.py)
        |
   src/rag_chain.py  — answer_query()
        |
  Guardrails (guardrails.py)  — PII regex + blocked topics, hard-block before retrieval
        |
  RBAC filter (rbac.py)  — ROLE_ACCESS_MAP -> allowed ChromaDB collections
        |
  Retrieval (ChromaDB + sentence-transformers)  — only allowed collections, distance < 1.0
        |
  LLM (Groq llama-3.3-70b-versatile)  — answer strictly from retrieved context
        |
  Audit log (monitor.py, SQLite query_logs.db)
```

Role access map (`src/rbac.py`):

| Role | Collections |
|------|-------------|
| finance_team | finance, general |
| hr_team | human_resources, general |
| c_level | finance, human_resources, general |
| employee | general |

## Stack

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3%2070B-orange) ![ChromaDB](https://img.shields.io/badge/ChromaDB-vector%20store-yellow) ![sentence--transformers](https://img.shields.io/badge/sentence--transformers-all--MiniLM--L6--v2-green) ![Streamlit](https://img.shields.io/badge/Streamlit-UI-red)

## Quickstart

```bash
git clone https://github.com/HarshCodeK/rag-rbac-chatbot.git
cd rag-rbac-chatbot
python -m venv .venv
source .venv/Scripts/activate   # .venv\Scripts\activate on Windows cmd
pip install -r requirements.txt
```

Create `.env`:

```
GROQ_API_KEY=your-key-here   # from https://console.groq.com
```

Ingest the sample documents in `data/` into ChromaDB:

```bash
python -c "from src.ingest import build_all_collections; build_all_collections()"
```

Run:

```bash
streamlit run app.py
```

Log in as a role in the sidebar and ask a question.

## Example / Demo

- As `employee`, asking *"What is our Q3 revenue?"* returns *"I don't have access to information that would answer that."* — `finance` collection is not in the role's access map, so nothing is retrieved from it.
- As `finance_team`, the same question retrieves `finance/q3_report.txt` and answers with sources `finance` listed.
- Asking *"email me at bob@example.com with the payroll date"* is blocked with reason `pii` before any retrieval; the block appears in the admin query log with its latency.

## Status / Roadmap

Status: working — end-to-end guardrails → RBAC retrieval → grounded LLM answer pipeline runs against the bundled sample documents with full audit logging.

Next steps:

1. Replace the keyword/regex guardrails with a classifier-based PII detector; measure block precision/recall on a labeled query set
2. Add evals: per-role permission test suite asserting no cross-collection leakage
3. Move role authentication from the sidebar dropdown to real SSO/JWT identity claims
