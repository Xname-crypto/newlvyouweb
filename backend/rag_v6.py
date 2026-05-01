"""
Minimal, robust RAG engine used by Django endpoints.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import random
import time


HF_HOME_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hf_cache")
os.environ.setdefault("HF_HOME", HF_HOME_DIR)
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", HF_HOME_DIR)
os.environ.setdefault("TRANSFORMERS_CACHE", os.path.join(HF_HOME_DIR, "hub"))

# Offline-first for restricted networks. Set HF_OFFLINE=0 to allow downloading.
if str(os.getenv("HF_OFFLINE", "1")).lower() in ("1", "true", "yes"):
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


from langchain_core.documents import Document

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except Exception:
    class RecursiveCharacterTextSplitter:  # type: ignore[override]
        def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120, **_: Any):
            self.chunk_size = max(1, int(chunk_size))
            self.chunk_overlap = max(0, int(chunk_overlap))

        def split_documents(self, documents: List[Document]) -> List[Document]:
            out: List[Document] = []
            stride = max(1, self.chunk_size - self.chunk_overlap)
            for doc in documents:
                text = doc.page_content or ""
                if not text:
                    continue
                for i in range(0, len(text), stride):
                    chunk = text[i:i + self.chunk_size]
                    if not chunk:
                        continue
                    out.append(Document(page_content=chunk, metadata=dict(doc.metadata or {})))
                    if i + self.chunk_size >= len(text):
                        break
            return out

try:
    from langchain_community.embeddings import SentenceTransformerEmbeddings
except Exception:
    from langchain_huggingface import HuggingFaceEmbeddings as SentenceTransformerEmbeddings

from langchain_community.vectorstores import Chroma

try:
    from sentence_transformers import CrossEncoder
except Exception:
    CrossEncoder = None  # type: ignore[assignment]


class RAGConfig:
    chunk_size = 800
    chunk_overlap = 120
    k_retrieval = 6
    k_rerank = 4
    persist_directory = "./chroma_db"
    # 使用更轻量的中文 embedding 模型 (约 300MB vs 500MB)
    embedding_model = "shibing624/text2vec-base-chinese"
    # Reranker 已禁用以节省约 1GB 内存
    # 如需启用，改为 "BAAI/bge-reranker-base" 并确保内存充足
    rerank_model = None
    memory_db_path = "./memory.db"


def slugify(text: str) -> str:
    """将字符串转换为合法的 Chroma collection 名称（字母、数字、连字符、下划线）"""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "_", text)
    return text[:64]  # Chroma collection name max 64 chars


def get_collection_name(kb_id: int, kb_name: str = "") -> str:
    """生成 KB 对应的 Chroma collection 名称"""
    if kb_name:
        return f"kb_{kb_id}_{slugify(kb_name)}"
    return f"kb_{kb_id}_default"


# Embedding 模型缓存，支持多配置
_embedding_model_cache: Dict[str, SentenceTransformerEmbeddings] = {}


# 意图判断关键词 - 用于决定是否检索知识库
TRAVEL_KEYWORDS = [
    '景点', '旅游', '攻略', '美食', '酒店', '路线', '自驾', '旅行',
    '门票', '景区', '公园', '博物馆', '古镇', '海滩', '山', '湖',
    '推荐', '规划', '行程', '签证', '航班', '火车', '租车',
    '避坑', '注意', '建议', '好玩', '值得', '最美'
]

TRAVEL_QUESTION_PATTERNS = [
    r'哪里.*好.*', r'哪里.*值得', r'.*景点.*', r'.*推荐.*',
    r'.*怎么去.*', r'.*路线.*', r'.*攻略.*', r'.*美食.*',
    r'.*酒店.*', r'.*住宿.*', r'.*门票.*', r'.*花费.*',
    r'.*天.*行程', r'.*自驾.*', r'.*穷游.*', r'.*周边.*',
]


@dataclass
class UserProfile:
    user_id: str
    name: str = ""
    background: str = ""
    preferences: Dict[str, Any] = None
    interaction_count: int = 0
    last_active: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if self.preferences is None:
            self.preferences = {}
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.last_active:
            self.last_active = now


@dataclass
class Personality:
    warmth: int = 50
    proactivity: int = 70
    humor: int = 30
    patience: int = 50

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


@dataclass
class MemoryEvent:
    session_id: str
    user_input: str
    agent_response: str
    summary: str = ""
    topics: List[str] = None
    importance: float = 1.0
    timestamp: str = ""

    def __post_init__(self) -> None:
        if self.topics is None:
            self.topics = []
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class MemorySystem:
    def __init__(self, db_path: str = RAGConfig.memory_db_path):
        self.db_path = db_path
        self._profiles_fallback: Dict[str, UserProfile] = {}
        self._personality_fallback: Dict[str, Personality] = {}
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
              user_id TEXT PRIMARY KEY,
              payload TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS personalities (
              user_id TEXT PRIMARY KEY,
              payload TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id TEXT,
              payload TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        try:
            conn = self._conn()
            cur = conn.cursor()
            cur.execute("SELECT payload FROM user_profiles WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return self._profiles_fallback.get(user_id)
            data = json.loads(row[0])
            return UserProfile(**data)
        except Exception:
            return self._profiles_fallback.get(user_id)

    def update_user_profile(self, user_id: str, profile: UserProfile) -> None:
        profile.user_id = user_id
        profile.last_active = datetime.now().isoformat()
        payload = json.dumps(asdict(profile), ensure_ascii=False)
        self._profiles_fallback[user_id] = profile
        try:
            conn = self._conn()
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO user_profiles(user_id, payload) VALUES (?, ?)",
                (user_id, payload),
            )
            conn.commit()
            conn.close()
        except Exception:
            return

    def get_personality(self, user_id: str) -> Personality:
        try:
            conn = self._conn()
            cur = conn.cursor()
            cur.execute("SELECT payload FROM personalities WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return self._personality_fallback.get(user_id, Personality())
            return Personality(**json.loads(row[0]))
        except Exception:
            return self._personality_fallback.get(user_id, Personality())

    def update_personality(self, user_id: str, personality: Personality) -> None:
        payload = json.dumps(personality.to_dict(), ensure_ascii=False)
        self._personality_fallback[user_id] = personality
        try:
            conn = self._conn()
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO personalities(user_id, payload) VALUES (?, ?)",
                (user_id, payload),
            )
            conn.commit()
            conn.close()
        except Exception:
            return

    def add_event(self, user_id: str, event: MemoryEvent) -> None:
        try:
            conn = self._conn()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO memory_events(user_id, payload) VALUES (?, ?)",
                (user_id, json.dumps(asdict(event), ensure_ascii=False)),
            )
            conn.commit()
            conn.close()
        except Exception:
            return


class PyPDFLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> List[Document]:
        import pypdf

        out: List[Document] = []
        with open(self.file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    out.append(Document(page_content=text, metadata={"source": self.file_path, "page": i}))
        return out


class Docx2txtLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> List[Document]:
        import docx2txt

        text = docx2txt.process(self.file_path) or ""
        return [Document(page_content=text, metadata={"source": self.file_path})]


class TextLoader:
    def __init__(self, file_path: str, encoding: str = "utf-8"):
        self.file_path = file_path
        self.encoding = encoding

    def load(self) -> List[Document]:
        with open(self.file_path, "r", encoding=self.encoding, errors="ignore") as f:
            text = f.read()
        return [Document(page_content=text, metadata={"source": self.file_path})]


class HTMLLoader:
    """使用 BeautifulSoup 提取 HTML 中的正文文本"""
    def __init__(self, file_path: str, encoding: str = "utf-8"):
        self.file_path = file_path
        self.encoding = encoding

    def load(self) -> List[Document]:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            # bs4 未安装，回退到纯文本读取
            return TextLoader(self.file_path, self.encoding).load()

        with open(self.file_path, "r", encoding=self.encoding, errors="ignore") as f:
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")
        # 移除 script / style / nav / footer 等无关标签
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        # 压缩空行
        text = re.sub(r"\n{3,}", "\n\n", text)
        return [Document(page_content=text, metadata={"source": self.file_path, "type": "html"})]


class PPTLoader:
    """使用 python-pptx 提取 PPT 文字内容"""
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> List[Document]:
        try:
            from pptx import Presentation
        except ImportError:
            return []

        texts = []
        try:
            prs = Presentation(self.file_path)
            for i, slide in enumerate(prs.slides):
                slide_texts = []
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_texts.append(shape.text.strip())
                if slide_texts:
                    texts.append(f"--- Slide {i + 1} ---\n" + "\n".join(slide_texts))
        except Exception:
            return []

        if not texts:
            return []
        full_text = "\n\n".join(texts)
        return [Document(page_content=full_text, metadata={"source": self.file_path, "type": "ppt"})]


def load_documents(file_path: str) -> List[Document]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return PyPDFLoader(file_path).load()
    if ext == ".docx":
        return Docx2txtLoader(file_path).load()
    if ext == ".html" or ext == ".htm":
        return HTMLLoader(file_path).load()
    if ext == ".pptx":
        return PPTLoader(file_path).load()
    if ext in (".txt", ".md", ".csv", ".json"):
        return TextLoader(file_path).load()
    return TextLoader(file_path).load()


def split_documents(documents: List[Document]) -> List[Document]:
    """向后兼容的分割接口，使用全局默认配置"""
    return _split_documents_internal(documents)


# Singleton instances for models (legacy, for backward compatibility)
_embedding_model_instance = None
_reranker_model_instance = None


def _embedding_model(
    embedding_model: str = None,
    quantization: str = "",
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> SentenceTransformerEmbeddings:
    """
    获取 Embedding 模型实例，支持量化配置。

    Args:
        embedding_model: HuggingFace 模型名称，为空则用 RAGConfig 默认值
        quantization: 量化方式，"4bit" / "8bit" / ""（不量化）
        chunk_size: 文本分块大小，为空则用 RAGConfig 默认值
        chunk_overlap: 块重叠大小，为空则用 RAGConfig 默认值
    """
    model_name = embedding_model or RAGConfig.embedding_model
    cache_key = f"{model_name}_q{quantization}"

    if cache_key not in _embedding_model_cache:
        kwargs: Dict[str, Any] = {"model_kwargs": {"local_files_only": True}}

        # 尝试启用 BitsAndBytes 量化（需要 bitsandbytes 库）
        if quantization in ("4bit", "8bit"):
            try:
                from transformers import BitsAndBytesConfig
                quant_config = BitsAndBytesConfig(
                    load_in_4bit=(quantization == "4bit"),
                    load_in_8bit=(quantization == "8bit"),
                )
                kwargs["model_kwargs"]["quantization_config"] = quant_config
            except ImportError:
                pass  # bitsandbytes 未安装，跳过量化

        _embedding_model_cache[cache_key] = SentenceTransformerEmbeddings(
            model_name=model_name,
            **kwargs
        )

    return _embedding_model_cache[cache_key]


def _split_documents_internal(
    documents: List[Document],
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Document]:
    """根据指定配置分割文档"""
    cs = chunk_size if chunk_size is not None else RAGConfig.chunk_size
    co = chunk_overlap if chunk_overlap is not None else RAGConfig.chunk_overlap
    splitter = RecursiveCharacterTextSplitter(chunk_size=cs, chunk_overlap=co)
    return splitter.split_documents(documents)


def create_knowledge_base(
    documents: List[Document],
    collection_name: str = None,
    embedding_model: str = None,
    quantization: str = "",
    chunk_size: int = None,
    chunk_overlap: int = None,
    kb_id: int = None,
    kb_name: str = "",
):
    """
    创建或追加到一个 Chroma collection（向量知识库）。

    Args:
        documents: 原始文档列表
        collection_name: 指定的 collection 名（为空则自动生成）
        embedding_model: 使用的 embedding 模型名
        quantization: 量化方式，"4bit"/"8bit"/""
        chunk_size: 文本块大小
        chunk_overlap: 块重叠大小
        kb_id: 关联的 KB id（用于生成默认 collection 名）
        kb_name: KB 名称（用于生成默认 collection 名）
    """
    if not documents:
        return None

    # 确定 collection 名称
    if not collection_name:
        if kb_id is not None:
            collection_name = get_collection_name(kb_id, kb_name)
        else:
            collection_name = "kb_default"

    chunks = _split_documents_internal(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    if not chunks:
        return None

    # 构造持久化路径：每个 collection 一个子目录
    persist_dir = os.path.join(RAGConfig.persist_directory + "_knowledge", collection_name)
    os.makedirs(persist_dir, exist_ok=True)

    embedding = _embedding_model(
        embedding_model=embedding_model,
        quantization=quantization,
    )

    # 检查 collection 是否已存在（追加场景）
    try:
        existing = Chroma(
            client=chromadb.PersistentClient(path=persist_dir),
            collection_name=collection_name,
            embedding_function=embedding,
        )
        # 追加新文档
        existing.add_documents(documents=chunks)
        existing.persist()
        return existing
    except Exception:
        # 不存在则创建新的
        pass

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embedding,
        persist_directory=persist_dir,
        collection_name=collection_name,
    )
    vectordb.persist()
    return vectordb


def delete_knowledge_collection(collection_name: str) -> bool:
    """删除指定 collection 的所有向量数据（仅删除 Chroma 侧，Django 侧记录由调用方处理）"""
    if not collection_name or collection_name == "kb_default":
        return False
    persist_dir = os.path.join(RAGConfig.persist_directory + "_knowledge", collection_name)
    try:
        if os.path.exists(persist_dir):
            import shutil
            shutil.rmtree(persist_dir)
            return True
    except Exception:
        pass
    return False


def list_knowledge_collections() -> List[str]:
    """列出所有已存在的 KB collection 名称"""
    base_dir = RAGConfig.persist_directory + "_knowledge"
    if not os.path.exists(base_dir):
        return []
    collections = []
    for name in os.listdir(base_dir):
        path = os.path.join(base_dir, name)
        if os.path.isdir(path):
            collections.append(name)
    return collections


def retrieve_knowledge(vectordb, query: str, k: int = 5) -> List[Document]:
    if not vectordb:
        return []
    retriever = vectordb.as_retriever(search_type="mmr", search_kwargs={"k": k, "fetch_k": max(k * 2, 8)})
    return retriever.invoke(query)


def rerank_documents(query: str, documents: List[Document], top_k: int) -> List[Document]:
    """重排序文档，如果禁用 reranker 则直接返回前 top_k 个"""
    global _reranker_model_instance
    if not documents:
        return []
    # 如果 rerank_model 为 None，禁用 reranker
    if RAGConfig.rerank_model is None:
        return documents[:top_k]
    if CrossEncoder is None:
        return documents[:top_k]
    try:
        if _reranker_model_instance is None:
            _reranker_model_instance = CrossEncoder(RAGConfig.rerank_model, local_files_only=True)
        model = _reranker_model_instance
        pairs = [[query, d.page_content] for d in documents]
        scores = model.predict(pairs)
        ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return [d for d, _ in ranked[:top_k]]
    except Exception:
        return documents[:top_k]


def _should_retrieve_knowledge(user_input: str) -> bool:
    """
    判断用户问题是否与旅行相关，需要检索知识库。
    非旅行相关问题直接跳过知识库检索，节省资源和时间。
    """
    import re
    user_lower = user_input.lower()

    # 1. 检测旅行关键词
    for keyword in TRAVEL_KEYWORDS:
        if keyword in user_lower:
            return True

    # 2. 检测问句模式
    for pattern in TRAVEL_QUESTION_PATTERNS:
        if re.search(pattern, user_input):
            return True

    return False


class PersonalizedRAGEngine:
    def __init__(self, knowledge_vectordb=None):
        self.memory = MemorySystem()
        self.knowledge_db = knowledge_vectordb
        self.user_id = "default_user"
        self.profile = UserProfile(user_id=self.user_id)
        self.personality = Personality()

    def _build_prompt(self, user_input: str) -> tuple[str, bool]:
        """
        构建提示词。

        Returns:
            tuple: (prompt, did_retrieve) - 提示词和是否进行了知识检索
        """
        # 意图判断：非旅行问题不检索知识库
        should_retrieve = _should_retrieve_knowledge(user_input)

        if not should_retrieve or not self.knowledge_db:
            return user_input, False

        # 检索知识库
        docs = retrieve_knowledge(self.knowledge_db, user_input, k=RAGConfig.k_retrieval)
        docs = rerank_documents(user_input, docs, top_k=RAGConfig.k_rerank)
        context = "\n\n".join(d.page_content[:1200] for d in docs) if docs else ""

        if context:
            return f"Use the context to answer.\n\nContext:\n{context}\n\nUser: {user_input}", True
        return user_input, False

    def process_message(self, user_input: str, llm=None) -> str:
        uid = self.user_id or "default_user"
        profile = self.memory.get_user_profile(uid)
        if profile is None:
            profile = UserProfile(user_id=uid)
            self.memory.update_user_profile(uid, profile)
        self.profile = profile
        self.personality = self.memory.get_personality(uid)

        prompt, did_retrieve = self._build_prompt(user_input)
        if llm is not None:
            try:
                answer = llm.invoke(prompt) or ""
            except Exception as e:
                answer = f"LLM call failed: {e}"
        else:
            answer = "Model is not configured yet. Please configure an active provider API key."

        self.memory.add_event(
            uid,
            MemoryEvent(
                session_id=uid,
                user_input=user_input,
                agent_response=answer,
                summary=user_input[:120],
            ),
        )
        return answer
