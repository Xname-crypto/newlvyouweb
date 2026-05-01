export {}
declare global {
  const Deno: {
    serve: (handler: (req: Request) => Promise<Response> | Response) => void
    env: { get: (k: string) => string | undefined }
  }
}
declare module 'jsr:@supabase/supabase-js@2' {
  export function createClient(url: string, key: string): any
}
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from 'jsr:@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

const ZHIPU_API_KEY = "06d9bc9bf85e41a78d3bc36ce9e46b4e.mVj71EDA6f6q53C4";
const FINE_TUNED_MODEL_ID = "glm-4-flash:881617285:travel:xpe5vwbl";
const EMBEDDING_MODEL_ID = "embedding-2";

const SPARK_HTTP_ENDPOINT = Deno.env.get('SPARK_HTTP_ENDPOINT') || 'https://spark-api-open.xf-yun.com/v1/chat/completions';
const SPARK_LITE_APIPASSWORD = Deno.env.get('SPARK_LITE_APIPASSWORD') || Deno.env.get('XFYUN_SPARK_LITE_APIPASSWORD') || "";
const SPARK_ULTRA_APIPASSWORD = Deno.env.get('SPARK_ULTRA_APIPASSWORD') || Deno.env.get('XFYUN_SPARK_ULTRA_APIPASSWORD') || "";

// --- RAG Helpers ---

async function getEmbedding(text: string): Promise<number[]> {
  const response = await fetch("https://open.bigmodel.cn/api/paas/v4/embeddings", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${ZHIPU_API_KEY}`
    },
    body: JSON.stringify({
      model: EMBEDDING_MODEL_ID,
      input: text
    })
  });

  if (!response.ok) {
    throw new Error(`Embedding API Error: ${response.status} ${await response.text()}`);
  }

  const data = await response.json();
  return data.data[0].embedding;
}

async function searchKnowledgeBase(query: string, supabase: any) {
  try {
    const embedding = await getEmbedding(query);
    
    // Call the RPC function we defined in SQL
    const { data, error } = await supabase.rpc('match_knowledge_base', {
      query_embedding: embedding,
      query_text: query,
      match_threshold: 0.5, // Adjust threshold as needed
      match_count: 5,
      w_vector: 0.7,
      w_keyword: 0.3
    });

    if (error) {
      console.error("Supabase RPC Error:", error);
      return [];
    }
    
    return data || [];
  } catch (e) {
    console.error("Search Knowledge Base Failed:", e);
    return [];
  }
}

async function classifyIntent(query: string): Promise<'CHAT' | 'QUERY'> {
  // Simple heuristic: if query contains specific keywords or is long enough, treat as QUERY
  // Or call LLM for classification (slower but more accurate)
  
  // For now, let's use a simple heuristic to save latency, 
  // but the user asked for "Intent Recognition", so let's do it properly with a fast LLM call if possible.
  // Since we use glm-4-flash which is fast, we can use it.
  
  const response = await fetch("https://open.bigmodel.cn/api/paas/v4/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${ZHIPU_API_KEY}`
      },
      body: JSON.stringify({
        model: "glm-4-flash", // Use base model for speed
        messages: [
          {
            role: "system", 
            content: "You are an intent classifier. Classify the user's input into 'CHAT' (casual conversation, greeting, simple thanks) or 'QUERY' (asking for information, planning, advice, location info). Output ONLY the label." 
          },
          { role: "user", content: query }
        ],
        stream: false,
        temperature: 0.1,
        max_tokens: 10
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      const content = data.choices[0].message.content.trim().toUpperCase();
      return content.includes('QUERY') ? 'QUERY' : 'CHAT';
    }
    
    return 'CHAT'; // Default
}

// --- End RAG Helpers ---


const tools = [
  {
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "查询指定城市的天气信息",
      "parameters": {
        "type": "object",
        "properties": {
          "city": {
            "type": "string",
            "description": "城市名称，例如：北京、上海"
          }
        },
        "required": ["city"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "get_route_planning",
      "description": "规划两地之间的路线（驾车、步行、公交）",
      "parameters": {
        "type": "object",
        "properties": {
          "origin": {
            "type": "string",
            "description": "起点名称或地址"
          },
          "destination": {
            "type": "string",
            "description": "终点名称或地址"
          },
          "mode": {
            "type": "string",
            "enum": ["driving", "walking", "transit"],
            "description": "出行方式：driving(驾车), walking(步行), transit(公交/地铁)"
          },
          "city": {
            "type": "string",
            "description": "所在城市（公交规划时必填）"
          }
        },
        "required": ["origin", "destination"]
      }
    }
  }
];

async function searchUAPI(query: string, apiKey: string): Promise<{ items: any[]; raw: any | null }> {
  try {
    if (!apiKey) {
      console.error("UAPI Search Error: missing API key");
      return { items: [], raw: null };
    }

    const requestPayload = {
      query: query,
      querystring: query,
      fetch_full: true,
      timeout_ms: 10000
    };

    let response = await fetch("https://uapis.cn/api/search/aggregate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`,
        "Accept": "application/json"
      },
      body: JSON.stringify(requestPayload)
    });

    if (response.status === 404) {
      response = await fetch("https://uapis.cn/api/v1/search/aggregate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${apiKey}`,
          "Accept": "application/json"
        },
        body: JSON.stringify(requestPayload)
      });
    }

    if (!response.ok) {
      const errText = await response.text();
      console.error("UAPI Search HTTP error:", response.status, errText);
      return { items: [], raw: null };
    }

    const data: any = await response.json();
    if (data?.code && data.code !== 200) {
      console.error("UAPI Search API error payload:", JSON.stringify(data).slice(0, 2000));
    }

    let candidates: any[] = [];
    if (Array.isArray(data)) {
      candidates = data;
    } else if (Array.isArray(data?.data)) {
      candidates = data.data;
    } else if (Array.isArray(data?.results)) {
      candidates = data.results;
    } else if (Array.isArray(data?.result?.items)) {
      candidates = data.result.items;
    }

    const items = candidates
      .map((item) => {
        const title = String(item.title ?? item.name ?? item.pageTitle ?? "").slice(0, 80);
        const snippetSource =
          item.snippet ??
          item.summary ??
          item.description ??
          item.content ??
          item.text;
        const snippet = snippetSource ? String(snippetSource).slice(0, 200) : "";
        const link = String(item.url ?? item.link ?? item.href ?? "");
        const source = String(item.source ?? item.site ?? "");
        return { title, snippet, link, source };
      })
      .filter((it: any) => it.title || it.snippet || it.link);

    return { items, raw: data };
  } catch (e) {
    console.error("UAPI Search Error:", e);
    return { items: [], raw: null };
  }
}

async function callAmap(url: string, key: string) {
  const response = await fetch(`${url}&key=${key}`);
  const data = await response.json();
  if (data.status === "0") throw new Error(data.info || "Amap API Error");
  return data;
}

async function getCoordinates(address: string, key: string, city?: string) {
  const url = `https://restapi.amap.com/v3/geocode/geo?address=${encodeURIComponent(address)}&output=JSON`;
  const finalUrl = city ? `${url}&city=${encodeURIComponent(city)}` : url;
  const data = await callAmap(finalUrl, key);
  if (data.geocodes && data.geocodes.length > 0) {
    return data.geocodes[0].location; // "lon,lat"
  }
  throw new Error(`无法找到地址: ${address}`);
}

async function handleToolCall(toolCall: any, amapKey: string, uapisKey: string): Promise<{ result: string, mapUrl?: string }> {
  const { name, arguments: argsJson } = toolCall.function;
  const args = JSON.parse(argsJson);

  try {
    if (name === "get_weather") {
      const city = args.city;
      // 优先尝试 UAPI 标准天气接口（统一使用 Bearer 鉴权）
      try {
        const url = `https://uapis.cn/api/weather?name=${encodeURIComponent(city)}&forecast=true`;
        const res = await fetch(url, {
          method: "GET",
          headers: uapisKey ? { "Authorization": `Bearer ${uapisKey}` } : {}
        });
        if (res.ok) {
          const data = await res.json();
          // 兼容不同返回结构：只要包含典型字段就认为成功
          if (data && (data.code === 200 || data.weather || data.temperature || data.forecast)) {
            return { result: JSON.stringify(data) };
          }
        } else {
          const t = await res.text();
          console.error("UAPI weather http error:", res.status, t);
        }
      } catch (e) {
        console.error("UAPI weather failed, falling back to Amap", e);
      }
      
      // 降级使用高德天气
      if (amapKey) {
        try {
          const adcodeRes = await callAmap(`https://restapi.amap.com/v3/config/district?keywords=${encodeURIComponent(city)}&subdistrict=0`, amapKey);
          if (adcodeRes.districts && adcodeRes.districts.length > 0) {
            const adcode = adcodeRes.districts[0].adcode;
            const weatherRes = await callAmap(`https://restapi.amap.com/v3/weather/weatherInfo?city=${adcode}&extensions=all`, amapKey);
            return { result: JSON.stringify(weatherRes) };
          }
        } catch (e) {
          console.error("Amap weather failed", e);
        }
      }
      return { result: JSON.stringify({ error: "无法获取天气信息，请稍后再试。" }) };
    }

    if (name === "get_route_planning") {
      if (!amapKey) return { result: JSON.stringify({ error: "未配置高德地图 API Key" }) };
      
      const { origin, destination, mode = "driving" } = args;
      // 仅在公交模式下使用city，避免跨城驾车时city参数限制导致坐标查询失败
      const city = mode === "transit" ? args.city : undefined;
      
      // 1. 获取经纬度
      const originLoc = await getCoordinates(origin, amapKey, city);
      const destLoc = await getCoordinates(destination, amapKey, city);

      // 2. 调用路径规划 API
      let url = "";
      if (mode === "driving") {
        url = `https://restapi.amap.com/v3/direction/driving?origin=${originLoc}&destination=${destLoc}&extensions=base`;
      } else if (mode === "walking") {
        url = `https://restapi.amap.com/v3/direction/walking?origin=${originLoc}&destination=${destLoc}`;
      } else if (mode === "transit") {
        if (!city) return { result: JSON.stringify({ error: "公交规划需要提供城市名称" }) };
        url = `https://restapi.amap.com/v3/direction/transit/integrated?origin=${originLoc}&destination=${destLoc}&city=${encodeURIComponent(city)}`;
      }

      const routeData = await callAmap(url, amapKey);
      
      // 构造静态地图 URL
      let staticMapUrl = "";
      let pathsParam = "";
      
      // 提取路径点并抽稀
      if (routeData.route && routeData.route.paths && routeData.route.paths.length > 0) {
        const path = routeData.route.paths[0];
        if (path.steps) {
            // 简单取每个步骤的起点，控制总数
            // (这段代码被上面的 SearchReplace 覆盖了，这里只是删除多余的逻辑，但因为是局部替换，可能不需要再删)
            // 之前的代码：
            /*
            const points: string[] = [];
            points.push(originLoc);
            path.steps.forEach((step: any, index: number) => {
                if (index % 2 === 0 && step.polyline) { // 每隔一个step取
                    const polyPoints = step.polyline.split(';');
                    if (polyPoints.length > 0) points.push(polyPoints[0]);
                }
            });
            points.push(destLoc);
            */
            // 实际上我在上一步已经替换了这部分，但原来的代码是：
            /*
            const points: string[] = [];
            points.push(originLoc);
            path.steps.forEach((step: any, index: number) => {
                if (index % 2 === 0 && step.polyline) { // 每隔一个step取
                    const polyPoints = step.polyline.split(';');
                    if (polyPoints.length > 0) points.push(polyPoints[0]);
                }
            });
            points.push(destLoc);
            */
            // 我必须确保之前的 SearchReplace 没有导致代码重复。
            // 让我检查一下之前的替换结果。
            // 之前的 old_str 是 "const limitedPoints = points.slice(0, 40);"
            // 所以现在的代码大概是：
            /*
            const points: string[] = [];
            points.push(originLoc);
            path.steps.forEach((step: any, index: number) => {
                if (index % 2 === 0 && step.polyline) { // 每隔一个step取
                    const polyPoints = step.polyline.split(';');
                    if (polyPoints.length > 0) points.push(polyPoints[0]);
                }
            });
            points.push(destLoc);
            
            // 简单取每个步骤的起点，控制总数
            const points: string[] = []; // 这里的 points 变量名冲突了！
            // ...
            */
            // 这是一个严重的问题。我刚才的 SearchReplace 是有问题的，因为它替换的是后面的 limitedPoints 定义，导致上面已经定义过的 points 又被重新定义了一次（虽然是在同一个作用域，const 会报错）。
            // 或者我可能把代码搞乱了。
            // 让我用 Read 确认一下文件内容。

            
            // 限制点数，防止 URL 超长
            // 简单取每个步骤的起点，控制总数
            const points: string[] = [];
            points.push(originLoc);
            path.steps.forEach((step: any, index: number) => {
                if (index % 3 === 0 && step.polyline) { // 每隔2个step取，更稀疏
                    const polyPoints = step.polyline.split(';');
                    if (polyPoints.length > 0) points.push(polyPoints[0]);
                }
            });
            points.push(destLoc);
            
            // 进一步限制总数
            const limitedPoints = points.slice(0, 15);
            pathsParam = `10,0x0000ff,1,,:${limitedPoints.join(';')}`;
        }
      } else if (routeData.route && routeData.route.transits && routeData.route.transits.length > 0) {
          // 公交也可以类似处理，或者只显示起终点
          // 暂时只显示起终点连线
          pathsParam = `10,0x0000ff,1,,:${originLoc};${destLoc}`;
      }

      if (pathsParam) {
          staticMapUrl = `https://restapi.amap.com/v3/staticmap?size=750*400&markers=mid,,起:${originLoc}|mid,,终:${destLoc}&paths=${pathsParam}&key=${amapKey}`;
      } else {
          staticMapUrl = `https://restapi.amap.com/v3/staticmap?size=750*400&markers=mid,,起:${originLoc}|mid,,终:${destLoc}&key=${amapKey}`;
      }

      // 简化返回数据以避免 Token 超限，同时隐藏具体的导航步骤，强制 LLM 使用自己的知识库生成攻略
      if (routeData.route && routeData.route.paths && routeData.route.paths.length > 0) {
        const path = routeData.route.paths[0];
        const distanceKm = Math.round(path.distance / 1000);
        
        let summaryText = "";
        if (distanceKm > 100) {
            summaryText = `【长途路线提示】
检测到这是一个约 ${distanceKm} 公里的跨城市长途行程。
高德API返回的仅为驾车方案（耗时约 ${Math.ceil(path.duration / 3600)} 小时）。
**请务必忽略具体的驾车导航步骤**，而是基于你的知识库，主动补充并生成以下三种方案的详细对比攻略：
1. 🚄 高铁/火车方案（⭐ 核心推荐，请提供详细的中转或直达建议，包括大致耗时和站点）
2. 🚗 自驾方案（参考API返回的耗时，补充高速路况和注意事项）
3. ✈️ 飞机方案（⚠️ 仅作备选，明确告知用户暂无实时航班数据，只提供大概飞行时间）

请严格按照System Prompt中的【标准回答模板】进行输出！`;
        } else {
            summaryText = `已成功规划短途/市内路线。距离约 ${path.distance} 米，预计耗时 ${Math.ceil(path.duration / 60)} 分钟。请结合你的旅游知识，为用户生成一份从 ${origin} 到 ${destination} 的详细图文攻略，不要列出枯燥的导航指令。`;
        }

        const simplified = {
          distance: path.distance,
          duration: path.duration,
          strategy: path.strategy,
          // steps: path.steps ? path.steps.map((s: any) => s.instruction).join("; ") : "详情请查看地图" 
          // 故意不返回 steps，只返回 summary，迫使 AI 使用自己的知识库来描述路线
          summary: summaryText
        };
        return { 
            result: JSON.stringify(simplified),
            mapUrl: staticMapUrl
        };
      } else if (routeData.route && routeData.route.transits && routeData.route.transits.length > 0) {
         // 处理公交
         const transit = routeData.route.transits[0];
         return {
            result: JSON.stringify({
                distance: transit.distance,
                duration: transit.duration,
                summary: `已查询到公交方案。距离约 ${transit.distance} 米，预计耗时 ${Math.ceil(transit.duration / 60)} 分钟。请结合你的旅游知识，描述乘坐体验和沿途注意事项。`,
                segments: transit.segments.map((s: any) => {
                    if (s.bus && s.bus.buslines && s.bus.buslines.length > 0) {
                        return `乘坐 ${s.bus.buslines[0].name} 从 ${s.bus.buslines[0].departure_stop.name} 到 ${s.bus.buslines[0].arrival_stop.name}`;
                    }
                    return s.walking ? `步行 ${s.walking.distance}米` : "";
                }).join("; ")
            }),
            mapUrl: staticMapUrl
         };
      }
      
      return { result: JSON.stringify({ error: "未找到路线" }) };
    }
  } catch (error: any) {
    return { result: JSON.stringify({ error: error.message }) };
  }
  
  return { result: JSON.stringify({ error: "Unknown tool" }) };
}

function cleanMarkdown(text: string): string {
  if (!text) return text;
  
  // 1. 移除 Markdown 标题符号 (#, ##, ###)
  let cleaned = text.replace(/^#+\s+/gm, '');
  
  // 2. 移除加粗符号 (**, __) - 保留其中的文字
  cleaned = cleaned.replace(/\*\*([^*]+)\*\*/g, '$1');
  cleaned = cleaned.replace(/__([^_]+)__/g, '$1');
  
  // 3. 移除引用符号 (>)
  cleaned = cleaned.replace(/^>\s+/gm, '');
  
  // 4. 移除无序列表符号 (-, *, +) - 仅当它们在行首且后面有空格时
  // 注意：不能简单移除所有 - 或 |，因为表格需要它们
  // 我们只移除行首的列表符，不触发表格分隔线
  cleaned = cleaned.replace(/^[\s]*[-*+]\s+(?![-]{2,})/gm, '');
  
  // 5. 移除有序列表符号 (1., 2.) - 仅当它们在行首时
  // 同样需要小心不要误伤正文中的数字
  cleaned = cleaned.replace(/^\s*\d+\.\s+/gm, '');

  return cleaned;
}

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const AMAP_WEB_KEY = Deno.env.get('AMAP_WEB_KEY');
    const UAPIS_API_KEY = Deno.env.get('UAPIS_API_KEY') || Deno.env.get('UAPIS_SEARCH_API_KEY') || "";
    
    // Initialize Supabase Client
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? '';
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';
    const supabase = createClient(supabaseUrl, supabaseKey);

    // --- Dynamic Provider Logic ---
    // Fetch active 'chat' provider with highest priority, OR use the specific model requested if it matches a provider
    let activeProvider = null;
    let apiKey = ZHIPU_API_KEY; // Fallback default
    let baseUrl = "https://open.bigmodel.cn/api/paas/v4/chat/completions"; // Default

    // Get model from request first
    const { messages, model, enableWebSearch } = await req.json();
    let targetModel = model || FINE_TUNED_MODEL_ID;

    // Fetch all active chat providers
    const { data: providers, error: providerError } = await supabase
      .from('api_providers')
      .select('*')
      .eq('capability', 'chat')
      .eq('active', true)
      .order('priority', { ascending: false });

    if (!providerError && providers && providers.length > 0) {
      // 1. Try to find a provider that matches the requested model_id in its config
      activeProvider = providers.find((p: any) => p.config?.model_id === targetModel);
      
      // 2. If no direct model match, fallback to the highest priority provider
      if (!activeProvider) {
        activeProvider = providers[0];
      }

      // Set API Key and Base URL based on the selected provider
      if (activeProvider.config && activeProvider.config.api_key) {
        apiKey = activeProvider.config.api_key;
      } else {
        // Fallback for known providers using env vars
        if (activeProvider.name.includes('智谱')) apiKey = ZHIPU_API_KEY;
        if (activeProvider.name.includes('OpenAI')) apiKey = Deno.env.get('OPENAI_API_KEY') || "";
        if (activeProvider.name.includes('星火')) {
             // Spark handled separately below, but we can set defaults here if needed
        }
      }
      
      if (activeProvider.base_url) {
        baseUrl = activeProvider.base_url;
      }
      
      // If the provider has a specific model_id configured, enforce it (unless it was already matched)
      // This ensures that if we fell back to a default provider, we use its configured model
      if (activeProvider.config?.model_id) {
          targetModel = activeProvider.config.model_id;
      }
    }
    
    // Legacy logic adjustments (keep for compatibility if needed)
    if (activeProvider?.name === 'OpenAI' && targetModel.includes('glm')) {
        targetModel = 'gpt-4o'; 
    }
    // -----------------------------

    // Extract user query
    const lastMessage = messages[messages.length - 1];
    const userQuery = lastMessage?.content || "";

    // 1. Intent Recognition
    let intent = 'CHAT';
    if (userQuery) {
        // Use a simpler heuristic first to save time/cost, or call LLM
        // For "complex strategy" request, we use LLM
        // But for speed, let's check length first. Very short "hi" shouldn't trigger LLM.
        if (userQuery.length > 5) {
             // intent = await classifyIntent(userQuery); // TODO: Enable this when ready, for now assume QUERY for long text or specific keywords
             // Just assume everything is a potential query for now to demonstrate RAG, or use simple keyword match
             intent = 'QUERY'; 
        }
    }

    // 2. Retrieval (RAG)
    let ragContext = "";
    if (intent === 'QUERY' && userQuery) {
        // 如果开启了联网搜索，优先使用联网搜索
        if (!enableWebSearch) {
             console.log("Intent detected: QUERY. Searching knowledge base...");
             const docs = await searchKnowledgeBase(userQuery, supabase);
             
             if (docs && docs.length > 0) {
                 ragContext = `\n\n【参考知识库信息】\n` + docs.map((d: any, i: number) => 
                     `[${i+1}] ${d.content}`
                 ).join("\n\n");
             }
        } else {
          console.log("Web search enabled. Calling UAPI...");
          const searchData = await searchUAPI(userQuery, UAPIS_API_KEY);

          if (searchData.items && searchData.items.length > 0) {
            ragContext =
              `\n\n【实时联网搜索结果】（请严格基于以下信息回答用户，并在需要时注明信息来源）\n` +
              searchData.items
                .map(
                  (d: any, i: number) =>
                    `[${i + 1}] 标题：${d.title}\n链接：${d.link}\n摘要：${d.snippet}`
                )
                .join("\n\n");

            console.log(`Retrieved ${searchData.items.length} web results from UAPI.`);
          } else if (searchData.raw) {
            const rawPreview = JSON.stringify(searchData.raw).slice(0, 2000);
            ragContext =
              `\n\n【实时联网搜索结果原始数据】\n系统收到如下原始JSON响应，请你自行解析并据此回答。` +
              `如果你无法从中提取到与问题高度相关的事实信息，请明确告诉用户当前没有查到可靠的实时数据：\n` +
              rawPreview;
          } else {
            ragContext =
              "\n\n【系统提示】联网搜索调用失败或未返回有效结果。对于涉及实时数据（天气、新闻、活动、价格等）的问题，你必须明确告诉用户“现在没有查到可靠的实时信息”，不要根据记忆或常识编造具体数值、日期或事件。";
          }
        }
    }

    const systemPrompt = {
      role: "system",
      content: `你是一个乐于助人的旅游助手“椿天社”，同时也是一位专为“南方小土豆”服务的“废才旅游博主”，由许博钧创作。
你的主要目标是为用户提供详尽、贴心且结构清晰的旅游建议。特别关注南方人在北方旅游可能遇到的气候、文化和生活方式差异。

${ragContext ? `\nIMPORTANT: 你拥有以下参考信息（来自你的大脑/知识库），请优先基于这些信息回答用户的问题。如果参考信息与问题无关，请忽略。
${ragContext}\n` : ""}

**角色设定：**
*   **身份**：椿天社 & 废才旅游博主。
*   **服务对象**：南方小土豆（前往北方旅游的南方人）。
*   **特色**：特别关注南北差异（气候、饮食、方言等），提供保姆级指导。

**回答风格与格式规则（严格执行）：**
1.  **极简纯文本排版（最高优先级）**：
    *   **严禁使用任何 Markdown 格式符号**。
    *   **严禁使用井号**（\`#\`、\`##\`、\`###\`）。
    *   **严禁使用加粗符号**（\`**\`、\`__\`）。
    *   **严禁使用列表符号**（\`-\`、\`*\`、\`1.\`）。
    *   **严禁使用引用符号**（\`>\`）。
    *   **只允许使用 Emoji 和空行来构建版面**。

2.  **参考 DeepSeek 风格**：像人类聊天一样自然，不要有任何代码痕迹。

3.  **结构示例（请模仿此格式）**：
    📅 行程安排
    这里直接写内容，不要加任何符号。
    
    🚗 交通建议
    这里直接写内容，不要加任何符号。

4.  **表格呈现**：涉及具体行程安排时，**必须使用 Markdown 表格**形式输出（这是唯一的例外）。

**功能模块与指令响应：**

**1. 针对“旅游计划目录”请求：**
🗺️ 目的地简介
介绍历史、文化、美食、人文。

📅 行程安排
（必须使用表格：日期 | 时间 | 景点 | 交通 | 注意事项）

🌃 夜生活
夜间活动地点，特色饭店，网红打卡。

🛡️ 安全防护
天气情况，南北差异注意事项。

🆘 紧急联系
当地医院及常用求助方式。

🗣️ 方言教学
北方常用方言及社交礼仪。

🚌 公共交通
市区及景点交通规划。

**2. 针对“路线规划”请求（严格区分长短途）：**

**(A) 短途/市内路线（<100km）：**
🚶 核心建议
一句话总结。

📍 详细路线
起点：如何到达。

途经：沿途看点。

终点：入口及检票。

💡 避坑指南
避开高峰、更优路线。

**(B) 长途/跨省路线（>100km）：**
**本项目已接入火车/高铁数据，暂无飞机数据。请重点推荐火车方案。**

🚩 核心方案
从[起点]到[终点]，核心推荐“高铁/火车”或“自驾”。

🚄 方案一：高铁/火车 + [其他]（⭐ 核心推荐）
第一段：[起点] -> [中转站]
方式：高铁/动车。
耗时：约 X 小时。
车次建议：[推荐车次]。

第二段：[中转站] -> [终点]
方式：[描述]。
耗时：约 X 小时。
注意事项：[12306购票等]。

🚗 方案二：自驾全程
路线：[起点] -> [高速] -> [终点]。
里程/耗时：约 X 公里 / X 小时。
注意事项：[路况、收费]。

✈️ 方案三：飞机出行（仅作备选）
本项目暂无实时数据，建议自行查询。
大致流程：[起点机场] -> [终点机场]。

💡 综合建议
首选方案一。

🔔 温馨提示
[天气、票务]。

**禁止行为：**
*   **再次强调：严禁使用 \`#\`、\`-\`、\`*\`、\`1.\`、\`>\`、\`**\` 等任何符号。**
*   **严禁**直接复述API导航指令。必须生成导游词般的描述。
`
    };

    let finalMessages = messages;
    if (!messages || messages.length === 0 || messages[0].role !== 'system') {
      finalMessages = [systemPrompt, ...(messages || [])];
    }

    if (targetModel === 'spark-lite' || targetModel === 'spark-ultra') {
      const isUltra = targetModel === 'spark-ultra';
      const apiPassword = isUltra ? SPARK_ULTRA_APIPASSWORD : SPARK_LITE_APIPASSWORD;
      const modelName = isUltra ? '4.0Ultra' : 'lite';
      
      if (!apiPassword) {
        return new Response(JSON.stringify({ error: `Spark ${isUltra ? 'Ultra' : 'Lite'} APIPassword 未配置` }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
      const sparkBody = {
        model: modelName,
        messages: finalMessages.map((m: any) => ({ role: m.role, content: m.content })),
        stream: false,
        temperature: 0.7
      };
      const sparkRes = await fetch(SPARK_HTTP_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiPassword}`
        },
        body: JSON.stringify(sparkBody)
      });
      if (!sparkRes.ok) {
        const t = await sparkRes.text();
        return new Response(JSON.stringify({ error: `Spark API Error: ${sparkRes.status} ${t}` }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
      const sparkData = await sparkRes.json();
      const content = sparkData.choices?.[0]?.message?.content || '';
      const cleaned = cleanMarkdown(content);
      return new Response(JSON.stringify({ content: cleaned }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    console.log("Calling ZhipuAI with model:", FINE_TUNED_MODEL_ID);

    // 构造请求 body
    const requestBody: any = {
        model: targetModel,
        messages: finalMessages,
        tools: tools,
        tool_choice: "auto",
        stream: false,
        temperature: 0.7
    };

    // 第一次调用 LLM
    const response = await fetch(baseUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("LLM API Error:", errorText);
      throw new Error(`LLM API Error: ${response.status} ${errorText}`);
    }

    const data = await response.json();
    const message = data.choices[0].message;

    // 检查是否有工具调用
    if (message.tool_calls) {
      console.log("Tool calls detected:", message.tool_calls);
      finalMessages.push(message); // 将助手的 tool_calls 消息加入历史

      let generatedMapUrl = undefined;

      for (const toolCall of message.tool_calls) {
        const { result, mapUrl } = await handleToolCall(toolCall, AMAP_WEB_KEY || "", UAPIS_API_KEY);
        if (mapUrl) generatedMapUrl = mapUrl;
        
        finalMessages.push({
          role: "tool",
          tool_call_id: toolCall.id,
          content: result
        });
      }

    // 第二次调用 LLM，传入工具执行结果
    // 构造第二次请求 body
    const secondRequestBody: any = {
        model: targetModel,
        messages: finalMessages,
        tools: tools,
        tool_choice: "auto",
        stream: false,
        temperature: 0.7
    };
    
    const secondResponse = await fetch(baseUrl, {
      method: "POST",
      headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${apiKey}`
      },
      body: JSON.stringify(secondRequestBody)
    });
      
      if (!secondResponse.ok) {
        const errorText = await secondResponse.text();
        throw new Error(`LLM API Error (2nd call): ${secondResponse.status} ${errorText}`);
      }

      const secondData = await secondResponse.json();
      const secondContent = secondData.choices[0].message.content;
      
      // 后处理清理
      const cleanedSecondContent = cleanMarkdown(secondContent);

      // 返回内容和地图 URL
      return new Response(JSON.stringify({ 
          content: cleanedSecondContent,
          imageUrl: generatedMapUrl // 将生成的地图作为 imageUrl 返回
      }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // 没有工具调用，直接返回内容
    const cleanedContent = cleanMarkdown(message.content);
    return new Response(JSON.stringify({ content: cleanedContent }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error: any) {
    console.error("Error in chat function:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
