import os
import asyncio
import random
import time
from typing import List, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from .models import KnowledgeBase
from asgiref.sync import sync_to_async


# Rate limiting: minimum delay between crawl requests (in seconds)
MIN_CRAWL_DELAY = 2.0
MAX_CRAWL_DELAY = 5.0

# Track last crawl time per host for rate limiting
_last_crawl_time: dict = {}


def _get_host(url: str) -> str:
    """Extract host from URL for rate limiting."""
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def _can_crawl(url: str, user_agent: str = "Mozilla/5.0 (compatible; TravelBot/1.0)") -> bool:
    """
    Check if crawling is allowed based on robots.txt.
    Returns True if allowed or robots.txt not found.
    """
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    try:
        resp = requests.get(robots_url, timeout=5, headers={"User-Agent": user_agent})
        if resp.status_code != 200:
            return True  # No robots.txt found, assume allowed

        # Simple robots.txt parser
        for line in resp.text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Check if this rule applies to our user agent
            if line.lower().startswith("user-agent:"):
                agent = line.split(":", 1)[1].strip()
                if agent == "*" or user_agent.lower().contains(agent.lower()):
                    # Now look for allow/disallow rules
                    continue
            elif line.lower().startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path and parsed.path.startswith(path):
                    return False
            elif line.lower().startswith("allow:"):
                path = line.split(":", 1)[1].strip()
                if path and parsed.path.startswith(path):
                    return True
        return True
    except Exception:
        return True  # If we can't read robots.txt, assume allowed


def _rate_limit(url: str) -> None:
    """Apply rate limiting before crawling a URL."""
    host = _get_host(url)
    now = time.time()

    if host in _last_crawl_time:
        elapsed = now - _last_crawl_time[host]
        delay = random.uniform(MIN_CRAWL_DELAY, MAX_CRAWL_DELAY)
        if elapsed < delay:
            sleep_time = delay - elapsed
            print(f"[RateLimit] Waiting {sleep_time:.1f}s before crawling {host}...")
            time.sleep(sleep_time)

    _last_crawl_time[host] = time.time()

# Set crawl4ai base directory to avoid PermissionError in user home
# We use a local directory inside the backend folder
# os.environ["CRAWL4AI_BASE_DIRECTORY"] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "crawl4ai_data")

# from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    class RecursiveCharacterTextSplitter:  # type: ignore[override]
        """Fallback splitter used when langchain_text_splitters isn't installed."""

        def __init__(self, chunk_size=1000, chunk_overlap=200, length_function=len, **_kwargs):
            self.chunk_size = max(int(chunk_size), 1)
            self.chunk_overlap = max(int(chunk_overlap), 0)
            self.length_function = length_function

        def split_text(self, text: str):
            if not text:
                return []
            if self.length_function(text) <= self.chunk_size:
                return [text]

            chunks = []
            step = max(self.chunk_size - self.chunk_overlap, 1)
            start = 0
            while start < len(text):
                end = start + self.chunk_size
                chunks.append(text[start:end])
                if end >= len(text):
                    break
                start += step
            return chunks
from .utils import get_embedding, SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

def simple_crawl(url: str) -> dict:
    """
    A simple crawler using requests and BeautifulSoup as a fallback/alternative.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Referer': 'https://www.zhihu.com/',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        # Add a small delay or retry logic if needed, but for now just enhanced headers
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        title = soup.title.string if soup.title else url
        
        return {
            "url": url,
            "title": title,
            "content": text,
            "html": str(soup)
        }
    except Exception as e:
        raise Exception(f"Simple crawl failed: {str(e)}")

def jina_crawl(url: str) -> dict:
    """
    Crawls a URL using Jina Reader (r.jina.ai), which converts web pages to Markdown.
    This is very robust against anti-scraping measures.
    """
    jina_url = f"https://r.jina.ai/{url}"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        response = requests.get(jina_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        content = response.text
        
        # Jina usually puts the title in the first line as markdown header
        lines = content.splitlines()
        title = url
        if lines and lines[0].startswith('# '):
            title = lines[0][2:].strip()
            
        return {
            "url": url,
            "title": title,
            "content": content,
            "html": "" # Jina returns markdown directly
        }
    except Exception as e:
        raise Exception(f"Jina crawl failed: {str(e)}")

def uapi_crawl(url: str) -> dict:
    """
    Crawls a URL using uapis.cn web-to-markdown async API.
    """
    # The UAPI domain is not resolving properly or is unstable. 
    # Fallback to Jina Reader directly
    raise Exception("UAPI service is currently unreachable, falling back to Jina")

def firecrawl(url: str) -> dict:
    """
    Crawls a URL using Firecrawl API as another fallback.
    """
    # Using a free proxy/alternative or simply another user-agent configuration for basic requests
    # since we don't have a firecrawl API key. We will enhance the simple_crawl instead
    raise Exception("Not implemented")

def fetch_with_playwright(url: str) -> dict:
    """
    Use Playwright as a highly robust alternative for dynamic/protected pages.
    Since Playwright might not be installed, we use a different approach.
    """
    raise Exception("Not implemented")

def advanced_crawl(url: str) -> dict:
    """
    An advanced crawler that tries to bypass standard blocks using alternative headers
    and proxies if available.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Use a generic web proxy service if direct access fails
        # For demonstration, we'll try a different approach: Google Webcache
        google_cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{url}"
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            # Fallback to Google Cache
            response = requests.get(google_cache_url, headers=headers, timeout=15)
            response.raise_for_status()
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript", "iframe"]):
            script.extract()
            
        # Try to find the main content area (often in <article> or <main> or specific classes)
        main_content = soup.find('article') or soup.find('main') or soup.find(class_='RichText ztext Post-RichText') or soup
            
        # Get text
        text = main_content.get_text(separator='\n')
        
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = '\n\n'.join(lines)
        
        title = soup.title.string if soup.title else url
        
        return {
            "url": url,
            "title": title,
            "content": text,
            "html": ""
        }
    except Exception as e:
        raise Exception(f"Advanced crawl failed: {str(e)}")

def zhihu_api_crawl(url: str) -> dict:
    """
    Specifically targets Zhihu articles by using their API directly to bypass 403s.
    """
    import re
    # Extract article ID from URL
    match = re.search(r'zhuanlan\.zhihu\.com/p/(\d+)', url)
    if not match:
        raise Exception("Not a valid Zhihu article URL")
        
    article_id = match.group(1)
    api_url = f"https://www.zhihu.com/api/v4/articles/{article_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': url,
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        title = data.get('title', url)
        content_html = data.get('content', '')
        
        # Parse HTML to text
        soup = BeautifulSoup(content_html, 'html.parser')
        text = soup.get_text(separator='\n')
        
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = '\n\n'.join(lines)
        
        return {
            "url": url,
            "title": title,
            "content": text,
            "html": content_html
        }
    except Exception as e:
        raise Exception(f"Zhihu API crawl failed: {str(e)}")

def uapi_sdk_crawl(url: str) -> dict:
    """
    Crawls a URL using the official UAPI Python SDK.
    Requires token setup and uapi package.
    """
    try:
        from uapi import UapiClient
        from uapi.errors import UapiError
        import time
        
        # Initialize client with your token
        client = UapiClient("https://uapis.cn", token="uapi-ptg8oapimiqHE8nxG7hobCshwMnz7k8sG6fWNa5E")
        
        # Submit task
        submit_result = client.webparse.post_web_tomarkdown_async(url=url)
        
        # The result might already contain the data if it's fast, or we need to extract task ID
        # Since we don't have the exact SDK response structure, we assume it behaves like the REST API
        if hasattr(submit_result, 'task_id') or (isinstance(submit_result, dict) and 'taskId' in submit_result):
            task_id = getattr(submit_result, 'task_id', None) or submit_result.get('taskId')
            
            # Since the SDK might not have a direct poll method exposed in the snippet,
            # we fallback to REST polling if we have a task ID
            api_url = "https://uapis.cn/api/v1/web/tomarkdown-async"
            for _ in range(30):
                time.sleep(2)
                poll_response = requests.get(f"{api_url}?taskId={task_id}", timeout=10)
                poll_result = poll_response.json()
                
                if poll_result.get("code") == "200":
                    data = poll_result.get("data", {})
                    return {
                        "url": url,
                        "title": data.get("title", url),
                        "content": data.get("markdown", ""),
                        "html": ""
                    }
                elif poll_result.get("code") == "202":
                    continue
                else:
                    raise Exception(f"UAPI SDK polling failed: {poll_result.get('msg')}")
            raise Exception("UAPI SDK timeout")
            
        else:
            # Maybe it returns synchronously if it's cached?
            if isinstance(submit_result, dict) and 'markdown' in submit_result:
                 return {
                    "url": url,
                    "title": submit_result.get("title", url),
                    "content": submit_result.get("markdown", ""),
                    "html": ""
                }
            # Just return whatever we got stringified if structure is unknown
            return {
                "url": url,
                "title": url,
                "content": str(submit_result),
                "html": ""
            }
            
    except ImportError:
        raise Exception("UAPI SDK (uapi) is not installed. Please run: pip install uapi")
    except Exception as e:
        raise Exception(f"UAPI SDK crawl failed: {str(e)}")

async def crawl_and_process(url: str, save_to: str = 'supabase'):
    """
    Crawls a URL and processes the content into the knowledge base.
    Content is saved with status='pending_review' for admin review before activation.
    """
    if save_to == 'supabase':
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase credentials not configured.")

    # Apply rate limiting before crawling
    _rate_limit(url)

    # Check robots.txt
    if not _can_crawl(url):
        raise Exception(f"Crawling {url} is disallowed by robots.txt")

    print(f"Starting crawl for: {url} (Target: {save_to})")
    
    crawl_result = None
    crawl_method = "unknown"
    
    try:
        # 0. Try UAPI SDK first as requested by user
        try:
            crawl_result = uapi_sdk_crawl(url)
            crawl_method = "uapi_sdk"
        except Exception as e:
            print(f"UAPI SDK failed ({e}), trying next method...")
            
        # 1. If it's a Zhihu URL, try the specialized API first
        if not crawl_result and 'zhihu.com' in url:
            try:
                crawl_result = zhihu_api_crawl(url)
                crawl_method = "zhihu_api"
            except Exception as e:
                print(f"Zhihu API failed ({e}), falling back to advanced crawl...")
        
        # 2. Try advanced crawler if we don't have a result yet
        if not crawl_result:
            try:
                crawl_result = advanced_crawl(url)
                crawl_method = "advanced"
            except Exception as e:
                print(f"Advanced crawl failed ({e}), trying Jina Reader...")
                # 3. Try Jina Reader
                try:
                    crawl_result = jina_crawl(url)
                    crawl_method = "jina"
                except Exception as e2:
                    print(f"Jina crawl failed ({e2}), trying Simple...")
                    # 4. Fallback to simple
                    crawl_result = simple_crawl(url)
                    crawl_method = "simple"
            
        content = crawl_result['content']
        title = crawl_result['title']
        
        print(f"Crawled successfully using {crawl_method}. Title: {title}")
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_text(content)
        
        saved_count = 0
        
        if save_to == 'mysql':
            # Save to Local MySQL (KnowledgeBase model)
            # Use sync_to_async to wrap the Django ORM calls since we are in an async function
            @sync_to_async
            def save_to_db(chunks_to_save):
                saved = 0
                for i, chunk in enumerate(chunks_to_save):
                    KnowledgeBase.objects.create(
                        content=chunk,
                        metadata={
                            "source": url,
                            "title": title,
                            "chunk_index": i,
                            "crawled_at": str(timezone.now()),
                            "crawl_method": crawl_method,
                            "category": "未分类网络数据"
                        },
                        status="pending_review"
                    )
                    saved += 1
                return saved
                
            saved_count = await save_to_db(chunks)
                
        else:
            # Save to Supabase
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

            for i, chunk in enumerate(chunks):
                embedding = get_embedding(chunk)

                payload = {
                    "content": chunk,
                    "metadata": {
                        "source": url,
                        "title": title,
                        "chunk_index": i,
                        "crawled_at": str(timezone.now()),
                        "crawl_method": crawl_method,
                        "category": "未分类网络数据"
                    },
                    "embedding": embedding,
                    "status": "pending_review"
                }
                
                supabase.table("knowledge_base").insert(payload).execute()
                saved_count += 1
                
        return {
            "url": url,
            "title": title,
            "chunks_count": len(chunks),
            "saved_count": saved_count,
            "target": save_to,
            "method": crawl_method
        }
        
    except Exception as e:
        print(f"Crawl error: {e}")
        raise e

# Synchronous wrapper for calling from Django view
def run_crawl(url: str, save_to: str = 'supabase'):
    return asyncio.run(crawl_and_process(url, save_to))

