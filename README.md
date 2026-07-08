# RAG-RBAC Chatbot

An internal company chatbot that answers questions from private company documents, restricts what each user can see based on their role (RBAC), and blocks PII leakage and off-topic questions.

## Why RBAC matters for RAG systems

Without RBAC at the retrieval level, any employee could ask the chatbot for anyone else's data. For example, without access control, an intern could ask "What is our Q3 revenue?" and get a detailed financial answer. Access control has to happen at retrieval time — not just at the UI level — because the RAG pipeline retrieves documents before the LLM sees them. If you only hide results in the UI, the LLM has already seen restricted data, which is a data leak. This project enforces RBAC by only retrieving from collections the user's role is allowed to see, so the LLM never even receives restricted documents.

## Architecture

```
Query -> Guardrails Check -> RBAC Filter -> Retrieve from Allowed Collections Only -> LLM -> Grounded Answer
```

1. User submits a question with their role
2. Guardrails check for PII (emails, phones, SSNs) and off-topic keywords (weather, sports, etc.)
3. RBAC filter looks up which document collections the role can access
4. Retrieval runs against only the allowed ChromaDB collections (embedding similarity search)
5. Retrieved chunks + the original question are sent to the LLM (Groq) for a grounded answer
6. The answer is returned along with source collection names

## How to run

### Setup

1. Clone the repo and install dependencies:
```bash
pip install -r requirements.txt
```

2. Get a free API key from https://console.groq.com and create a `.env` file:
```
GROQ_API_KEY=gsk_your_key_here
```

3. Ingest the company documents into ChromaDB:
```bash
python -c "from src.ingest import build_all_collections; build_all_collections()"
```

4. Launch the chatbot:
```bash
streamlit run app.py
```

### Role access map

| Role | Can see collections |
|------|-------------------|
| finance_team | finance, general |
| hr_team | human_resources, general |
| c_level | finance, human_resources, general |
| employee | general |

## Worked examples

### Scenario 1: Employee asks about Q3 revenue (denied)

**Login:** employee
**Question:** "What is our Q3 revenue?"
**Result:** "I don't have access to information that would answer that."

Employees only have access to the "general" collection (company overview). The Q3 revenue data lives in the "finance" collection, which is not retrieved for this role. The LLM never sees the financial data.

### Scenario 2: Finance team asks about Q3 revenue (answered)

**Login:** finance_team
**Question:** "What is our Q3 revenue?"
**Result:** "Our Q3 revenue reached $24.7 million."

The finance_team role has access to both "finance" and "general" collections. The retrieval finds relevant chunks from the Q3 report, and the LLM produces a grounded answer.

### Scenario 3: Off-topic question (blocked)

**Login:** any role
**Question:** "What's the weather today?"
**Result:** "That's outside what I can help with. Please ask about company information."

The guardrails layer detects that "weather" is a blocked topic keyword and returns a warning before any retrieval happens.

### Scenario 4: PII in query (blocked)

**Login:** hr_team
**Question:** "My email is john@acme.com, what is the PTO policy?"
**Result:** "I can't process requests containing personal information."

The guardrails layer detects the email address pattern and blocks the request before any retrieval or LLM call occurs, preventing personal data from reaching the logs.

### Scenario 5: HR team asks about 401k match (answered)

**Login:** hr_team
**Question:** "What is the 401k match policy?"
**Result:** "The company matches 50% of contributions up to 6% of salary."

The hr_team role has access to "human_resources" and "general" collections. The payroll policy document in human_resources contains the 401k details and is retrieved successfully.

### Scenario 6: C-level asks about marketing spend (answered)

**Login:** c_level
**Question:** "How much did we spend on Google Ads?"
**Result:** "We spent $520,000 on Google Ads in Q3."

The c_level role has the broadest access — all three collections. The marketing expenses document in the finance collection contains the Google Ads figure and is retrieved.

### Scenario 7: Finance team asks about PTO policy (denied)

**Login:** finance_team
**Question:** "How many PTO days do employees get?"
**Result:** "I don't have access to information that would answer that."

The finance_team role does not have access to the "human_resources" collection where the employee handbook lives. The retrieval finds nothing relevant, and the request is denied at the retrieval layer.

### Scenario 8: Employee asks about company founding (answered from general)

**Login:** employee
**Question:** "When was Acme Corp founded?"
**Result:** "Acme Corp was founded in 2014 by Sarah Chen and Michael Torres."

Employees only have access to the "general" collection, but the company overview document contains founding details. The retrieval finds a match and the LLM answers correctly.

## What I'd add next

- **Real PII redaction:** The current guardrails only detect PII and block the query entirely. A better approach would be to redact PII tokens from the query (replacing emails with `[REDACTED]`) so legitimate questions that happen to contain personal info can still be answered safely.
- **Hybrid search:** The current retrieval only uses embedding similarity. Adding keyword search (BM25) alongside embeddings would improve precision for exact-match queries like policy names, employee names, or specific dollar amounts.
- **Automated eval suite:** RAG systems are prone to silent regressions when the retrieval logic, chunking strategy, or embedding model changes. An automated evaluation with a set of test questions and expected answers would catch regressions before they reach users.
