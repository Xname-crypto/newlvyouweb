
import os
import time
import requests
from typing import List, Dict, Any
from supabase import create_client, Client
from django.conf import settings

# LangChain Imports - moved to lazy import
# from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configuration (Use Django settings or environment variables)
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "06d9bc9bf85e41a78d3bc36ce9e46b4e.mVj71EDA6f6q53C4")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ZhipuAI Embedding Config
EMBEDDING_URL = "https://open.bigmodel.cn/api/paas/v4/embeddings"
EMBEDDING_MODEL = "embedding-2"

def get_embedding(text: str) -> List[float]:
    """Generates embedding using ZhipuAI API."""
    if not text or not text.strip():
        return None
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ZHIPU_API_KEY}"
    }
    payload = {
        "model": EMBEDDING_MODEL,
        "input": text
    }
    
    try:
        response = requests.post(EMBEDDING_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if "data" in data and len(data["data"]) > 0:
            return data["data"][0]["embedding"]
        else:
            print(f"Error: No embedding data returned. Response: {data}")
            return None
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def process_document(file_path: str):
    """Processes a document file and uploads chunks to Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase credentials not configured.")
    
    # Lazy imports here
    try:
        # Try to import from rag_v6 first (custom robust loaders)
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from rag_v6 import PyPDFLoader, Docx2txtLoader, TextLoader, RecursiveCharacterTextSplitter
    except ImportError:
        try:
            from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError as e:
            print(f"Failed to import LangChain modules: {e}")
            raise e

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    filename = os.path.basename(file_path)
    print(f"Processing Document: {filename}")
    
    loader = None
    if file_path.lower().endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.lower().endswith(".docx"):
        loader = Docx2txtLoader(file_path)
    elif file_path.lower().endswith(".txt"):
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {filename}")

    try:
        docs = loader.load()
        print(f"Loaded {len(docs)} pages/sections from {filename}")

        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "！", "，", " ", ""]
        )
        splits = text_splitter.split_documents(docs)
        print(f"Split into {len(splits)} chunks.")

        results = []
        for i, split in enumerate(splits):
            content = split.page_content
            metadata = split.metadata
            metadata["source"] = filename
            metadata["type"] = "document_chunk"
            metadata["chunk_index"] = i
            
            embedding = get_embedding(content)
            if not embedding:
                continue

            data = {
                "content": content,
                "metadata": metadata,
                "embedding": embedding
            }

            try:
                # Use Supabase client to insert data
                response = supabase.table("knowledge_base").insert(data).execute()
                results.append(f"Chunk {i} uploaded.")
            except Exception as e:
                print(f"Error inserting chunk {i}: {e}")
            
            time.sleep(0.1) # Rate limit

        return f"Successfully processed {len(results)} chunks from {filename}"

    except Exception as e:
        print(f"Error processing document {filename}: {e}")
        raise e
