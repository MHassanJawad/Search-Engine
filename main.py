from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from search_engine import search_query
import json

app = FastAPI()

# Serve static files (like index.html)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the HTML page
@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("static/index.html") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# Search API endpoint
@app.get("/search")
def search(q: str = Query(..., min_length=1)):
    results = search_query(q)
    return JSONResponse(content={"results": results})
