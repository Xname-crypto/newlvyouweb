export {}
declare global {
  const Deno: {
    serve: (handler: (req: Request) => Promise<Response> | Response) => void
    env: { get: (k: string) => string | undefined }
  }
}
declare module 'npm:openai@4.24.1' {
  const OpenAI: any
  export default OpenAI
}
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from 'jsr:@supabase/supabase-js@2';
import OpenAI from "npm:openai@4.24.1";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

Deno.serve(async (req: Request) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const { prompt, model } = await req.json();

    // Initialize Supabase Client
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? '';
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';
    const supabase = createClient(supabaseUrl, supabaseKey);

    // --- Dynamic Provider Logic ---
    let activeProvider = null;
    let apiKey = Deno.env.get('ARK_API_KEY') || ""; // Fallback
    let baseUrl = "https://ark.cn-beijing.volces.com/api/v3"; // Fallback

    // 1. First try to find a provider that matches the requested model
    let query = supabase
      .from('api_providers')
      .select('*')
      .eq('capability', 'image')
      .eq('active', true);

    if (model) {
        // If user requested a specific model, try to find the provider who owns it
        // We check if the provider's name or configured model_id matches the request
        // Since SQL 'or' with JSONB is tricky in Supabase JS simple syntax, we'll fetch all active image providers and filter in JS
        // This is fine as there are usually very few providers (<10)
    }
    
    const { data: providers, error: providerError } = await query.order('priority', { ascending: false });

    if (!providerError && providers && providers.length > 0) {
      // Filter logic:
      // 1. If model is provided, look for exact match in config.model_id OR fuzzy match in name
      // 2. If no model provided (or no match), fallback to highest priority
      
      if (model) {
          const lowerModel = model.toLowerCase();
          activeProvider = providers.find((p: any) => {
              const configModel = p.config?.model_id?.toLowerCase() || '';
              // Match if config model ID matches request
              if (configModel && (configModel === lowerModel || lowerModel.includes(configModel))) return true;
              // Special case: SiliconFlow handles kwai-kolors
              if (p.name === 'SiliconFlow' && lowerModel.includes('kolors')) return true;
              // Special case: Midjourney
              if (p.name === 'Midjourney' && lowerModel.includes('mj')) return true;
              // Special case: Doubao
              if (p.name === 'Doubao' && lowerModel.includes('doubao')) return true;
              return false;
          });
      }
      
      // If no specific match found, use the highest priority one (default)
      if (!activeProvider) {
          activeProvider = providers[0];
          console.log(`No specific provider found for model '${model}', falling back to default: ${activeProvider.name}`);
      } else {
          console.log(`Matched provider '${activeProvider.name}' for requested model '${model}'`);
      }

      if (activeProvider.config && activeProvider.config.api_key) {
        apiKey = activeProvider.config.api_key;
      } else {
        // Fallback checks
        if (activeProvider.name === 'Midjourney') apiKey = Deno.env.get('MIDJOURNEY_API_KEY') || "";
        if (activeProvider.name === 'SiliconFlow') apiKey = Deno.env.get('SILICONFLOW_API_KEY') || "";
        if (activeProvider.name === 'Doubao') apiKey = Deno.env.get('ARK_API_KEY') || "";
      }
      if (activeProvider.base_url) {
        baseUrl = activeProvider.base_url;
      }
    }
    // -----------------------------

    // For testing connectivity
    if (prompt === 'PING') {
      return new Response(JSON.stringify({ url: 'https://placehold.co/600x400?text=PONG' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    if (!prompt) {
      throw new Error('Prompt is required');
    }

    console.log(`Generating image for prompt: "${prompt}" using provider: ${activeProvider?.name || 'Default'}`);

    // Handle SiliconFlow / Kolors (Custom Logic)
    if (activeProvider?.name === 'SiliconFlow' || (model && model.toLowerCase().includes('kwai-kolors'))) {
      if (!apiKey) throw new Error('API Key is missing for SiliconFlow');
      
      const sfRes = await fetch('https://api.siliconflow.cn/v1/images/generations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
          model: 'Kwai-Kolors/Kolors',
          prompt,
          image_size: '1024x1024',
          batch_size: 1,
          num_inference_steps: 20,
          guidance_scale: 7.5
        })
      });
      if (!sfRes.ok) {
        const t = await sfRes.text();
        throw new Error(`SiliconFlow Error: ${sfRes.status} ${t}`);
      }
      const sfData: any = await sfRes.json();
      const imgs: any[] = sfData.images || sfData.data || [];
      if (!imgs || imgs.length === 0) throw new Error('No image generated');
      let url: string | undefined = imgs[0].url || imgs[0].image_url || imgs[0].imageUrl;
      if (!url && imgs[0].b64_json) {
        url = `data:image/png;base64,${imgs[0].b64_json}`;
      }
      if (!url && imgs[0].b64_image) {
        url = `data:image/png;base64,${imgs[0].b64_image}`;
      }
      if (!url) throw new Error('No image url in SiliconFlow response');
      return new Response(JSON.stringify({ url }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Default to OpenAI-compatible interface (Doubao/Ark, Midjourney Proxy, OpenAI DALL-E)
    if (!apiKey) {
      throw new Error('API Key is not configured');
    }

    const client = new OpenAI({
      apiKey: apiKey,
      baseURL: baseUrl,
    });

    // Default model if not specified or mapped
    let targetModel = "doubao-seedream-5-0-260128"; 
    if (activeProvider?.name === 'Midjourney') targetModel = "mj-v6";
    if (activeProvider?.name === 'OpenAI') targetModel = "dall-e-3";

    const imagesResponse = await client.images.generate({
      model: targetModel,
      prompt: prompt,
      size: "1024x1024", // Standardize size
      response_format: "url",
    });

    console.log('Image generation response:', JSON.stringify(imagesResponse));

    if (!imagesResponse.data || imagesResponse.data.length === 0) {
      throw new Error('No image generated');
    }

    const imageUrl = imagesResponse.data[0].url;

    return new Response(JSON.stringify({ url: imageUrl }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'Internal Server Error';
    console.error('Error generating image:', error);
    return new Response(JSON.stringify({ error: message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 500,
    });
  }
});
