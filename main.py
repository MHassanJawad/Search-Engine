from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import math
from search_engine import search_query  # Assuming this is your core search function

app = FastAPI()

# Serve static files (like index.html)
app.mount("/static", StaticFiles(directory="static"), name="static")

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

# Search API endpoint
@app.get("/search")
def search(q: str = Query(..., min_length=1)):
    try:
        # Fetch search results from search_query function
        results = search_query(q)

        # Handle case where no results are found
        if isinstance(results, dict) and "message" in results:
            return JSONResponse(content={"results": [], "message": results["message"]})

        # Sanitize results to avoid non-serializable data types
        sanitized_results = sanitize_data(results)

        # Return sanitized results
        return JSONResponse(content={"results": sanitized_results})
    except Exception as e:
        print(f"Error occurred: {str(e)}")  # Debug logging
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
