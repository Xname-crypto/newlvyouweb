import os
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse
import ipaddress

import requests
from supabase import create_client


def _get_supabase_client():
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


def _safe_get(d: Any, *path: str):
    cur = d
    for p in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


def _normalize_provider_type(value: Any) -> str:
    v = str(value or "").strip().lower()
    aliases = {
        "openai": "openai_compat",
        "openai-compatible": "openai_compat",
        "openai_compat": "openai_compat",
        "compat": "openai_compat",
        "ollama": "ollama",
        "local": "ollama",
        "zhipu": "zhipu",
        "glm": "zhipu",
        "spark": "spark",
        "xfyun": "spark",
        "xunfei": "spark",
    }
    return aliases.get(v, "")


def _is_local_base_url(base_url: str) -> bool:
    url = (base_url or "").strip()
    if not url:
        return False
    try:
        parsed = urlparse(url if "://" in url else f"http://{url}")
    except Exception:
        return False
    host = (parsed.hostname or "").strip().lower()
    if not host:
        return False
    if host in {"localhost", "127.0.0.1", "::1", "host.docker.internal"}:
        return True
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_loopback or ip.is_private
    except ValueError:
        return host.endswith(".local")


def _infer_provider_kind(provider_name: str, base_url: str) -> str:
    n = (provider_name or "").lower()
    b = (base_url or "").lower()
    if "ollama" in n or "11434" in b:
        return "ollama"
    if "spark" in n or "星火" in provider_name or "xf-yun" in b:
        return "spark"
    if "zhipu" in n or "智谱" in provider_name or "bigmodel" in b or "glm" in n:
        return "zhipu"
    return "openai_compat"


def _infer_default_model(provider_name: str, kind: str) -> str:
    name = provider_name or ""
    if kind == "zhipu":
        if "Plus" in name or "plus" in name:
            return "glm-4-plus"
        if "Air" in name or "air" in name:
            return "glm-4-air"
        return "glm-4-flash"
    if kind == "spark":
        if "Ultra" in name or "ultra" in name:
            return "4.0Ultra"
        return "lite"
    if kind == "openai_compat":
        if "DeepSeek" in name or "deepseek" in name:
            return "deepseek-chat"
        return "gpt-4o-mini"
    return "qwen2.5:7b"


def _infer_default_base_url(provider_name: str, kind: str) -> str:
    if kind == "zhipu":
        return "https://open.bigmodel.cn/api/paas/v4"
    if kind == "spark":
        return "https://spark-api-open.xf-yun.com/v1"
    if kind == "ollama":
        return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    if "DeepSeek" in (provider_name or "") or "deepseek" in (provider_name or "").lower():
        return os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    return os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")


def _infer_default_api_key(provider_name: str, kind: str) -> Optional[str]:
    if kind == "zhipu":
        return os.getenv("ZHIPU_API_KEY")
    if kind == "spark":
        return os.getenv("SPARK_LITE_APIPASSWORD") or os.getenv("SPARK_API_PASSWORD")
    if kind == "openai_compat":
        if "DeepSeek" in (provider_name or "") or "deepseek" in (provider_name or "").lower():
            return os.getenv("DEEPSEEK_API_KEY")
        return os.getenv("OPENAI_API_KEY")
    return None


def fetch_api_provider(provider_id: str) -> Optional[Dict[str, Any]]:
    supabase = _get_supabase_client()
    if not supabase:
        return None
    resp = supabase.from_("api_providers").select("*").eq("id", provider_id).limit(1).execute()
    data = getattr(resp, "data", None)
    if not data:
        return None
    return data[0]


class ChatLLM:
    def invoke(self, prompt: str) -> str:
        raise NotImplementedError()


class ZhipuChatLLM(ChatLLM):
    # 智谱 API 超时 120s（网络较慢时需要更长等待）
    TIMEOUT = 120

    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def invoke(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        url = f"{self.base_url}/chat/completions"
        resp = requests.post(url, headers=headers, json=payload, timeout=self.TIMEOUT)
        if resp.status_code != 200:
            return f"API Error: HTTP {resp.status_code} - {resp.text}"
        data = resp.json()
        return (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""


class OpenAICompatChatLLM(ChatLLM):
    # OpenAI 兼容 API 超时 60s
    TIMEOUT = 60

    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def _endpoint(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        if self.base_url.endswith("/v1"):
            return f"{self.base_url}/chat/completions"
        if self.base_url.endswith("/v1/"):
            return f"{self.base_url}chat/completions"
        return f"{self.base_url}/v1/chat/completions"

    def invoke(self, prompt: str) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        resp = requests.post(self._endpoint(), headers=headers, json=payload, timeout=self.TIMEOUT)
        if resp.status_code != 200:
            return f"API Error: HTTP {resp.status_code} - {resp.text}"
        data = resp.json()
        return (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""


class OllamaChatLLM(ChatLLM):
    # Ollama 本地模型超时 180s（7B 模型加载慢，5GB 内存环境下可能更慢）
    TIMEOUT = 180

    def __init__(self, model: str, base_url: str):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def invoke(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 2048,  # 减少上下文，降低内存占用
                "num_thread": 4,  # 限制线程数，避免资源争抢
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.TIMEOUT)
        except requests.Timeout:
            return "抱歉，AI 回答超时了（本地模型响应过慢）。您可以稍后再试，或联系管理员检查模型服务状态。"
        except requests.ConnectionError:
            return "抱歉，无法连接到本地 AI 模型服务。请确认 Ollama 服务已启动。"
        except Exception as e:
            return f"抱歉，AI 服务遇到问题：{str(e)}"
        if resp.status_code != 200:
            return f"API Error: HTTP {resp.status_code} - {resp.text}"
        data = resp.json()
        return data.get("response", "") or ""


class FallbackChatLLM(ChatLLM):
    """级联 LLM：主模型失败时自动降级到备用模型"""

    def __init__(self, primary: ChatLLM, fallback: ChatLLM, meta: Dict[str, Any]):
        self.primary = primary
        self.fallback = fallback
        self.meta = meta

    def invoke(self, prompt: str) -> str:
        try:
            result = self.primary.invoke(prompt)
            # 如果返回的是错误信息，尝试 fallback
            if result.startswith("API Error:") or "timeout" in result.lower() or "error" in result.lower():
                self.meta["fallback_used"] = True
                return self.fallback.invoke(prompt)
            return result
        except Exception as e:
            self.meta["fallback_used"] = True
            return self.fallback.invoke(prompt)


def resolve_chat_llm(model: Optional[str] = None, provider_id: Optional[str] = None, fallback_provider_id: Optional[str] = None) -> Tuple[Optional[ChatLLM], Dict[str, Any]]:
    provider = None
    if provider_id:
        provider = fetch_api_provider(provider_id)

    provider_name = (provider or {}).get("name") or ""
    provider_base_url = (provider or {}).get("base_url") or ""
    cfg_provider_type = _normalize_provider_type(_safe_get(provider, "config", "provider_type")) if provider else ""
    kind = cfg_provider_type or (_infer_provider_kind(provider_name, provider_base_url) if provider else "")

    cfg_model_id = _safe_get(provider, "config", "model_id") if provider else None
    cfg_api_key = _safe_get(provider, "config", "api_key") if provider else None
    cfg_base_url = (provider or {}).get("base_url") if provider else None

    if not kind:
        m = model or ""
        if m.startswith("glm"):
            kind = "zhipu"
        elif m.startswith("spark"):
            kind = "spark"
        elif ":" in m:
            kind = "ollama"
        else:
            kind = "openai_compat"

    requested_model = model
    if provider and requested_model and requested_model == provider_name:
        requested_model = None
    resolved_model = cfg_model_id or requested_model or _infer_default_model(provider_name, kind)
    resolved_base_url = (cfg_base_url or "").strip() or _infer_default_base_url(provider_name, kind)
    resolved_api_key = (cfg_api_key or "").strip() or _infer_default_api_key(provider_name, kind)

    meta = {
        "kind": kind,
        "provider_type": cfg_provider_type or kind,
        "provider_id": provider_id,
        "provider_name": provider_name,
        "model": resolved_model,
        "base_url": resolved_base_url,
    }

    # Guardrail: this is our own Django endpoint, not a model provider base URL.
    base_url_norm = (resolved_base_url or "").strip().lower().rstrip("/")
    if "/api/rag/chat" in base_url_norm:
        return None, {**meta, "error": "invalid_base_url"}

    if kind == "ollama":
        return OllamaChatLLM(model=resolved_model, base_url=resolved_base_url), meta

    allow_without_key = kind == "openai_compat" and _is_local_base_url(resolved_base_url)
    if not resolved_api_key and not allow_without_key:
        return None, {**meta, "error": "missing_api_key"}

    if kind == "zhipu":
        primary = ZhipuChatLLM(api_key=resolved_api_key, model=resolved_model, base_url=resolved_base_url)
    elif kind == "spark":
        primary = OpenAICompatChatLLM(api_key=resolved_api_key, model=resolved_model, base_url=resolved_base_url)
    else:
        primary = OpenAICompatChatLLM(api_key=resolved_api_key, model=resolved_model, base_url=resolved_base_url)

    # 如果有备用 provider，尝试加载并级联
    if fallback_provider_id:
        fallback_provider = fetch_api_provider(fallback_provider_id)
        if fallback_provider:
            fb_name = fallback_provider.get("name") or ""
            fb_base_url = fallback_provider.get("base_url") or ""
            fb_cfg_type = _normalize_provider_type(_safe_get(fallback_provider, "config", "provider_type"))
            fb_kind = fb_cfg_type or _infer_provider_kind(fb_name, fb_base_url)
            fb_model = _safe_get(fallback_provider, "config", "model_id") or _infer_default_model(fb_name, fb_kind)
            fb_base_url = (fallback_provider.get("base_url") or "").strip() or _infer_default_base_url(fb_name, fb_kind)
            fb_api_key = (_safe_get(fallback_provider, "config", "api_key") or "").strip() or _infer_default_api_key(fb_name, fb_kind)

            if fb_kind == "ollama":
                fb_llm = OllamaChatLLM(model=fb_model, base_url=fb_base_url)
            elif fb_kind == "zhipu":
                fb_llm = ZhipuChatLLM(api_key=fb_api_key, model=fb_model, base_url=fb_base_url)
            else:
                fb_llm = OpenAICompatChatLLM(api_key=fb_api_key, model=fb_model, base_url=fb_base_url)

            return FallbackChatLLM(primary, fb_llm, meta), meta

    return primary, meta
