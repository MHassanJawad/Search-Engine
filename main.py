from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import math
from search_engine import search_query  # Assuming this is your core search function
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

# Serve static files (like index.html)
app.mount("/static", StaticFiles(directory="static"), name="static")

class Article(BaseModel):
    article_id: Optional[str] = None
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    author: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    url_to_image: Optional[str] = None
    published_at: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    full_content: Optional[str] = None


# Serve the HTML page
@app.get("/", response_class=HTMLResponse)
def read_root():
    try:
        with open("static/index.html") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found")

# Function to sanitize the data (for NaN or other invalid values)
def sanitize_data(data):
    if isinstance(data, dict):
        return {key: sanitize_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    elif isinstance(data, float) and math.isnan(data):
        return None  # Replace NaN with None or any placeholder you prefer
    return data

@app.get("/search")
def search(q: str = Query(..., min_length=1), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1)):
    try:
        # Fetch search results and total count
        search_result = search_query(q)
        all_results = sanitize_data(search_result["results"])
        total_results = search_result["total_results"]

        # Calculate start and end indices for pagination
        start = (page - 1) * page_size
        end = start + page_size

        # Paginate results
        paginated_results = all_results[start:end]

        return JSONResponse(content={
            "results": paginated_results,
            "total_results": total_results,
            "page": page,
            "page_size": page_size
        })
    except Exception as e:
        print(f"Error occurred: {str(e)}")  # Debug logging
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.post("/add-articles")
def add_article(articles: List[Article]):
    # Iterate over the list of articles and print the data for each one
    for article in articles:
        print("Received article data:", article.dict())
    
    try:
        # Process each article
        for article in articles:
            # Convert Article object to dict
            article_data = article.dict()
            
            from make_json import add_article
            add_article(article_data)

        return {"message": "Articles added successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")