
import os
import sys
import time

print("Starting RAG test...")
start_time = time.time()

try:
    from rag_v6 import PersonalizedRAGEngine, RAGConfig
    
    # Disable vector DB for quick test if possible, or use empty
    print(f"Imported rag_v6 in {time.time() - start_time:.2f}s")
    
    print("Initializing Engine...")
    engine = PersonalizedRAGEngine(knowledge_vectordb=None)
    print(f"Engine initialized in {time.time() - start_time:.2f}s")
    
    print("Sending test message...")
    response = engine.process_message("你好")
    print(f"Response: {response}")
    print(f"Total time: {time.time() - start_time:.2f}s")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
