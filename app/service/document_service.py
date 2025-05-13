from typing import List, Dict, Any, Optional, BinaryIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert
import uuid
import os
import tempfile
from pathlib import Path
from app.utils.text_processings import chunk_text as chunk_sentence

from langchain_community.document_loaders import PyPDFLoader
from app.database.models import Document, DocumentChunk
from app.embeddings.openai import OpenAIEmbeddings
from app.utils.text_processings import clean_text, extract_metadata, chunk_text

class DocumentService:
    """Service for document processing and storage."""
    
    def __init__(self, db: AsyncSession, embeddings: Optional[OpenAIEmbeddings] = None):
        self.db = db
        self.embeddings = embeddings or OpenAIEmbeddings()
    
    async def create_document_from_pdf(self, 
                                      pdf_file: BinaryIO, 
                                      filename: str, 
                                      title: Optional[str] = None, 
                                      source: Optional[str] = None) -> Dict[str, Any]:
        """
        Process, chunk, and store a PDF document with its embeddings.
        
        Args:
            pdf_file: PDF file object
            filename: Original filename
            title: Document title (optional)
            source: Document source (optional)
            
        Returns:
            Dictionary with document information
        """
    
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_file.read())
            temp_path = temp_file.name
        
        try:
           
            loader = PyPDFLoader(temp_path)
            pages = loader.load()
            
            
            content = "\n\n".join([page.page_content for page in pages])
            
           
            cleaned_content = clean_text(content)
            
           
            if not title or not source:
                metadata = extract_metadata(cleaned_content)
                title = title or metadata.get("title") or Path(filename).stem or "Untitled Document"
                source = source or metadata.get("source") or filename
            
           
            document_id = uuid.uuid4()
            document = Document(
                id=document_id,
                title=title,
                source=source
            )
            
            self.db.add(document)
            await self.db.flush()
            
            
            chunks = chunk_sentence(cleaned_content)
            
            
            chunk_embeddings = await self.embeddings.embed_texts(chunks)
            
           
            for i, (chunk_text, embedding) in enumerate(zip(chunks, chunk_embeddings)):
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    content=chunk_text,
                    embedding=embedding
                )
                self.db.add(chunk)
            
            await self.db.commit()
            
            return {
                "document_id": str(document_id),
                "title": title,
                "source": source,
                "chunk_count": len(chunks)
            }
        finally:
           
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document information or None if not found
        """
        query = select(Document).where(Document.id == uuid.UUID(document_id))
        result = await self.db.execute(query)
        document = result.scalars().first()
        
        if not document:
            return None
            
       
        chunks_query = select(DocumentChunk).where(
            DocumentChunk.document_id == uuid.UUID(document_id)
        ).order_by(DocumentChunk.chunk_index)
        
        chunks_result = await self.db.execute(chunks_query)
        chunks = chunks_result.scalars().all()
        
        
        full_content = "\n".join(chunk.content for chunk in chunks)
        
        return {
            "document_id": str(document.id),
            "title": document.title,
            "source": document.source,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
            "chunk_count": len(chunks),
            "content": full_content
        }
    
    async def list_documents(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all documents.
        
        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            
        Returns:
            List of document information
        """
        query = select(Document).offset(skip).limit(limit)
        result = await self.db.execute(query)
        documents = result.scalars().all()
        print(documents)
        return [
            {
                "document_id": str(doc.id),
                "title": doc.title,
                "created_at": doc.created_at,
                "source":doc.source,
                "updated_at": doc.updated_at
            }
            for doc in documents
        ]
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and all its chunks.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if document was deleted, False if not found
        """
        query = select(Document).where(Document.id == uuid.UUID(document_id))
        result = await self.db.execute(query)
        document = result.scalars().first()
        
        if not document:
            return False
            
        await self.db.delete(document)
        await self.db.commit()
        
        return True