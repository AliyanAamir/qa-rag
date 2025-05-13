import re
from typing import List, Dict, Any
import tiktoken

from app.config import CHUNK_SIZE, CHUNK_OVERLAP
from langchain.document_loaders import PyPDFLoader

def get_token_count(text: str, encoding_name: str = "cl100k_base") -> int:
    """
    Calculate the number of tokens in the text.
    
    Args:
        text: Input text
        encoding_name: Tokenizer encoding to use
        
    Returns:
        Number of tokens
    """
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    return len(tokens)

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into chunks with specified size and overlap.
    
    Args:
        text: Text to split into chunks
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Overlap between chunks in characters
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
        
 
    chunks = []
    start = 0
    
    while start < len(text):
        
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        
       
        if chunk.strip(): 
            chunks.append(chunk)
            
       
        start = start + chunk_size - chunk_overlap
    
    return chunks

def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace, newlines, etc.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    
    text = re.sub(r'\s+', ' ', text)
    
    
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
  
    text = text.strip()
    
    return text

def extract_metadata(text: str) -> Dict[str, Any]:
    """
    Extract metadata from text if available (e.g., from document headers).
    
    Args:
        text: Text to extract metadata from
        
    Returns:
        Dictionary of metadata
    """
    metadata = {
        "title": None,
        "source": None,
    }
    
  
    lines = text.split('\n')
    if lines and lines[0].strip():
        metadata["title"] = lines[0].strip()
    
    return metadata


def load_split_pdf_file(pdf_file, text_splitter):
    loaded = PyPDFLoader(pdf_file)
    data = loaded.load_and_split(text_splitter)
    return data