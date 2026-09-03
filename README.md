# Banking RAG Assistant

A production-oriented conversational banking assistant powered by a retrieval-
augmented generation pipeline, FastAPI, LangChain, ChromaDB, and Groq models.

## Project status

The project is under active development. The first milestone provides the
application structure, configuration layer, and a minimal health endpoint.

## Prerequisites

- Python 3.12
- Git
- Docker

## Local development

```powershell
py -3.12 -m venv .venv
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

## Dataset preparation

The knowledge base uses the public
[Banking FAQ Dataset](https://www.kaggle.com/datasets/rudrakumargupta/banking-faq-dataset-for-chatbot-training)
from Kaggle. Raw and generated data are intentionally excluded from Git.

Download and extract the dataset by running:

```powershell
python scripts/download_dataset.py
```

The source CSV will be placed at:

```text
data/raw/banking-faq-dataset/banking_knowledge_base_1000.csv
```

Then build the normalized JSONL knowledge base:

```powershell
python scripts/prepare_dataset.py
```

The command creates `data/processed/banking_faq.jsonl` and a data-quality report
at `data/processed/quality_report.json`. Each normalized record contains a stable
identifier, category, question, answer, source, and the exact text that will be
embedded during the vector-store ingestion step.

## Vector-store indexing

Install the updated project dependencies after pulling this milestone:

```powershell
pip install -e ".[dev]"
```

Create the local ChromaDB index:

```powershell
python scripts/index_knowledge_base.py
```

The first run downloads the multilingual embedding model. ChromaDB persists the
result under `chroma_db`, which is excluded from Git. Running the indexing command
again updates the same FAQ identifiers instead of creating duplicates.

Test semantic retrieval without calling an LLM:

```powershell
python scripts/search_knowledge_base.py "How can I reset my card PIN?"
```

The query and all FAQ documents are embedded with the same configured model. The
search returns the five closest FAQ records and their relevance scores by default.
