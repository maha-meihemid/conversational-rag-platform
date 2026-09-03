# Data directory

This directory contains local source data and generated artifacts. Dataset files
are excluded from version control; only this documentation and placeholder files
are tracked.

## Source

- Dataset: Banking FAQ Dataset for NLP, RAG & Chatbot Dev
- Author: Rudra Kumar Gupta
- Kaggle version: 4
- License: MIT
- Source file: `banking_knowledge_base_1000.csv`
- Expected columns: `Section`, `Question`, `Answer`

Download the source CSV from the repository root:

```powershell
python scripts/download_dataset.py
```

The script places it at:

```text
data/raw/banking-faq-dataset/banking_knowledge_base_1000.csv
```

Run `python scripts/prepare_dataset.py` from the repository root to validate and
normalize it. Generated files are written to `data/processed`.
