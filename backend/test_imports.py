
import sys
import os

print("Starting test...")

try:
    print("Importing langchain...")
    import langchain
    print("Importing chromadb...")
    import chromadb
    print("Importing sentence_transformers...")
    from sentence_transformers import SentenceTransformer
    print("Importing ollama...")
    from langchain_community.llms import Ollama
    
    print("All imports successful.")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
except SystemExit as e:
    print(f"SystemExit: {e}")
    sys.exit(e.code)

print("Test complete.")
