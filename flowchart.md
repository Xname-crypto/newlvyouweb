# 旅游网站项目架构流程图

```mermaid
flowchart LR
    subgraph frontend["前端 (Vue.js)"]
        direction TB
        subgraph user["用户界面"]
            home["首页"]
            train["车票查询"]
            about["关于我们"]
        end
        subgraph community["社区模块"]
            posts["帖子浏览/发布"]
            assistant["AI助手"]
            profile["个人信息"]
        end
        subgraph auth["登录注册"]
            login["登录/注册"]
            forgot["找回密码"]
        end
        subgraph admin["管理界面"]
            dashboard["仪表盘"]
            user_mgr["用户管理"]
            api_mgr["API配置"]
            kb_mgr["知识库"]
        end
    end

    subgraph backend["后端 (Django)"]
        direction TB
        api["API网关"]
        auth_mod["认证模块"]
        rag["RAG服务"]
        llm_route["LLM路由"]
        crawl["爬虫模块"]
    end

    subgraph data["数据层"]
        mysql[("MySQL")]
        chroma[("ChromaDB")]
        supa[("Supabase")]
    end

    subgraph external["外部服务"]
        ollama(("Ollama"))
        openai(("OpenAI"))
        zhipu(("智谱AI"))
        geo(("地理API"))
        weather(("天气API"))
        train_api(("12306"))
    end

    user --> api
    community --> api
    assistant --> rag
    login --> auth_mod
    admin --> api

    api --> auth_mod
    api --> rag
    api --> crawl

    rag --> llm_route
    llm_route --> ollama
    llm_route --> openai
    llm_route --> zhipu
    llm_route --> geo
    llm_route --> weather

    crawl --> train_api
    crawl --> mysql
    rag --> chroma

    auth_mod --> mysql
    auth_mod --> supa
    api --> mysql

    style frontend fill:#FFF3E0,stroke:#FF9800
    style backend fill:#E8F5E9,stroke:#4CAF50
    style data fill:#F3E5F5,stroke:#9C27B0
    style external fill:#FFEBEE,stroke:#F44336
```

## 架构说明

### 前端层 (Vue.js) 🟠
| 模块 | 功能 |
|------|------|
| 用户界面 | 首页、车票查询、关于我们 |
| 社区模块 | 帖子浏览/发布、AI助手、个人信息 |
| 登录注册 | 登录/注册、找回密码 |
| 管理界面 | 仪表盘、用户管理、API配置、知识库 |

### 后端层 (Django) 🟢
| 模块 | 功能 |
|------|------|
| API网关 | 路由分发 |
| 认证模块 | 用户认证 |
| RAG服务 | 检索增强生成 |
| LLM路由 | 多模型路由选择 |
| 爬虫模块 | 数据爬取 |

### 数据层 🟣
| 存储 | 用途 |
|------|------|
| MySQL | 业务数据存储 |
| ChromaDB | 向量数据库（RAG） |
| Supabase | 认证服务 + 文件存储 |

### 外部服务 🔴
| 类型 | 提供商 |
|------|--------|
| LLM | Ollama(本地)、OpenAI、智谱AI |
| 信息API | 地理API、天气API |
| 数据源 | 12306火车票 |
