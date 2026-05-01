
"""
RAG 服务单例管理
负责在 Django 中初始化和持有 RAG 引擎实例，避免重复加载
"""
import os
import threading
from django.conf import settings

# Lazy import
# from rag_v6 import PersonalizedRAGEngine, load_documents, create_knowledge_base, RAGConfig

class RAGService:
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.engine = None
        self.is_initialized = False
        
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
        return cls._instance
    
    def initialize(self):
        """初始化 RAG 引擎（建议在 Django 启动时调用，或者第一次请求时懒加载）"""
        if self.is_initialized:
            return

        print("[Django] Initializing RAG engine...")
        
        try:
            # 尝试导入 rag_v6
            try:
                from rag_v6 import PersonalizedRAGEngine, load_documents, create_knowledge_base
            except ImportError as e:
                print(f"[Django] Failed to import rag_v6: {e}")
                # 尝试修复路径问题
                import sys
                sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from rag_v6 import PersonalizedRAGEngine, load_documents, create_knowledge_base

            # 知识库路径不再从配置读取文件夹，而是直接指定构建好的向量库路径
            # 即使这里设为空，rag_v6 也会默认去读 "./chroma_db_knowledge"
            KNOWLEDGE_PATH = ""
            
            knowledge_db = None
            db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "chroma_db_knowledge")
            
            # 如果存在预构建的向量库，直接连接
            if os.path.exists(db_dir):
                print("[Django] Found prebuilt vector knowledge base, connecting...")
                try:
                    from langchain_community.vectorstores import Chroma
                    from rag_v6 import _embedding_model

                    # 使用 rag_v6 的单例 embedding 函数
                    embeddings = _embedding_model()
                    knowledge_db = Chroma(persist_directory=db_dir, embedding_function=embeddings)
                    print("[Django] Vector knowledge base connected.")
                except Exception as e:
                    print(f"[Django] Failed to connect vector DB: {e}")
            else:
                print(f"[Django] Prebuilt vector DB not found ({db_dir}), starting without KB.")
                print("[Django] Hint: run `python build_vectordb.py` to build knowledge base.")
            
            # 无论是否有知识库，都初始化引擎
            self.engine = PersonalizedRAGEngine(knowledge_db)
            self.is_initialized = True
            print("[Django] RAG engine initialized.")
            
        except Exception as e:
            print(f"[Django] RAG engine init failed: {e}")
            import traceback
            traceback.print_exc()
            # 即使失败，也创建一个伪造的引擎，防止 500 错误
            self.engine = self._create_dummy_engine(str(e))
            self.is_initialized = True

    def _create_dummy_engine(self, error_message="Unknown"):
        """创建一个哑引擎，用于在初始化失败时提供基本响应"""
        class DummyEngine:
            def __init__(self, error):
                self.error = error
                self.memory = type('obj', (object,), {
                    'get_user_profile': lambda *args: None,
                    'get_personality': lambda *args: type('obj', (object,), {'to_dict': lambda: {}})()
                })
                self.knowledge_db = None
                self.user_id = "default"
                self.profile = None
                self.personality = self.memory.get_personality()
            
            def process_message(self, user_input, *args, **kwargs):
                return f"抱歉，本地 AI 引擎启动失败。错误信息: {self.error}。请检查后台日志或尝试重启服务。"
        
        return DummyEngine(error_message)

    def get_engine(self):
        if not self.is_initialized:
            self.initialize()
        return self.engine

# 全局单例
rag_service = RAGService.get_instance()

# Re-export functions for compatibility with views.py
# But they will fail if imported directly.
# Better to fix views.py to import them lazily too.
def split_documents(*args, **kwargs):
    from rag_v6 import split_documents
    return split_documents(*args, **kwargs)

def create_knowledge_base(*args, **kwargs):
    from rag_v6 import create_knowledge_base
    return create_knowledge_base(*args, **kwargs)

def load_documents(*args, **kwargs):
    from rag_v6 import load_documents
    return load_documents(*args, **kwargs)

def delete_knowledge_collection(*args, **kwargs):
    from rag_v6 import delete_knowledge_collection
    return delete_knowledge_collection(*args, **kwargs)

def list_knowledge_collections(*args, **kwargs):
    from rag_v6 import list_knowledge_collections
    return list_knowledge_collections(*args, **kwargs)
