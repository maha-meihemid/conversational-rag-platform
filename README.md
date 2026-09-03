# Banking RAG Assistant

Assistant bancaire conversationnel fondé sur un pipeline RAG, construit avec
FastAPI, LangChain, ChromaDB et les modèles Groq.

## État du projet

Le projet est en cours de construction. Le premier jalon met en place
l'architecture, la configuration et un endpoint de santé minimal.

## Prérequis

- Python 3.12
- Git
- Docker Desktop (optionnel à ce stade)

## Démarrage local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

L'API répond ensuite sur `http://127.0.0.1:8000` et sa documentation sur
`http://127.0.0.1:8000/docs`.

## Vérification

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
pytest
```

La clé Groq devra être placée dans `.env`. Ce fichier ne doit jamais être
commité.
