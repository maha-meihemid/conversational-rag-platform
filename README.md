# Banking RAG Assistant

A production-oriented conversational banking assistant powered by a retrieval-
augmented generation pipeline, FastAPI, LangChain, ChromaDB, and Groq models.

## Project status

The project is under active development. The first milestone provides the
application structure, configuration layer, and a minimal health endpoint.

## Prerequisites

- Python 3.12
- Git
- Docker Desktop (optional at this stage)

## Local development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`, and its interactive
documentation is available at `http://127.0.0.1:8000/docs`.

## Verification

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
pytest
```

Add the Groq API key to `.env` when the model integration is implemented. Never
commit this file or expose the API key in source code.
