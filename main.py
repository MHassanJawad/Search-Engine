"""FastAPI entry point for the search-engine web application."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from search_engine import IndexDataError, search_query


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Swift News Search")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def read_root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/search")
def search(
    q: str = Query(..., min_length=1, max_length=300),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> dict[str, object]:
    try:
        search_result = search_query(q)
    except IndexDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    results = search_result["results"]
    start = (page - 1) * page_size
    return {
        "results": results[start : start + page_size],
        "total_results": search_result["total_results"],
        "page": page,
        "page_size": page_size,
    }
