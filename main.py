from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import math
from search_engine import search_query  

app = FastAPI()

#serve static files (like index.html)
app.mount("/static", StaticFiles(directory="static"), name="static")

#serve the HTML page
@app.get("/", response_class=HTMLResponse)
def read_root(q: str = "", page: int = 1, page_size: int = 10):
    try:
        # fetching all search results (search_query returns {"total_results":..., "results":[...]})
        search_res = search_query(q)
        results_list = sanitize_data(search_res.get("results", []))
        # calculate start and end indices for pagination
        start = (page - 1) * page_size
        end = start + page_size
        # paginate results
        paginated_results = results_list[start:end]
        # total results count
        total_results = search_res.get("total_results", len(results_list))
 
        return JSONResponse(content={
             "results": paginated_results,
             "total_results": total_results,
             "page": page,
             "page_size": page_size
         })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#function to sanitize the data for invalid values
def sanitize_data(data):
    if isinstance(data, dict):
        return {key: sanitize_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    elif isinstance(data, float) and math.isnan(data):
        return None  #replace NaN with None 
    return data

#Search API endpoint
@app.get("/search")
def search(q: str = Query(..., min_length=1), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1)):
    try:
        # fetching all search results (search_query returns {"total_results":..., "results":[...]})
        search_res = search_query(q)
        results_list = sanitize_data(search_res.get("results", []))
        # calculate start and end indices for pagination
        start = (page - 1) * page_size
        end = start + page_size
        # paginate results
        paginated_results = results_list[start:end]
        # total results count
        total_results = search_res.get("total_results", len(results_list))
 
        return JSONResponse(content={
             "results": paginated_results,
             "total_results": total_results,
             "page": page,
             "page_size": page_size
         })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

