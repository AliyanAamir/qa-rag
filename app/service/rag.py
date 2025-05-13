from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text,bindparam,Integer
from pgvector.sqlalchemy import Vector
from app.database.models import  Query
from app.embeddings.openai import OpenAIEmbeddings
from app.config import TOP_K_RESULTS
from typing import List, Dict, Any, Optional
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
from app.database.models import Query


class RetrievalService:
    """Service for retrieving relevant document chunks."""
    
    def __init__(self, db: AsyncSession, embeddings: Optional[OpenAIEmbeddings] = None):
        self.db = db
        self.embeddings = embeddings or OpenAIEmbeddings()
    
    async def retrieve_relevant_chunks(self, query_text: str, top_k: int = TOP_K_RESULTS) -> List[Dict[str, Any]]:
        """
        Retrieve relevant document chunks for a query.
        
        Args:
            query_text: Query text
            top_k: Number of results to retrieve
            
        Returns:
            List of relevant chunks with similarity scores
        """
        
        query_embedding = await self.embeddings.embed_text(query_text)
        
        
       
        query = Query(
            query_text=query_text,
            embedding=query_embedding
        )
        self.db.add(query)
        await self.db.flush()
        
        
        sql = text("""
    SELECT 
        dc.id, 
        dc.content, 
        dc.document_id,
        d.title as document_title,
        1 - (dc.embedding <=> :query_embedding) as similarity_score
    FROM 
        document_chunks dc
    JOIN
        documents d ON dc.document_id = d.id
    ORDER BY 
        dc.embedding <=> :query_embedding
    LIMIT :top_k
""").bindparams(
    bindparam("query_embedding", type_=Vector(1536)),
    bindparam("top_k", type_=Integer()))
        
        result = await self.db.execute(
            sql, 
            {"query_embedding": query_embedding, "top_k": top_k}
        )
        
        chunks = []
        chunk_ids = []
        
        for row in result:
            chunk_id = row.id
            chunk_ids.append(chunk_id)
            chunks.append({
                "chunk_id": str(chunk_id),
                "document_id": str(row.document_id),
                "document_title": row.document_title,
                "content": row.content,
                "similarity_score": float(row.similarity_score)
            })
        
        
        query.retrieved_chunk_ids = chunk_ids
        await self.db.commit()
        
        return chunks
    
    async def search_documents(self, query_text: str, top_k: int = TOP_K_RESULTS) -> Dict[str, Any]:
        """
        Search for documents based on a query.
        
        Args:
            query_text: Query text
            top_k: Number of results to retrieve
            
        Returns:
            Dictionary with query and retrieved chunks
        """
        chunks = await self.retrieve_relevant_chunks(query_text, top_k)
        
        return {
            "query": query_text,
            "results": chunks
        }
    

class GenerationService:
    """Service for generating answers using retrieved content."""
    
    def __init__(self, db: AsyncSession, retrieval_service: Optional[RetrievalService] = None):
        self.db = db
        self.retrieval_service = retrieval_service or RetrievalService(db)
    
   
    async def generate_answer(self, query_id: str, context_chunks: List[Dict[str, Any]], 
                             model: str = "gpt-4o-mini") -> str:
        """
        Generate an answer using a language model and context.
        
        Args:
            query_id: Query ID
            context_chunks: List of relevant document chunks
            model: Language model to use
            
        Returns:
            Generated answer
        """
       
        context = "\n\n".join([
            f"Document: {chunk['document_title']}\n{chunk['content']}"
            for chunk in context_chunks
        ])
        
       
        messages = [
            {"role": "system", "content": (
                "You are a helpful assistant that answers questions based on the provided context. "
                "Always base your answers on the information in the context. "
                "If you don't know the answer based on the context, say so clearly. "
                "Do not make up information or use knowledge outside of the provided context."
            )},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query_id}"}
        ]
        
        
        response =  openai.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=500,
            temperature=0.5
        )
        
        answer = response.choices[0].message.content.strip()
        
        return answer
    
    async def answer_query(self, query_text: str) -> Dict[str, Any]:
        """
        Answer a query using RAG pipeline.
        
        Args:
            query_text: Query text
            
        Returns:
            Dictionary with query, answer, and retrieved chunks
        """
       
        search_results = await self.retrieval_service.search_documents(query_text)
        chunks = search_results["results"]
        
      
        answer = await self.generate_answer(query_text, chunks)
        
        from sqlalchemy.future import select
        query_stmt = select(Query).order_by(Query.created_at.desc()).limit(1)
        result = await self.db.execute(query_stmt)
        query = result.scalars().first()
        
        if query:
            query.response = answer
            await self.db.commit()
        
        return {
            "query": query_text,
            "answer": answer,
            "sources": [
                {
                    "document_id": chunk["document_id"],
                    "document_title": chunk["document_title"],
                    "similarity_score": chunk["similarity_score"]
                }
                for chunk in chunks
            ]
        }
