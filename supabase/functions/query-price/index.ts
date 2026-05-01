import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    // 12306 接口可能返回错误或非 JSON 数据，需要捕获异常并返回 500
    // 但是为了避免 CORS 错误（浏览器看到 500 会认为 CORS 失败如果 header 不对），
    // 即使出错，我们也应该尽量返回 200 并在 body 中包含错误信息，或者确保 500 响应也包含 CORS 头。
    
    const body = await req.json();
    const { train_no, from_station_no, to_station_no, seat_types, train_date } = body;

    if (!train_no || !from_station_no || !to_station_no || !seat_types || !train_date) {
      return new Response(
        JSON.stringify({ error: 'Missing required parameters' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    const url = `https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice?train_no=${train_no}&from_station_no=${from_station_no}&to_station_no=${to_station_no}&seat_types=${seat_types}&train_date=${train_date}`;
    
    console.log(`Querying price: ${url}`);

    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': 'https://kyfw.12306.cn/otn/leftTicket/init',
        'Cookie': 'JSESSIONID=00000000000000000000000000000000; route=00000000000000000000000000000000;'
      }
    });

    if (!response.ok) {
        throw new Error(`12306 API responded with ${response.status}`);
    }

    const data = await response.json();
    console.log('Price data received:', JSON.stringify(data).substring(0, 200));

    if (!data.data) {
        throw new Error('No price data returned from 12306');
    }

    return new Response(
      JSON.stringify({ data: data.data }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
    );

  } catch (error) {
    console.error('Error fetching price:', error);
    return new Response(
      JSON.stringify({ error: error.message }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    );
  }
});
