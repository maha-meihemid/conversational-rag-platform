# Conversational RAG Platform

A production-oriented conversational RAG API for JSON and JSONL question-answer
knowledge bases. It combines LangChain, ChromaDB, multilingual embeddings, Groq,
FastAPI, and persistent session memory.

The platform is domain-independent. Product documentation, support FAQs, internal
policies, educational content, and other Q&A datasets can use the same pipeline
without code changes. The banking dataset is retained only as an optional example.

## Core capabilities

- Generic JSON and JSONL Q&A ingestion
- Deterministic validation, normalization, deduplication, and record identifiers
- Multilingual semantic retrieval with a local embedding model
- ChromaDB persistence and relevance filtering
- Grounded answers generated with Groq through LangChain
- Persistent, isolated conversation memory with SQLite
- Follow-up question rewriting before retrieval
- Configurable assistant profiles with immutable RAG safety rules
- FastAPI endpoints with validated public response models
- Unit and API tests that do not call external model providers

## Architecture

```text
JSON / JSONL knowledge base
            |
            v
Validation and normalization
            |
            v
Embeddings -> ChromaDB
                 |
User -> FastAPI -> LangChain conversation memory
                 |          |
                 |          v
                 |   Standalone question
                 |          |
                 +----------+
                            |
                            v
                    Grounded Groq answer
```

ChromaDB stores knowledge records. SQLite stores chat messages by conversation ID.
These stores have separate responsibilities and can be replaced independently.

## Knowledge-base format

The input must be a JSON array or a JSONL file. `question` and `answer` are required.
`category` and `source` are optional.

```json
[
  {
    "question": "How do I reset my password?",
    "answer": "Open account settings and select Reset password.",
    "category": "Account",
    "source": "Product documentation"
  },
  {
    "question": "How can I contact support?",
    "answer": "Use the support form on the Help page."
  }
]
```

When optional fields are missing, the pipeline uses `General` as the category and
the input filename as the source.

## Local setup

Requirements:

- Python 3.12
- Git

Create and activate the environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
Copy-Item .env.example .env
```

Add a Groq API key to `.env`:

```env
GROQ_API_KEY=your_key_here
```

Never commit `.env` or expose provider credentials to a client application.

## Prepare a knowledge base

There are two supported workflows.

### Option A: prepare a local Q&A dataset

Copy the included generic example:

```powershell
Copy-Item examples/knowledge_base.json data/raw/knowledge_base.json
```

Alternatively, download the original banking example and convert it automatically
to the generic schema:

```powershell
python scripts/download_banking_example.py
```

Normalize and validate the selected input:

```powershell
python scripts/prepare_dataset.py
```

The command creates:

```text
data/processed/knowledge_base.jsonl
data/processed/quality_report.json
```

Custom paths are supported:

```powershell
python scripts/prepare_dataset.py --input path/to/my_knowledge_base.json
```

The input path can point to any local `.json` or `.jsonl` file. The source dataset
does not need to be copied into the repository when `--input` is provided.

### Option B: use an already prepared knowledge base

If the data is already normalized in the platform's processed JSONL format, copy it
directly to:

```text
data/processed/knowledge_base.jsonl
```

Then skip `scripts/prepare_dataset.py` and run the indexing command directly. Each
line must be a JSON object with these fields:

```json
{
  "id": "record_password_reset",
  "category": "Account",
  "question": "How do I reset my password?",
  "answer": "Open account settings and select Reset password.",
  "source": "Product documentation",
  "content": "Question: How do I reset my password?\nAnswer: Open account settings and select Reset password."
}
```

Use Option A when the local dataset contains only Q&A fields. It generates the
identifier and retrieval content automatically and is the safest default.

## Build and inspect the vector store

Create or update the local ChromaDB collection:

```powershell
python scripts/index_knowledge_base.py
```

The first run downloads the multilingual embedding model. Test retrieval without
calling Groq:

```powershell
python scripts/search_knowledge_base.py "How do I reset my password?"
```

## Assistant profile

The system prompt has two layers:

1. Immutable grounding and prompt-injection rules controlled by the application.
2. A use-case profile containing the assistant name, role, domain, tone, language,
   additional instructions, and fallback message.

Default profile values are configured in `.env`. The active profile can be read at:

```text
GET /api/v1/assistant-profile
```

Profile editing is disabled by default. For local administration, set:

```env
ASSISTANT_PROFILE_EDITING_ENABLED=true
```

The future administration interface will update the structured profile through:

```text
PUT /api/v1/assistant-profile
```

The saved profile is stored in `data/assistant_profile.json`. Keep profile editing
disabled on a public deployment unless the endpoint is protected by authentication.

## Conversation memory

LangChain's `RunnableWithMessageHistory` manages the conversation lifecycle, while
`SQLChatMessageHistory` persists messages in `data/conversations.db`. Reuse the same
identifier to continue a session:

```powershell
python scripts/ask.py "How do I track my order?" --conversation-id demo
python scripts/ask.py "How long does it take?" --conversation-id demo
```

Before retrieval, follow-up questions are rewritten as standalone search questions
using recent messages from the same session.

## Chat API

Start the application:

```powershell
uvicorn app.main:app --reload
```

Swagger UI is available at `http://127.0.0.1:8000/docs`.

Send a first message:

```powershell
$response = Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/chat `
  -ContentType "application/json" `
  -Body '{"message":"How do I reset my password?"}'
```

Reuse `$response.conversation_id` to continue the same conversation. The public
response contains only `conversation_id` and `answer`. Retrieval sources, similarity
scores, model reasoning, and provider errors are not exposed.

Clear the session memory:

```powershell
Invoke-RestMethod `
  -Method Delete `
  -Uri "http://127.0.0.1:8000/api/v1/conversations/$($response.conversation_id)"
```

## Verification

```powershell
pytest
ruff check .
mypy app scripts
```

Tests use in-memory histories and dependency overrides. They do not call Groq or
download embedding models.

## Local persistence

The following runtime artifacts are excluded from Git:

- `.env`
- `chroma_db/`
- `data/raw/`
- `data/processed/`
- `data/conversations.db`
- `data/assistant_profile.json`
