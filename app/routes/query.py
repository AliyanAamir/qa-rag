from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db_connection import get_async_db
from app.service.rag import RetrievalService, GenerationService


router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    query: str = Field(..., description="Query text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is machine learning?"
            }
        }


class SourceDocument(BaseModel):
    document_id: str
    document_title: str
    similarity_score: float

class ChunkDetail(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    content: str
    similarity_score: float

class SearchResult(BaseModel):
    query: str
    results: List[ChunkDetail]

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceDocument]

@router.post("/search", response_model=SearchResult)
async def search_documents(
    query_req: QueryRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Search for relevant document chunks."""
    retrieval_service = RetrievalService(db)
    result = await retrieval_service.search_documents(query_req.query)
    return result

@router.post("", response_model=QueryResponse)
async def answer_query(
    query_req: QueryRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Answer a query using RAG pipeline."""
    generation_service = GenerationService(db)
    result = await generation_service.answer_query(query_req.query)
    return result