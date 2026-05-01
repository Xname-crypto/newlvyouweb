const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

declare const Deno: {
  serve: (handler: (req: Request) => Promise<Response> | Response) => void;
  env: { get: (k: string) => string | undefined };
};

type Json = Record<string, unknown>;

const buildQS = (params: Record<string, string | number | undefined>) => {
  const p = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null) p.append(k, String(v));
  });
  return p.toString();
};

const amapFetch = async (base: string, params: Record<string, string | number | undefined>, key: string) => {
  const url = `${base}?${buildQS({ ...params, key })}`;
  const res = await fetch(url);
  const text = await res.text();
  try {
    const data = JSON.parse(text);
    return { ok: res.ok, data };
  } catch {
    return { ok: res.ok, data: { raw: text } };
  }
};

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }
  try {
    const key = Deno.env.get('AMAP_WEB_KEY');
    if (!key) {
      return new Response(JSON.stringify({ error: 'Missing AMAP_WEB_KEY' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500,
      });
    }
    const body = await req.json().catch(() => ({} as Json));
    const action = (body as Json)?.action as string | undefined;
    const params = ((body as Json)?.params as Record<string, string | number | undefined>) || {};

    if (!action) {
      return new Response(JSON.stringify({ error: 'Missing action' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400,
      });
    }

    if (action === 'nearby') {
      const location = params.location as string | undefined;
      const radius = params.radius ?? 2000;
      const types = params.types as string | undefined;
      if (!location) {
        return new Response(JSON.stringify({ error: 'Missing location' }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 400,
        });
      }
      const r = await amapFetch('https://restapi.amap.com/v3/place/around', { location, radius, types, output: 'JSON' }, key);
      return new Response(JSON.stringify(r.data), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
    }

    if (action === 'keyword') {
      const keywords = params.keywords as string | undefined;
      const city = params.city as string | undefined;
      if (!keywords) {
        return new Response(JSON.stringify({ error: 'Missing keywords' }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 400,
        });
      }
      const r = await amapFetch('https://restapi.amap.com/v3/place/text', { keywords, city, output: 'JSON' }, key);
      return new Response(JSON.stringify(r.data), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
    }

    if (action === 'regeo') {
      const location = params.location as string | undefined;
      if (!location) {
        return new Response(JSON.stringify({ error: 'Missing location' }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 400,
        });
      }
      const r = await amapFetch('https://restapi.amap.com/v3/geocode/regeo', { location, output: 'JSON' }, key);
      return new Response(JSON.stringify(r.data), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
    }

    if (action === 'geocode') {
      const address = params.address as string | undefined;
      const city = params.city as string | undefined;
      if (!address) {
        return new Response(JSON.stringify({ error: 'Missing address' }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 400,
        });
      }
      const r = await amapFetch('https://restapi.amap.com/v3/geocode/geo', { address, city, output: 'JSON' }, key);
      return new Response(JSON.stringify(r.data), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
    }

    if (action === 'district') {
      const keywords = params.keywords as string | undefined;
      const subdistrict = params.subdistrict ?? 0;
      const r = await amapFetch('https://restapi.amap.com/v3/config/district', { keywords, subdistrict, extensions: 'base', output: 'JSON' }, key);
      return new Response(JSON.stringify(r.data), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
    }

    if (action === 'route_driving') {
      const origin = params.origin as string | undefined;
      const destination = params.destination as string | undefined;
      const strategy = params.strategy ?? 0;
      if (!origin || !destination) {
        return new Response(JSON.stringify({ error: 'Missing origin or destination' }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 400,
        });
      }
      const r = await amapFetch('https://restapi.amap.com/v3/direction/driving', { origin, destination, strategy, extensions: 'base' }, key);
      return new Response(JSON.stringify(r.data), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
    }

    if (action === 'route_walking') {
      const origin = params.origin as string | undefined;
      const destination = params.destination as string | undefined;
      if (!origin || !destination) {
        return new Response(JSON.stringify({ error: 'Missing origin or destination' }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 400,
        });
      }
      const r = await amapFetch('https://restapi.amap.com/v3/direction/walking', { origin, destination }, key);
      return new Response(JSON.stringify(r.data), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
    }

    if (action === 'route_transit') {
      const origin = params.origin as string | undefined;
      const destination = params.destination as string | undefined;
      const city = params.city as string | undefined;
      if (!origin || !destination || !city) {
        return new Response(JSON.stringify({ error: 'Missing origin, destination or city' }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 400,
        });
      }
      const r = await amapFetch('https://restapi.amap.com/v3/direction/transit/integrated', { origin, destination, city }, key);
      return new Response(JSON.stringify(r.data), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
    }

    return new Response(JSON.stringify({ error: 'Unknown action' }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 400,
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return new Response(JSON.stringify({ error: msg }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 500,
    });
  }
});
