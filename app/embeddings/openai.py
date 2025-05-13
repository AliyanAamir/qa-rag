import os
from typing import List, Union
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import OPENAI_API_KEY, EMBEDDING_MODEL

class OpenAIEmbeddings:
    """Wrapper for OpenAI embedding models."""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for a single text using OpenAI's embedding model.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the text embedding
        """
        response = await self.client.embeddings.create(
            model=self.model_name,
            input=text
        )
        return response.data[0].embedding
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a batch.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings, one for each input text
        """
        if not texts:
            return []
        
        response = await self.client.embeddings.create(
            model=self.model_name,
            input=texts
        )
        
        return [item.embedding for item in response.data]