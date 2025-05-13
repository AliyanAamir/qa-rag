from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid
from app.database.db_connection import get_async_db
from app.service.document_service import DocumentService


router = APIRouter(prefix="/documents", tags=["documents"])

class DocumentCreate(BaseModel):
    content: str = Field(..., description="Document content")
    title: Optional[str] = Field(None, description="Document title")
    source: Optional[str] = Field(None, description="Document source")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "This is a sample document about artificial intelligence...",
                "title": "Introduction to AI",
                "source": "AI Handbook"
            }
        }


class DocumentResponse(BaseModel):
    document_id: str
    title: str
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DocumentDetail(DocumentResponse):
    chunk_count:int
    content: str


    


@router.post("/upload-pdf", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf_document(
    file: UploadFile = File(...),
    title: str = None,
    source: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Upload and process a PDF document."""
    document_service = DocumentService(db)
    result = await document_service.create_document_from_pdf(
        pdf_file=file.file,
        filename=file.filename,
        title=title,
        source=source
    )
    return result

@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """Retrieve a specific document by ID with its full content."""
    document_service = DocumentService(db)
    result = await document_service.get_document(str(document_id))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return result

@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db)
):
    """List all documents with pagination."""
    
    document_service = DocumentService(db)
    docs= await document_service.list_documents(skip=skip, limit=limit)
    return docs

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a document and all its chunks."""
    document_service = DocumentService(db)
    success = await document_service.delete_document(str(document_id))
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)