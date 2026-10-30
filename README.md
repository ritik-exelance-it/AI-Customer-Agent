# AI Customer Support & Resolution Agent

A local customer-support assistant built with Streamlit, LangGraph, LangChain,
and SQLite. It answers support questions using local knowledge files, can look
up demo customers and tickets, optionally searches the public web, stores chat
history, and records requests that need human review.

This is a learning and portfolio prototype, not a production customer-service
system. Read [Security and limitations](#security-and-limitations) before using
real customer data or exposing it to a network.

## What it can do

- Answer customer-support questions about products, policies, and troubleshooting using Markdown and text documents in `knowledge_base/`.
- Show source filenames for knowledge-base answers.
- Look up customers by ID or name, retrieve support tickets, and list tickets belonging to a customer.
- Create support tickets through the Streamlit ticket form with explicit user confirmation.
- Validate ticket subjects, descriptions, priorities, and customer IDs before creating tickets.
- Record ticket creation and authorized status updates in the audit log.
- Optionally search the public web using Tavily.
- Store conversations and LangGraph checkpoints in local SQLite databases.
- Record requests that need human review.
- Decline clearly unrelated questions using a support-scope check.

Ticket creation is handled through the application service and repository. Ticket status changes require explicit authorization; the AI assistant should not be treated as an authentication or authorization mechanism.

## Requirements

- Windows, macOS, or Linux.
- Python 3.12 recommended. Python 3.11 may work, but the dependencies should be
  installed and tested in the environment you plan to use.
- A chat-model API key for the selected provider.
- Internet access for model calls and (optionally) web search.

The app and tests have also run in a Python 3.14 environment, but installed
LangChain/Pydantic dependencies emit compatibility warnings there. Use Python
3.12 for the most predictable setup.

## Quick start (Windows PowerShell)

Run commands from the project root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and set `OPENROUTER_API_KEY` (the default provider), then initialize
the database:

```powershell
python init_db.py --seed-demo-data
```

Start the app:

```powershell
streamlit run app.py
```

Open the local URL printed by Streamlit, usually <http://localhost:8501>.
To run tests:

```powershell
python -m pytest -q
```

The first request requiring a model may take longer than a local greeting or
scope refusal because it makes a network request. Provider availability and
model latency are outside this app's control.

### macOS/Linux quick start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
# Add your API key to .env, then initialize and run:
python init_db.py --seed-demo-data
streamlit run app.py
```

## Configuration

Settings are loaded from the project-root `.env` file and environment variables.
Environment variables take precedence. Restart Streamlit after changing
configuration.

| Variable | Default | Purpose |
|---|---|---|
| `MODEL_PROVIDER` | `openrouter` | Provider: `openrouter`, `openai`, `anthropic`, or `google_genai`. |
| `MODEL_NAME` | `nvidia/nemotron-3.5-super-vl:free` | Provider-specific model identifier. Change it when changing providers. |
| `MODEL_TEMPERATURE` | `0` | Sampling temperature from 0 to 2. |
| `MODEL_TIMEOUT_SECONDS` | `45` | Request timeout in seconds. |
| `MODEL_MAX_RETRIES` | `0` | Model request retries. Increase only if you accept longer waits. |
| `OPENROUTER_API_KEY` | unset | Required when `MODEL_PROVIDER=openrouter`. |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter-compatible API base URL. |
| `OPENAI_API_KEY` | unset | Required when `MODEL_PROVIDER=openai`. |
| `ANTHROPIC_API_KEY` | unset | Required when `MODEL_PROVIDER=anthropic`. |
| `GOOGLE_API_KEY` | unset | Required when `MODEL_PROVIDER=google_genai`. |
| `TAVILY_API_KEY` | unset | Optional; enables public web search. |
| `LANGSMITH_TRACING` | `false` | Optional tracing. Review privacy implications before enabling. |
| `LANGSMITH_API_KEY` | unset | Optional LangSmith API key. |
| `LANGSMITH_PROJECT` | `ai-customer-support` | LangSmith project name. |
| `LANGSMITH_ENDPOINT` | LangSmith default endpoint | LangSmith API endpoint. |
| `DATABASE_PATH` | `storage/support.db` | SQLite database for customers, tickets, conversations, and escalations. |
| `CHECKPOINT_PATH` | `storage/checkpoints.sqlite` | SQLite database for LangGraph checkpoints. |
| `SUPPORT_CHECKPOINT_DB_PATH` | unset | Legacy checkpoint-path override; if set, takes precedence over `CHECKPOINT_PATH`. |

For another provider, edit `.env`, for example:

```dotenv
MODEL_PROVIDER=openai
MODEL_NAME=gpt-4o-mini
OPENAI_API_KEY=your-key-here
```

Use the model identifier supported by your provider/account. Do not put an API
key in source code, screenshots, issue reports, or a committed file. `.env` is
ignored by Git; `.env.example` is safe to share because its keys are blank.

`APP_NAME`, `APP_ENV`, `DEBUG`, `OPENROUTER_SITE_URL`,
`OPENROUTER_APP_NAME`, and `VECTOR_STORE_PATH` are currently present in
configuration but are not used to control the active UI/model/retrieval
behavior. Retrieval currently scans knowledge files directly; no vector
database is created.

## Using the customer interface

1. Optionally enter a known ID in **Customer ID** before starting the
   conversation. The first conversation is created when the page loads; to
   change the association later, enter the ID and click **New conversation**.
2. Ask a support question. Provide a ticket or customer ID when relevant.
3. Use **New conversation** to start a separate chat.

The customer ID associates a conversation with a local record; it is not
identity verification and does not authorize access to real customer data.
This demo can answer billing-policy questions, but it is not connected to
billing statements and cannot display or send bills.

Conversations are stored in SQLite, but the current UI does not provide a past
conversation browser or an admin dashboard. Greetings and clearly out-of-scope
requests are answered locally. A name or ID supplied after a support-related
clarification is treated as part of that support request. Other support
requests requiring an answer go to the configured model. The activity panel
reports workflow stages, not live model tokens.

## Adding knowledge-base documents

1. Add UTF-8 `.md` or `.txt` files under `knowledge_base/`. Nested folders are
   supported.
2. Use clear headings and concise, accurate support instructions. Remove
   secrets and personal/customer data unless you have approval to use it.
3. Ask a related question in the app. Files are loaded and searched at request
   time, so there is no separate indexing command or restart required.

The retriever uses lexical BM25-style scoring with title/phrase boosts. It is
not embedding/semantic retrieval; wording that differs significantly from a
document may not match. Sources identify the relative filename in
`knowledge_base/`. Supported file types are `.md` and `.txt`; PDF, Word, and
image files are not currently indexed.

Knowledge files in `knowledge_base/` are intended to be project content and
may be included in a Git submission. Keep private or customer-specific
documents under `knowledge_base/private/` or
`knowledge_base/customer_data/`; these paths are Git-ignored but still read by
the app. Never store credentials in the knowledge base.

## Customer and ticket data

### Fictional demo records

`python init_db.py` creates the schema without adding customers. To add
fictional sample records:

```powershell
python init_db.py --seed-demo-data
```

The seed operation is safe to repeat: it inserts the built-in records only when
their IDs do not already exist. The demo IDs are:

| Customer ID | Demo name | Ticket IDs |
|---|---|---|
| `CUST-1001` | Alex Morgan | `TICK-2001`, `TICK-2002` |
| `CUST-1002` | Jordan Lee | `TICK-2003` |
| `CUST-1003` | Taylor Smith | none |

These are fictional examples. The UI and tools only find records that exist in
the configured database.

### Adding your own local test records

There is no customer CSV importer or customer-management UI. For a local demo,
you can insert records with Python using the repository's connection helper.
Run this in PowerShell from the project root after installing dependencies:

```powershell
@'
from datetime import datetime, timezone
from config import get_settings
from database.connection import get_connection

now = datetime.now(timezone.utc).isoformat()
with get_connection(get_settings().database_path) as connection:
    connection.execute(
        """INSERT INTO customers
           (customer_id, full_name, email, account_status, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        ("CUST-9001", "Demo Customer", "demo@example.test", "active", now),
    )
    connection.execute(
        """INSERT INTO support_tickets
           (ticket_id, customer_id, subject, description, status, priority,
            created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("TICK-9001", "CUST-9001", "Example support request",
         "Fictional test data.", "open", "medium", now, now),
    )
print("Inserted fictional local demo records.")
'@ | python -
```

Use unique IDs. `account_status` must be `active`, `inactive`, or `suspended`.
Ticket `status` must be `open`, `in_progress`, `resolved`, or `closed`;
`priority` must be `low`, `medium`, `high`, or `urgent`. A ticket must refer to
an existing customer. Use fictional data; this prototype does not provide
authentication, data import validation, or production access controls.

To customize the built-in seed data, edit the fictional rows in
`database/schema.py` before running the seed command. Existing IDs are not
overwritten by seeding; edit records through your local database tool or use
new IDs.

## Local storage, persistence, and backup

By default, the app creates `storage/` and its SQLite files when they are
needed. You can override the file locations in `.env`:

```dotenv
DATABASE_PATH=storage/support.db
CHECKPOINT_PATH=storage/checkpoints.sqlite
```

For another location, use an absolute path appropriate to your operating
system. The parent directory is created automatically. The application database
contains customer/ticket demo data, chat transcripts, escalation records, and
audit entries. The checkpoint database contains LangGraph conversation state.
The files are separate and both are needed for a complete local backup. If
either path is outside `storage/`, back up that file and its SQLite sidecars as
well.

Stop Streamlit before copying or moving the SQLite files. Keep the whole
`storage/` directory backed up and private. `storage/`, SQLite files, and their
WAL/SHM sidecars are ignored by Git; do not remove or commit active database
files.

## Docker (optional)

Build from the project root:

```powershell
docker build -t ai-customer-support .
docker run --rm -p 8501:8501 `
  -e "OPENROUTER_API_KEY=$env:OPENROUTER_API_KEY" `
  -v support_storage:/app/storage `
  ai-customer-support
```

Set `$env:OPENROUTER_API_KEY` before running, or pass the key for whichever
provider is configured. Add `-e TAVILY_API_KEY=...` only if you want web search.
The named Docker volume preserves SQLite data when the container is replaced.
Do not bake `.env` or secrets into the image. For a persistent non-Docker setup,
back up the storage directory as described above.

## Troubleshooting

- **Missing API key:** confirm `MODEL_PROVIDER` and the matching provider key
  are set in `.env`; restart Streamlit after changing them.
- **Slow or failed model answer:** check internet access, provider/model
  availability, account limits, and the configured model ID. `MODEL_TIMEOUT_SECONDS`
  is in seconds; retries default to zero to avoid long retry backoffs.
- **No customer or ticket result:** initialize the database, seed demo data if
  appropriate, and use an ID present in the configured database.
- **Knowledge answer has no source or is not relevant:** make sure the document
  is UTF-8 `.md` or `.txt`, under `knowledge_base/`, and contains terms related
  to the question.
- **Web search unavailable:** set `TAVILY_API_KEY`; web search is optional.
- **Import/dependency errors:** activate the project virtual environment and
  run `python -m pip install -r requirements.txt`.
- **Resetting local data:** back up first. Stop the app before replacing or
  deleting SQLite databases; deleting them erases local conversations and
  checkpoints. Re-run `python init_db.py --seed-demo-data` to create a fresh
  fictional demo database.

## Tests

Run the full test suite from the project root:

```powershell
python -m pytest -q
```

Tests cover workflow routing, retrieval, tool behavior, grounding, web-search
configuration, and model configuration. Most external-model behavior is tested
with mocks; a passing test suite does not guarantee that an external provider is
available.

## Project layout

```text
agents/          Prompts and model tool registry
database/        SQLite connections, schema, and repositories
graph/           LangGraph nodes, routing, state, and checkpointing
knowledge/       Markdown/text loading and lexical retrieval
knowledge_base/  Support documents used by retrieval
middleware/      Input, scope, and escalation policies
services/        Conversation, chat, and escalation orchestration
storage/         Local SQLite databases (generated; Git-ignored)
tests/           Automated tests
tools/           Customer, ticket, knowledge, and web-search tools
ui/              Streamlit presentation components
app.py           Streamlit entry point
config.py        Environment/.env settings
init_db.py       Database initialization and optional demo seeding
model.py         Provider-specific chat model factory
```

## Security and limitations

- A customer ID is an identifier, not proof of identity. Never expose this
  unauthenticated demo publicly with real customer data.
- Use fictional data only. SQLite files and knowledge files can contain
  sensitive information; keep them private and out of public repositories.
- Human escalation creates a pending database record; it does not notify or
  assign a representative.
- The model can produce incorrect responses. Knowledge citations do not prove
  that every sentence is supported; review answers before relying on them.
- The support-scope pre-check is keyword-based and can have false positives or
  false negatives. Adjust `SUPPORT_SCOPE_PATTERNS` in
  `middleware/policies.py` for your support domain.
- Web pages and retrieved files are untrusted input. Keep API keys and
  authorization decisions outside model prompts and tool output.
- LangSmith tracing can transmit prompts and traces to an external service.
  Leave it disabled unless you have reviewed privacy, retention, and access.
- The local lexical retriever scans files at query time and is not suitable for
  a large knowledge corpus without further performance work.
- There is no production authentication, role management, multi-tenant
  isolation, backup automation, or confirmed human-notification integration.

Before any real deployment, add authentication and authorization, validate
customer ownership server-side, review privacy/retention requirements, secure
secret delivery, and test deployment backups and recovery.
