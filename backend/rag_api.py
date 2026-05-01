"""
RAG 知识库 API 接口
将本地 RAG 引擎封装为 FastAPI 服务，供前端调用
"""
import os
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import shutil

# 导入我们的 RAG 引擎
from rag_v6 import PersonalizedRAGEngine, load_documents, create_knowledge_base, RAGConfig, UserProfile, split_documents

import django
import sys
from pathlib import Path

# 初始化 Django 环境，以便在 FastAPI 中可以使用 Django 的 Model
# 这样就可以将 RAG 的数据保存到您现有的 MySQL/SQLite 数据库中
django_project_path = Path(__file__).resolve().parent
if str(django_project_path) not in sys.path:
    sys.path.append(str(django_project_path))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lvyou_backend.settings')
django.setup()

# 现在您可以导入您的 Django 模型了，例如：
# from datasource_manager.models import KnowledgeBase

app = FastAPI(title="RAG Knowledge Base API", description="个人私有知识库 v6.0 API")

# 全局变量存储引擎实例
engine = None

class ChatRequest(BaseModel):
    user_input: str
    user_id: str = "default_user"

class ChatResponse(BaseModel):
    response: str
    personality: Dict[str, float]

@app.on_event("startup")
async def startup_event():
    global engine
    
    # 知识库路径（直接指向您的本地文件夹）
    KNOWLEDGE_PATH = r"g:\newlvyouweb\【全国旅游攻略】(1)"
    knowledge_db = None
    
    if os.path.exists(KNOWLEDGE_PATH):
        print(f"📚 正在初始化知识库...")
        # 直接利用 rag_v6.py 的 load_documents 函数
        # 注意：这里可能会花时间，生产环境建议优化为增量加载
        docs = load_documents(KNOWLEDGE_PATH)
        if docs:
            knowledge_db = create_knowledge_base(docs)
            print("✅ 知识库加载完成")
    
    engine = PersonalizedRAGEngine(knowledge_db)
    print("🚀 RAG API 服务启动成功！")

@app.post("/upload_knowledge")
async def upload_knowledge(files: List[UploadFile] = File(...)):
    """
    管理员上传知识库文件接口
    支持批量上传 PDF/Word/TXT
    """
    global engine
    if not engine:
        raise HTTPException(status_code=500, detail="RAG Engine not initialized")
        
    uploaded_count = 0
    new_docs = []
    
    # 定义临时上传目录
    UPLOAD_DIR = "./uploaded_knowledge"
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    try:
        for file in files:
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            
            # 保存文件到本地
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            print(f"📥 接收到文件: {file.filename}")
            
            # 直接使用 rag_v6 的 load_documents
            # 注意：load_documents 内部已经支持了根据后缀名加载
            docs = load_documents(file_path)
            if docs:
                new_docs.extend(docs)
                uploaded_count += 1
                
        if new_docs:
            print(f"🔄 正在更新向量数据库，新增 {len(new_docs)} 个文档片段...")
            
            # 1. 对新文档进行分块
            # 注意：split_documents 需要 List[Document]
            # 我们需要确保 split_documents 在 rag_v6.py 中被正确导入
            # 已经在 rag_api.py 头部导入了 split_documents
            texts = split_documents(new_docs)
            
            # 2. 将新文档添加到现有的 Chroma 数据库中
            if engine.knowledge_db:
                # 增量添加
                # Chroma.add_documents 会自动处理 ID 和持久化
                engine.knowledge_db.add_documents(texts)
                engine.knowledge_db.persist()
                print("✅ 增量更新知识库成功")
            else:
                # 如果之前没有知识库，则创建一个新的
                engine.knowledge_db = create_knowledge_base(new_docs)
                print("✅ 新建知识库成功")
                
        return {"message": f"成功上传并处理了 {uploaded_count} 个文件", "processed_docs": len(new_docs)}
        
    except Exception as e:
        print(f"上传处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天接口
    - user_input: 用户的问题
    - user_id: 用户ID（用于区分不同用户的记忆）
    """
    global engine
    if not engine:
        raise HTTPException(status_code=500, detail="RAG Engine not initialized")
    
    try:
        # 简单处理多用户：这里我们直接根据 user_id 来切换上下文
        # 注意：这只是一个演示性质的实现，生产环境建议使用 session 或连接池
        engine.user_id = request.user_id
        engine.profile = engine.memory.get_user_profile(request.user_id)
        if not engine.profile:
            engine.profile = UserProfile(user_id=request.user_id)
            engine.memory.update_user_profile(request.user_id, engine.profile)
        engine.personality = engine.memory.get_personality(request.user_id)
        
        print(f"收到用户 {request.user_id} 的消息: {request.user_input}")
        response = engine.process_message(request.user_input)
        
        return ChatResponse(
            response=response,
            personality=engine.personality.to_dict()
        )
    except Exception as e:
        print(f"处理消息时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 启动 API 服务，运行在 8000 端口
    # 注意：因为涉及到 RAG 初始化，如果报错可以尝试去掉 reload=True
    uvicorn.run("rag_api:app", host="0.0.0.0", port=8000)
