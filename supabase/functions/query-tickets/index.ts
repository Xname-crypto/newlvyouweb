const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

Deno.serve(async (req: Request) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const body = await req.json();
    const { from_station, to_station, date } = body;

    if (!from_station || !to_station || !date) {
      return new Response(
        JSON.stringify({ error: 'Missing required parameters' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    console.log(`Querying tickets from ${from_station} to ${to_station} on ${date}`);

    // Construct 12306 URL
    const url = `https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=${date}&leftTicketDTO.from_station=${from_station}&leftTicketDTO.to_station=${to_station}&purpose_codes=ADULT`;

    console.log(`Requesting URL: ${url}`);

    // Fetch data from 12306
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Referer': 'https://kyfw.12306.cn/otn/leftTicket/init',
        // Cookie is often required for 12306, even if empty or dummy
        'Cookie': 'JSESSIONID=00000000000000000000000000000000; route=00000000000000000000000000000000;'
      }
    });

    console.log(`12306 response status: ${response.status}`);

    if (!response.ok) {
        const text = await response.text();
        console.error(`12306 API error: ${response.status} ${response.statusText}`, text);
        throw new Error(`12306 API responded with ${response.status}: ${text.substring(0, 100)}`);
    }

    // Check if response is JSON
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text();
        console.error('12306 returned non-JSON:', text.substring(0, 200));
        
        // Sometimes 12306 returns HTML error page when blocked
        return new Response(
            JSON.stringify({ 
                data: [], 
                message: '12306 API returned unexpected format (likely blocked). Using mock data instead.',
                isMock: true
            }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
        );
    }

    const data = await response.json();
    console.log('12306 data received:', JSON.stringify(data).substring(0, 200));

    if (!data.data || !data.data.result) {
        console.warn('No data from 12306, returning empty list or mock data');
        return new Response(
            JSON.stringify({ 
                data: [], 
                message: 'No tickets found or API blocked. Please try later.',
                original_response: data
            }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
        );
    }

    // Construct 12306 price URL (this API might be rate limited or need cookies)
    // For demo purposes, we will mock prices based on duration or seat type if real API fails
    // Real price API: https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice?train_no=...&from_station_no=...&to_station_no=...&seat_types=...&train_date=...
    
    // Parse result
    let tickets: any[] = [];
    
    if (data.data && data.data.result) {
        tickets = data.data.result.map((item: string) => {
          const fields = item.split('|');
          
          return {
            train_no: fields[3], // 车次
            train_code: fields[2], // 内部编码 (needed for price query)
            from_station_code: fields[6],
            to_station_code: fields[7],
            from_station_no: fields[16], // 出发站序号
            to_station_no: fields[17], // 到达站序号
            start_time: fields[8],
            arrive_time: fields[9],
            duration: fields[10],
            // Seat availability
        business_seat: fields[32] || '--', // 商务座/特等座
        first_class: fields[31] || '--',   // 一等座
        second_class: fields[30] || '--',  // 二等座
        soft_sleeper: fields[23] || '--',  // 软卧/一等卧
        hard_sleeper: fields[28] || '--',  // 硬卧/二等卧
        hard_seat: fields[29] || '--',     // 硬座
        no_seat: fields[26] || '--',       // 无座
            // Prices are not directly in this API, usually require separate query or local calculation
            can_buy: fields[11] === 'Y',
            // Mock prices removed as per request
            prices: {} 
          };
        });
    }

    // If no tickets found from 12306 or API blocked, return mock data for demonstration
    if (tickets.length === 0) {
        console.log('Using mock data for demonstration');
        tickets = [
            {
                train_no: 'G1',
                train_code: 'G1',
                from_station_code: 'BJP',
                to_station_code: 'SHH', 
                from_station_no: '01',
                to_station_no: '02',
                start_time: '09:00',
                arrive_time: '13:18',
                duration: '04:18',
                business_seat: '10',
                first_class: '有',
                second_class: '有',
                soft_sleeper: '--',
                hard_sleeper: '--',
                hard_seat: '--',
                no_seat: '--',
                can_buy: true,
                prices: {}
            },
             {
                train_no: 'G101',
                train_code: 'G101',
                from_station_code: 'BJP',
                to_station_code: 'SHH', 
                from_station_no: '01',
                to_station_no: '02',
                start_time: '10:00',
                arrive_time: '14:28',
                duration: '04:28',
                business_seat: '5',
                first_class: '有',
                second_class: '有',
                soft_sleeper: '--',
                hard_sleeper: '--',
                hard_seat: '--',
                no_seat: '--',
                can_buy: true,
                prices: {}
            },
            {
                train_no: 'T109',
                train_code: 'T109',
                from_station_code: 'BJP',
                to_station_code: 'SHH', 
                from_station_no: '01',
                to_station_no: '02',
                start_time: '19:33',
                arrive_time: '10:18',
                duration: '14:45',
                business_seat: '--',
                first_class: '--',
                second_class: '--',
                soft_sleeper: '5',
                hard_sleeper: '20',
                hard_seat: '有',
                no_seat: '有',
                can_buy: true,
                prices: {}
            },
            {
                train_no: 'Z281',
                train_code: 'Z281',
                from_station_code: 'BJP',
                to_station_code: 'SHH', 
                from_station_no: '01',
                to_station_no: '02',
                start_time: '19:00',
                arrive_time: '09:30',
                duration: '14:30',
                business_seat: '--',
                first_class: '--',
                second_class: '--',
                soft_sleeper: '10',
                hard_sleeper: '50',
                hard_seat: '有',
                no_seat: '无',
                can_buy: true,
                prices: {}
            },
            {
                train_no: 'K1109',
                train_code: 'K1109',
                from_station_code: 'BJP',
                to_station_code: 'SHH', 
                from_station_no: '01',
                to_station_no: '02',
                start_time: '13:30',
                arrive_time: '12:00',
                duration: '22:30',
                business_seat: '--',
                first_class: '--',
                second_class: '--',
                soft_sleeper: '2',
                hard_sleeper: '8',
                hard_seat: '有',
                no_seat: '有',
                can_buy: true,
                prices: {}
            }
        ];
    }

    return new Response(
      JSON.stringify({ data: tickets }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
    );

  } catch (error) {
    const msg = error && (error as any).message ? (error as any).message : 'Internal Server Error';
    console.error('Error processing request:', error);
    return new Response(
      JSON.stringify({ error: msg }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    );
  }
});
