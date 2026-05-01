import os
import pandas as pd
import requests
import json
import time
from typing import List, Dict, Any
from supabase import create_client, Client

# LangChain Imports
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Configuration
# Please set these environment variables or fill them in directly
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "06d9bc9bf85e41a78d3bc36ce9e46b4e.mVj71EDA6f6q53C4")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") # Must be Service Role Key for writing
EXCEL_PATH = "旅游景点.xlsx"
DOCS_DIR = "knowledge_docs"

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

def ingest_excel(file_path: str, supabase: Client):
    """Processes structured Excel data."""
    if not os.path.exists(file_path):
        print(f"Excel file not found at {file_path}, skipping.")
        return

    print(f"Processing Excel: {file_path}")
    try:
        df = pd.read_excel(file_path)
        df = df.fillna("")
        
        print(f"Found {len(df)} rows in Excel.")

        for index, row in df.iterrows():
            # Mapping Chinese columns to variables (modify as needed)
            name = row.get("名称", row.get("name", "Unknown"))
            city = row.get("城市", row.get("city", ""))
            address = row.get("地址", row.get("address", ""))
            intro = row.get("简介", row.get("introduction", ""))
            level = row.get("等级", row.get("level", ""))
            price = row.get("价格", row.get("price", 0))
            rating = row.get("评分", row.get("rating", 0))
            
            content = f"""
景点名称：{name}
位置：{city} {address}
等级：{level}
评分：{rating}
价格：{price}
简介：{intro}
""".strip()

            print(f"Processing Excel Row [{index+1}/{len(df)}]: {name}")
            
            # Check if already exists (optional, simplistic check)
            # res = supabase.table("knowledge_base").select("id").eq("metadata->>name", name).execute()
            # if res.data:
            #     print(f"Skipping {name}, already exists.")
            #     continue

            embedding = get_embedding(content)
            if not embedding:
                print(f"Skipping {name} due to embedding error.")
                continue

            metadata = {
                "name": name,
                "city": city,
                "level": level,
                "price": price,
                "rating": rating,
                "address": address,
                "source": os.path.basename(file_path),
                "type": "excel_row"
            }

            data = {
                "content": content,
                "metadata": metadata,
                "embedding": embedding
            }
            
            try:
                supabase.table("knowledge_base").insert(data).execute()
            except Exception as e:
                print(f"Error inserting {name}: {e}")
            
            time.sleep(0.1) # Rate limit
    except Exception as e:
        print(f"Error processing Excel file: {e}")

def ingest_document(file_path: str, supabase: Client):
    """Processes unstructured documents (PDF, DOCX, TXT)."""
    if not os.path.exists(file_path):
        return

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
        print(f"Unsupported file type: {filename}")
        return

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

        for i, split in enumerate(splits):
            content = split.page_content
            # Combine existing metadata with our custom metadata
            metadata = split.metadata
            metadata["source"] = filename
            metadata["type"] = "document_chunk"
            metadata["chunk_index"] = i
            
            print(f"Processing Chunk [{i+1}/{len(splits)}]...")
            
            embedding = get_embedding(content)
            if not embedding:
                continue

            data = {
                "content": content,
                "metadata": metadata,
                "embedding": embedding
            }

            try:
                supabase.table("knowledge_base").insert(data).execute()
            except Exception as e:
                print(f"Error inserting chunk {i} of {filename}: {e}")
            
            time.sleep(0.1) # Rate limit

    except Exception as e:
        print(f"Error processing document {filename}: {e}")

def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables.")
        return

    print(f"Connecting to Supabase: {SUPABASE_URL}")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 1. Process Excel
    ingest_excel(EXCEL_PATH, supabase)

    # 2. Process Knowledge Docs Directory
    if os.path.exists(DOCS_DIR):
        print(f"Scanning directory: {DOCS_DIR}")
        for root, dirs, files in os.walk(DOCS_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                ingest_document(file_path, supabase)
    else:
        print(f"Directory {DOCS_DIR} not found. Skipping document ingestion.")

    print("Ingestion complete!")

if __name__ == "__main__":
    main()
