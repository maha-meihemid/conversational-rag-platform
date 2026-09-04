# Data directory

Runtime data is excluded from version control. The platform expects a generic JSON
or JSONL Q&A source at `data/raw/knowledge_base.json` by default.

Required fields:

- `question`
- `answer`

Optional fields:

- `category`
- `source`

Use `examples/knowledge_base.json` as a minimal template. Run the preparation and
indexing pipeline from the repository root:

```powershell
python scripts/prepare_dataset.py
python scripts/index_knowledge_base.py
```

For a dataset stored elsewhere on the local machine, keep it in place and pass its
path directly:

```powershell
python scripts/prepare_dataset.py --input C:\path\to\knowledge_base.json
```

If a knowledge base already uses the platform's processed JSONL schema (`id`,
`category`, `question`, `answer`, `source`, and `content`), place it directly at
`data/processed/knowledge_base.jsonl`. In that case, skip preparation and run only
`python scripts/index_knowledge_base.py`.

Generated knowledge records and reports are written to `data/processed`. Persistent
conversation memory and the editable assistant profile are also stored under `data`.
