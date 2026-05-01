
import sys
print("Testing utils.py imports...")
try:
    from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
    print("Loaders imported.")
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    print("Splitter imported.")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
print("Success.")
