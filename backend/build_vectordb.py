import os
import sys
import time
import json
from pathlib import Path
from tqdm import tqdm

# 设置环境变量
os.environ["HF_HOME"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hf_cache")
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 导入必要的库
from rag_v6 import (
    load_documents, 
    split_documents, 
    RAGConfig, 
    SentenceTransformerEmbeddings
)
from langchain_community.vectorstores import Chroma

# 知识库路径
KNOWLEDGE_PATH = r"g:\newlvyouweb\【全国旅游攻略】(1)\全国旅游攻略 国内穷游自驾游旅行地图电子版周边游线路美食指南"
DB_DIR = RAGConfig.persist_directory + "_knowledge"

def get_all_supported_files(directory):
    """获取目录下所有支持的文件（PDF, DOCX, TXT）"""
    supported_extensions = ('.pdf', '.docx', '.txt')
    file_list = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(supported_extensions):
                file_list.append(os.path.join(root, file))
    return file_list

def main():
    print("="*60)
    print("🚀 开始离线构建 RAG 向量知识库")
    print("="*60)
    
    if not os.path.exists(KNOWLEDGE_PATH):
        print(f"❌ 错误：找不到知识库文件夹 {KNOWLEDGE_PATH}")
        return

    # 获取所有文件
    all_files = get_all_supported_files(KNOWLEDGE_PATH)
    total_files = len(all_files)
    print(f"📂 共找到 {total_files} 个支持的文档。")
    
    if total_files == 0:
        return

    # 初始化 Embedder
    print("⏳ 正在加载 Embedding 模型 (本地)...")
    embeddings = SentenceTransformerEmbeddings(model_name=RAGConfig.embedding_model)
    
    # 初始化/连接到 ChromaDB
    print(f"📁 连接/创建 Chroma 数据库: {DB_DIR}")
    vectordb = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
    
    # 加载已处理的文件记录（断点续传）
    progress_file = "build_progress.json"
    processed_files = set()
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                processed_files = set(json.load(f))
            print(f"🔄 发现断点续传记录，已跳过 {len(processed_files)} 个文件。")
        except:
            pass

    # 开始逐个处理文件
    print("\n⚡ 开始逐个处理文档 (单线程，低内存模式)...\n")
    
    successful = 0
    failed = 0
    
    for i, file_path in enumerate(all_files):
        if file_path in processed_files:
            continue
            
        filename = os.path.basename(file_path)
        print(f"[{i+1}/{total_files}] 正在处理: {filename} ...", end=" ")
        
        try:
            # 1. 加载单个文档
            docs = load_documents(file_path)
            if not docs:
                print("⚠️ 跳过 (空内容或格式不支持)")
                continue
                
            # 2. 文本分块
            splits = split_documents(docs)
            
            # 3. 写入向量库
            vectordb.add_documents(documents=splits)
            vectordb.persist()
            
            # 4. 记录进度
            processed_files.add(file_path)
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(list(processed_files), f, ensure_ascii=False)
                
            successful += 1
            print(f"✅ 完成 (提取 {len(splits)} 个片段)")
            
        except Exception as e:
            failed += 1
            print(f"❌ 失败: {str(e)}")
            
        # 强制垃圾回收，防止内存泄漏
        import gc
        gc.collect()
        
        # 稍微休眠一下，给 CPU 散热的时间
        time.sleep(0.5)
        
    print("\n" + "="*60)
    print("🎉 知识库构建任务结束！")
    print(f"📊 总计: {total_files} | 成功新增: {successful} | 失败: {failed} | 已跳过: {len(processed_files) - successful}")
    print("💡 现在你可以安全地启动 Django 后端了，它将瞬间读取这个建好的库。")
    print("="*60)

if __name__ == "__main__":
    main()
