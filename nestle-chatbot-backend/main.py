import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

from scraper import save_to_blob, scrape_website, save_locally
from indexer_service import index_scraped_content
from openai_service import generate_response
from search_service import AzureSearchService
from graphRAG import graph_rag_response

import uvicorn

app = FastAPI()

# CORS Configuration - Allow all origins (adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class ChatRequest(BaseModel):
    message: str


class SearchRequest(BaseModel):
    query: str
    filter: Optional[str] = None


class GraphQuery(BaseModel):
    gremlin: str


@app.post("/scrape")
async def run_scraper():
    try:
        scraped_pages = asyncio.run(scrape_website())
        save_locally(scraped_pages)
        # save_to_blob(scraped_pages)
        return {"status": "success", "message": f"{len(scraped_pages)} pages scraped and saved."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index")
async def run_indexer():
    try:
        index_scraped_content()
        return {"status": "success", "message": "Documents indexed in Azure Search."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def ask_chat(request: ChatRequest):    
    try:
        response = generate_response(request.message)
        
        if response.startswith("Error:"):
            raise HTTPException(
                status_code=400,
                detail=response.replace("Error: ", "")
            )
            
        return {
            "status": "success",
            "response": response,
        }
        
    except HTTPException:
        print(f"HTTPException raised: {str(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )



@app.post("/search")
async def run_search(request: SearchRequest):
    try:
        results = AzureSearchService.search_documents(request.query, request.filter)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graphrag")
async def run_graphrag(request: ChatRequest):
    try:
        response = await graph_rag_response(request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/")
def home():
    return {"message": "Nestlé AI Assistant API is running ✅"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
