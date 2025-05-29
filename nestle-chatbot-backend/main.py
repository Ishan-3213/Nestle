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

# Initialize FastAPI app
app = FastAPI()

# Configure CORS (Cross-Origin Resource Sharing)
# Allow all origins, headers, and methods – modify in production for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Request Models for API Endpoints
# -------------------------------

class ChatRequest(BaseModel):
    """Request body model for chat endpoint."""
    message: str


class SearchRequest(BaseModel):
    """Request body model for Azure Cognitive Search query."""
    query: str
    filter: Optional[str] = None  # Optional filter condition


class GraphQuery(BaseModel):
    """Request body model for GraphRAG gremlin query."""
    gremlin: str


# -------------------------------
# API Endpoints
# -------------------------------

@app.post("/scrape")
async def run_scraper():
    """
    Endpoint to scrape the 'Made With Nestlé' website.
    Saves scraped content locally (and optionally to Azure Blob).
    """
    try:
        scraped_pages = asyncio.run(scrape_website())
        save_locally(scraped_pages)
        # save_to_blob(scraped_pages)  # Optional: Uncomment to enable Azure Blob upload
        return {
            "status": "success",
            "message": f"{len(scraped_pages)} pages scraped and saved."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index")
async def run_indexer():
    """
    Endpoint to index previously scraped content into Azure Cognitive Search.
    """
    try:
        index_scraped_content()
        return {
            "status": "success",
            "message": "Documents indexed in Azure Search."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def ask_chat(request: ChatRequest):    
    """
    Endpoint to interact with the chatbot (NestleBOT) using OpenAI GPT model.
    Keeps track of chat history and appends user/assistant messages.
    """
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
        # FastAPI will re-raise this
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )


@app.post("/search")
async def run_search(request: SearchRequest):
    """
    Endpoint to search Azure Cognitive Search index for matching content.
    Returns ranked search results.
    """
    try:
        results = AzureSearchService.search_documents(request.query, request.filter)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graphrag")
async def run_graphrag(request: ChatRequest):
    """
    Endpoint for Graph-based Retrieval-Augmented Generation (GraphRAG).
    Executes vector + graph-enhanced search logic with OpenAI.
    """
    try:
        response = await graph_rag_response(request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def home():
    """
    Root health check endpoint for the API.
    """
    return {"message": "Nestlé AI Assistant API is running ✅"}


# -------------------------------
# Local Development Entry Point
# -------------------------------

if __name__ == "__main__":
    # Run FastAPI app with Uvicorn server (hot-reload enabled)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
