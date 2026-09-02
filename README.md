# Swift News Search Engine

A news information-retrieval project. It builds a forward index plus per-letter
inverted-index **barrels**, then serves BM25-ranked results from FastAPI.

## How it works

- `make_json.py` reads `datasets/data.csv`, tokenizes the article fields, and
  records term frequencies.
- `datasets/barrel_a.json` through `barrel_z.json` map terms to document IDs and
  frequencies. Splitting the inverted index avoids loading the whole index.
- `doc_lengths.json` provides BM25 length normalization; `doc_metadata.json`
  provides result titles, descriptions, links, and images.
- `search_engine.py` loads only needed barrels, calculates BM25, adds a small
  title-match boost, and ranks documents matching any query term.
- `main.py` exposes `/search` and serves the UI under `static/`.

## Run it

Use Python 3.10 or newer:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open <http://127.0.0.1:8000>. API documentation is at
<http://127.0.0.1:8000/docs>.

This workspace already has generated indexes in `datasets/`, so rebuilding is
not required. A first query can take a moment while its barrel is loaded.

## Rebuild the indexes

Put a compatible CSV at `datasets/data.csv`, then run:

```powershell
python make_json.py
```

The full dataset is large, so a rebuild uses substantial RAM, disk, and time.
Test the pipeline first with a small output directory:

```powershell
python make_json.py --limit 100 --output test-index
```

Custom paths are supported with `--data` and `--output`.
