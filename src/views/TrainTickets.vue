<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { ArrowDown, Search, ArrowRightLeft, User, Calendar, Clock, Armchair } from 'lucide-vue-next';
import Navigation from '@/components/Navigation.vue';
import SocialSidebar from '@/components/SocialSidebar.vue';
import Footer from '@/components/Footer.vue';
import { supabase } from '@/utils/supabase';
import { cityMap } from '@/utils/cityData';

const scrollY = ref(0);
const trainHeroImage = 'https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?q=72&w=1600&auto=format&fit=crop&fm=webp';
const fromStation = ref('北京');
const toStation = ref('上海');
const date = ref('');
const tickets = ref<any[]>([]);
const loading = ref(false);
const error = ref('');

// Advanced Search Filters
const isRoundTrip = ref(false);
const returnDate = ref('');
const passengerType = ref('ADULT'); // ADULT, STUDENT
const hasInfant = ref(false);
const sortBy = ref('time'); // time, duration, price
const filterSeat = ref('all'); // all, business, first, second

// Set default dates
const tomorrow = new Date();
tomorrow.setDate(tomorrow.getDate() + 1);
date.value = tomorrow.toISOString().split('T')[0];

const dayAfterTomorrow = new Date();
dayAfterTomorrow.setDate(dayAfterTomorrow.getDate() + 2);
returnDate.value = dayAfterTomorrow.toISOString().split('T')[0];

const handleScroll = () => {
  scrollY.value = window.scrollY;
};

const swapStations = () => {
  const temp = fromStation.value;
  fromStation.value = toStation.value;
  toStation.value = temp;
};

const getTrainType = (trainNo: string) => {
  const code = trainNo.charAt(0);
  if (code === 'G') return '高速动车';
  if (code === 'D') return '动车组';
  if (code === 'C') return '城际列车';
  if (code === 'Z') return '直达特快';
  if (code === 'T') return '特快';
  if (code === 'K') return '快速';
  return '普快';
};

const getSeatClass = (seatStatus: string) => {
  if (seatStatus === '--' || seatStatus === '无') {
    return 'text-white/20';
  }
  // Check if seatStatus is a number (available count) or "有"
  const count = parseInt(seatStatus);
  if (seatStatus === '有' || (!isNaN(count) && count > 0)) {
    return 'text-accent';
  }
  return 'text-white/20';
};

const sortedTickets = computed(() => {
  let result = [...tickets.value];
  
  // Filter by seat availability
  if (filterSeat.value !== 'all') {
    const seatMap: Record<string, string> = {
      business: 'business_seat',
      first: 'first_class',
      second: 'second_class',
      soft_sleeper: 'soft_sleeper',
      hard_sleeper: 'hard_sleeper',
      hard_seat: 'hard_seat'
    };
    result = result.filter(t => {
      const key = seatMap[filterSeat.value];
      return key ? t[key] !== '--' && t[key] !== '无' && t[key] !== '0' : true;
    });
  }

  // Sort
  if (sortBy.value === 'time') {
    result.sort((a, b) => a.start_time.localeCompare(b.start_time));
  } else if (sortBy.value === 'duration') {
    result.sort((a, b) => a.duration.localeCompare(b.duration));
  }
  
  return result;
});

const fetchRealPrice = async (ticket: any, seatType: string) => {
  // If price is already fetching or fetched and is not a mock price (mock prices usually start with ¥)
  // Actually, mock prices also start with ¥, so we might need a flag.
  // But here we can just force fetch on click.
  
  if (!ticket.realPrices) {
    ticket.realPrices = {};
    ticket.priceLoading = {};
  }
  
  if (ticket.priceLoading[seatType]) return;

  ticket.priceLoading[seatType] = true;

  try {
    // Map internal seat types: second=O, first=M, business=9, hard_sleeper=3, etc.
    // 12306 seat types: 
    // Business: 9, First: M, Second: O, Hard Sleeper: 3, Soft Sleeper: 4, Hard Seat: 1
    const seatTypeMap: Record<string, string> = {
      'business': '9',
      'first': 'M',
      'second': 'O',
      'hard_sleeper': '3',
      'soft_sleeper': '4',
      'hard_seat': '1',
      'no_seat': 'WZ',
      // D train sleeper mappings
      'dong_wo': 'F', // 动卧 commonly maps to F or 4 depending on train type, try F for now
      'gao_ji_ruan_wo': '6' // 高级软卧
    };

    const { data, error: err } = await supabase.functions.invoke('query-price', {
      body: {
        // Note: use internal code for price query
        // Wait, query-tickets returns train_no as '5l0000G53170', and train_code as 'G531'
        // Let's check what we saved in query-tickets
        // In previous step we saved: train_no: fields[3] (e.g. G531), train_code: fields[2] (internal code)
        // Actually fields[2] is internal code (e.g. 2400000G330A), fields[3] is visible code (e.g. G33)
        // We need the internal code for price query.
        train_no: ticket.train_code, 
        from_station_no: ticket.from_station_no || '01', // We need these fields from query-tickets
        to_station_no: ticket.to_station_no || '02',
        seat_types: seatTypeMap[seatType] || 'O',
        train_date: date.value
      }
    });

    if (err) throw err;
    if (data.error) throw new Error(data.error);

    // Update price
    // The API returns prices for all seats usually
    // data.data is the object with prices
    // Format: { A9: "¥1748.0", M: "¥933.0", O: "¥553.0" }
    
    const priceMap: Record<string, string> = {
        'A9': 'business',
        '9': 'business',
        'M': 'first',
        'O': 'second',
        '3': 'hard_sleeper',
        '4': 'soft_sleeper',
      'F': 'soft_sleeper', // Map 'F' (动卧) to soft_sleeper for display consistency
      '1': 'hard_seat',
      'WZ': 'no_seat'
    };

    Object.keys(data.data).forEach(key => {
        const type = priceMap[key];
        if (type) {
            ticket.prices[type] = data.data[key];
            // Mark as real
            if (!ticket.isRealPrice) ticket.isRealPrice = {};
            ticket.isRealPrice[type] = true;
        } else if (key === 'WZ') {
             ticket.prices['no_seat'] = data.data[key];
             if (!ticket.isRealPrice) ticket.isRealPrice = {};
             ticket.isRealPrice['no_seat'] = true;
        }
    });

  } catch (err: any) {
    console.error('Failed to fetch real price', err);
    // If real price fails, show error in UI or leave as is (loading stops)
    // We do NOT fallback to mock price as requested.
    // Optionally we could set an error state for this specific seat
    ticket.prices[seatType] = '查询失败';
  } finally {
    ticket.priceLoading[seatType] = false;
  }
};

const queryTickets = async () => {
  if (!fromStation.value || !toStation.value || !date.value) {
    error.value = '请填写完整查询信息';
    return;
  }

  // Get station codes from city names
  const fromCode = cityMap[fromStation.value];
  const toCode = cityMap[toStation.value];

  if (!fromCode) {
    error.value = `未找到出发地 "${fromStation.value}"，请检查输入`;
    return;
  }

  if (!toCode) {
    error.value = `未找到目的地 "${toStation.value}"，请检查输入`;
    return;
  }

  if (isRoundTrip.value && !returnDate.value) {
    error.value = '请选择返程日期';
    return;
  }

  loading.value = true;
  error.value = '';
  tickets.value = [];

  // Log search asynchronously
  try {
    const { data: { user } } = await supabase.auth.getUser();
    supabase.from('search_logs').insert({
      user_id: user?.id,
      search_type: 'train_ticket',
      content: {
        from: fromStation.value,
        to: toStation.value,
        date: date.value,
        return_date: isRoundTrip.value ? returnDate.value : null,
        passenger_type: passengerType.value
      }
    }).then(({ error }) => {
      if (error) console.error('Search logging failed:', error);
    });
  } catch (e) {
    console.warn('Search logging error:', e);
  }

  try {
    const { data, error: err } = await supabase.functions.invoke('query-tickets', {
      body: {
        from_station: fromCode,
        to_station: toCode,
        date: date.value,
        passenger_type: passengerType.value
      }
    });

    if (err) throw err;
    if (data.error) throw new Error(data.error);
    
    if (data.message && !data.data?.length) {
      error.value = data.message;
    } else {
      tickets.value = data.data || [];
    }
  } catch (err: any) {
    console.error('Error querying tickets:', err);
    error.value = err.message || '查询失败，请稍后重试';
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  const link = document.createElement('link');
  link.rel = 'preload';
  link.as = 'image';
  link.href = trainHeroImage;
  document.head.appendChild(link);
  window.addEventListener('scroll', handleScroll);
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
});
</script>

<template>
  <div class="bg-primary min-h-screen text-text-main overflow-x-hidden selection:bg-accent selection:text-primary">
    <Navigation>
      <template #logo>
        <router-link to="/" class="text-text-main font-bold text-4xl tracking-wide" style="font-family: 'PangMenZhengDao', serif;">
          椿天社
        </router-link>
      </template>
    </Navigation>
    <SocialSidebar />

    <main>
      <!-- Hero Section -->
      <div class="relative w-full h-[800px] overflow-hidden flex flex-col items-center pt-32 lg:pt-64">
        <!-- Background Image with Parallax -->
        <div 
          class="absolute top-0 left-0 w-full h-full z-0 bg-cover bg-center pointer-events-none"
          :style="{ 
            transform: `translateY(${scrollY * 0.5}px)`
          }"
        >
          <img
            class="absolute inset-0 h-full w-full object-cover"
            :src="trainHeroImage"
            alt=""
            decoding="async"
            fetchpriority="high"
            loading="eager"
          />
          <!-- Gradient Overlays -->
          <div class="absolute inset-0 bg-gradient-to-b from-transparent via-primary/30 to-primary"></div>
          <div class="absolute inset-0 bg-gradient-to-t from-primary via-transparent to-transparent opacity-80"></div>
        </div>

        <!-- Content -->
        <div class="relative z-10 container mx-auto px-4 lg:px-20 flex flex-col items-start max-w-5xl">
          <div class="flex items-center gap-4 mb-8">
            <div class="w-[72px] h-[2px] bg-accent"></div>
            <span class="text-accent font-bold tracking-[6px] uppercase text-lg font-sans">出行助手</span>
          </div>
          
          <h1 class="text-text-main font-serif text-5xl md:text-7xl lg:text-[88px] leading-tight mb-8 capitalize">
            探索世界，<br />从一张车票开始
          </h1>
          
          <div class="flex items-center gap-4 text-text-main font-bold cursor-pointer mt-8 animate-bounce">
            <span>开始查询</span>
            <ArrowDown :size="20" />
          </div>
        </div>
      </div>

      <!-- Search Section -->
      <div class="relative z-20 -mt-32 pb-32 bg-gradient-to-b from-transparent to-primary min-h-[600px]">
        <div class="container mx-auto px-4 lg:px-20">
          <!-- Search Box -->
          <div class="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-8 max-w-5xl mx-auto shadow-2xl">
            <!-- Trip Type & Passenger Toggle -->
            <div class="flex items-center gap-6 mb-6">
              <div class="flex bg-white/5 rounded-lg p-1">
                <button 
                  @click="isRoundTrip = false"
                  :class="['px-4 py-1.5 rounded-md text-sm font-bold transition-all', !isRoundTrip ? 'bg-accent text-primary' : 'text-white/70 hover:text-white']"
                >
                  单程
                </button>
                <button 
                  @click="isRoundTrip = true"
                  :class="['px-4 py-1.5 rounded-md text-sm font-bold transition-all', isRoundTrip ? 'bg-accent text-primary' : 'text-white/70 hover:text-white']"
                >
                  往返
                </button>
              </div>

              <div class="flex items-center gap-4">
                <label class="flex items-center gap-2 cursor-pointer group">
                  <input type="checkbox" v-model="passengerType" true-value="STUDENT" false-value="ADULT" class="hidden">
                  <div :class="['w-4 h-4 rounded border flex items-center justify-center transition-colors', passengerType === 'STUDENT' ? 'bg-accent border-accent' : 'border-white/30 group-hover:border-accent']">
                    <div v-if="passengerType === 'STUDENT'" class="w-2 h-2 bg-primary rounded-sm"></div>
                  </div>
                  <span class="text-white/80 text-sm font-sans group-hover:text-white">学生票</span>
                </label>

                <label class="flex items-center gap-2 cursor-pointer group">
                  <input type="checkbox" v-model="hasInfant" class="hidden">
                  <div :class="['w-4 h-4 rounded border flex items-center justify-center transition-colors', hasInfant ? 'bg-accent border-accent' : 'border-white/30 group-hover:border-accent']">
                    <div v-if="hasInfant" class="w-2 h-2 bg-primary rounded-sm"></div>
                  </div>
                  <span class="text-white/80 text-sm font-sans group-hover:text-white">携带婴儿</span>
                </label>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
              <!-- Stations -->
              <div class="md:col-span-5 flex items-end gap-2 relative">
                <div class="flex-1 space-y-2">
                  <label class="text-xs font-bold text-accent uppercase tracking-wider flex items-center gap-1">
                    <div class="w-1.5 h-1.5 rounded-full bg-accent"></div> 出发地
                  </label>
                  <input 
                    v-model="fromStation"
                    type="text" 
                    list="station-list"
                    placeholder="北京"
                    class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-accent transition-colors font-sans"
                  >
                </div>
                
                <button 
                  @click="swapStations"
                  class="mb-3 p-2 rounded-full bg-white/5 hover:bg-accent hover:text-primary text-white/50 transition-all border border-white/10"
                  title="互换出发/到达地"
                >
                  <ArrowRightLeft :size="16" />
                </button>

                <div class="flex-1 space-y-2">
                  <label class="text-xs font-bold text-accent uppercase tracking-wider flex items-center gap-1">
                    <div class="w-1.5 h-1.5 rounded-full bg-red-400"></div> 目的地
                  </label>
                  <input 
                    v-model="toStation"
                    type="text" 
                    list="station-list"
                    placeholder="上海"
                    class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-accent transition-colors font-sans"
                  >
                </div>
                
                <datalist id="station-list">
                  <option v-for="(_, name) in cityMap" :key="name" :value="name"></option>
                </datalist>
              </div>
              
              <!-- Dates -->
              <div class="md:col-span-5 flex gap-4">
                <div class="flex-1 space-y-2">
                  <label class="text-xs font-bold text-accent uppercase tracking-wider flex items-center gap-1">
                    <Calendar :size="12" /> 出发日期
                  </label>
                  <input 
                    v-model="date"
                    type="date" 
                    class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-accent transition-colors font-sans"
                  >
                </div>
                
                <div v-if="isRoundTrip" class="flex-1 space-y-2">
                  <label class="text-xs font-bold text-accent uppercase tracking-wider flex items-center gap-1">
                    <Calendar :size="12" /> 返程日期
                  </label>
                  <input 
                    v-model="returnDate"
                    type="date" 
                    class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-accent transition-colors font-sans"
                  >
                </div>
              </div>
              
              <!-- Search Button -->
              <div class="md:col-span-2">
                <button 
                  @click="queryTickets"
                  :disabled="loading"
                  class="w-full bg-accent text-primary font-bold py-3.5 rounded-lg hover:bg-accent/90 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-accent/20"
                >
                  <Search v-if="!loading" :size="20" />
                  <span v-else class="animate-spin w-5 h-5 border-2 border-primary border-t-transparent rounded-full"></span>
                  {{ loading ? '查询' : '查询车票' }}
                </button>
              </div>
            </div>
            
            <p class="text-white/40 text-xs mt-4 flex justify-between">
              <span>热门城市：北京, 上海, 广州, 深圳, 杭州, 武汉, 成都, 西安</span>
              <span v-if="passengerType === 'STUDENT'" class="text-accent">已开启学生票查询</span>
            </p>
          </div>

          <!-- Filters & Sort (Visible only when results exist) -->
          <div v-if="tickets.length > 0" class="max-w-6xl mx-auto mt-8 flex flex-wrap items-center justify-between gap-4 bg-white/5 p-4 rounded-xl border border-white/10">
            <div class="flex items-center gap-4">
              <span class="text-sm font-bold text-white/70">排序方式:</span>
              <button 
                @click="sortBy = 'time'"
                :class="['px-3 py-1.5 rounded text-sm transition-colors flex items-center gap-1', sortBy === 'time' ? 'bg-white/20 text-white' : 'text-white/50 hover:text-white']"
              >
                <Clock :size="14" /> 发车时间
              </button>
              <button 
                @click="sortBy = 'duration'"
                :class="['px-3 py-1.5 rounded text-sm transition-colors flex items-center gap-1', sortBy === 'duration' ? 'bg-white/20 text-white' : 'text-white/50 hover:text-white']"
              >
                <Clock :size="14" /> 历时最短
              </button>
            </div>

            <div class="flex items-center gap-4">
              <span class="text-sm font-bold text-white/70">只看有票:</span>
              <div class="relative">
                <select v-model="filterSeat" class="appearance-none bg-white/10 border border-white/10 rounded px-4 py-2 pr-8 text-sm text-white focus:outline-none focus:border-accent hover:bg-white/20 transition-colors cursor-pointer min-w-[120px]">
                  <option value="all" class="text-gray-900">全部席别</option>
                  <option value="second" class="text-gray-900">二等座</option>
                  <option value="first" class="text-gray-900">一等座</option>
                  <option value="business" class="text-gray-900">商务座</option>
                  <option value="hard_sleeper" class="text-gray-900">硬卧</option>
                  <option value="soft_sleeper" class="text-gray-900">软卧</option>
                  <option value="hard_seat" class="text-gray-900">硬座</option>
                </select>
                <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-white/50">
                  <ArrowDown :size="14" />
                </div>
              </div>
            </div>
            
            <div class="text-sm text-white/50">
              共找到 <span class="text-accent font-bold">{{ sortedTickets.length }}</span> 个车次
            </div>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="max-w-4xl mx-auto mt-8 p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-200 text-center">
            {{ error }}
          </div>

          <!-- Results List -->
          <div v-if="tickets.length > 0" class="max-w-6xl mx-auto mt-12 space-y-4">
            <div class="grid grid-cols-1 gap-4">
              <div v-for="(ticket, index) in sortedTickets" :key="index" class="bg-white/5 border border-white/10 rounded-xl p-6 hover:bg-white/10 transition-colors group">
                <div class="flex flex-col md:flex-row items-center justify-between gap-6">
                  <!-- Train Info -->
                  <div class="flex items-center gap-8 w-full md:w-auto">
                    <div class="text-center w-24">
                      <div class="text-2xl font-bold text-white">{{ ticket.train_no }}</div>
                      <div class="text-sm text-accent mt-1 group-hover:text-accent/80">{{ getTrainType(ticket.train_no) }}</div>
                    </div>
                    
                    <div class="flex items-center gap-4 flex-1">
                      <div class="text-center">
                        <div class="text-xl font-bold text-white">{{ ticket.start_time }}</div>
                        <div class="text-xs text-white/50">{{ fromStation }}</div>
                      </div>
                      
                      <div class="flex flex-col items-center px-4">
                        <div class="text-xs text-white/30 mb-1">{{ ticket.duration }}</div>
                        <div class="w-20 h-[2px] bg-white/20 relative">
                          <div class="absolute right-0 top-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-white/20 rounded-full"></div>
                        </div>
                      </div>
                      
                      <div class="text-center">
                        <div class="text-xl font-bold text-white">{{ ticket.arrive_time }}</div>
                        <div class="text-xs text-white/50">{{ ticket.to_station_code }}</div>
                      </div>
                    </div>
                  </div>

                  <!-- Seats -->
                  <div class="grid grid-cols-4 gap-4 w-full md:w-auto text-center text-sm">
                    <!-- G/D/C Train Seats -->
                    <template v-if="['G', 'D', 'C'].includes(ticket.train_no.charAt(0))">
                      <!-- 商务座 -->
                      <div 
                          v-if="ticket.business_seat !== '--'"
                          class="space-y-1 relative group/seat cursor-pointer flex flex-col items-center justify-center min-w-[60px]"
                          @click="fetchRealPrice(ticket, 'business')"
                      >
                        <div class="text-white/50">商务座</div>
                        <div :class="getSeatClass(ticket.business_seat)">
                          {{ ticket.business_seat }}
                        </div>
                        <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-xs rounded opacity-0 group-hover/seat:opacity-100 transition-opacity whitespace-nowrap pointer-events-none shadow-xl border border-white/10 z-10 flex items-center gap-2">
                          <span v-if="ticket.priceLoading?.business" class="animate-spin w-3 h-3 border-2 border-white/30 border-t-white rounded-full"></span>
                          <span v-else>{{ ticket.prices?.business || '--' }}</span>
                          <span v-if="ticket.isRealPrice?.business" class="text-[10px] text-green-400 bg-green-400/10 px-1 rounded">实</span>
                          <div class="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
                        </div>
                      </div>

                      <!-- 一等座 -->
                      <div 
                          v-if="ticket.first_class !== '--'"
                          class="space-y-1 relative group/seat cursor-pointer flex flex-col items-center justify-center min-w-[60px]"
                          @click="fetchRealPrice(ticket, 'first')"
                      >
                        <div class="text-white/50">一等座</div>
                        <div :class="getSeatClass(ticket.first_class)">
                          {{ ticket.first_class }}
                        </div>
                        <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-xs rounded opacity-0 group-hover/seat:opacity-100 transition-opacity whitespace-nowrap pointer-events-none shadow-xl border border-white/10 z-10 flex items-center gap-2">
                          <span v-if="ticket.priceLoading?.first" class="animate-spin w-3 h-3 border-2 border-white/30 border-t-white rounded-full"></span>
                          <span v-else>{{ ticket.prices?.first || '--' }}</span>
                          <span v-if="ticket.isRealPrice?.first" class="text-[10px] text-green-400 bg-green-400/10 px-1 rounded">实</span>
                          <div class="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
                        </div>
                      </div>

                      <!-- 二等座 -->
                      <div 
                          v-if="ticket.second_class !== '--'"
                          class="space-y-1 relative group/seat cursor-pointer flex flex-col items-center justify-center min-w-[60px]"
                          @click="fetchRealPrice(ticket, 'second')"
                      >
                        <div class="text-white/50">二等座</div>
                        <div :class="getSeatClass(ticket.second_class)">
                          {{ ticket.second_class }}
                        </div>
                        <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-xs rounded opacity-0 group-hover/seat:opacity-100 transition-opacity whitespace-nowrap pointer-events-none shadow-xl border border-white/10 z-10 flex items-center gap-2">
                          <span v-if="ticket.priceLoading?.second" class="animate-spin w-3 h-3 border-2 border-white/30 border-t-white rounded-full"></span>
                          <span v-else>{{ ticket.prices?.second || '--' }}</span>
                          <span v-if="ticket.isRealPrice?.second" class="text-[10px] text-green-400 bg-green-400/10 px-1 rounded">实</span>
                          <div class="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
                        </div>
                      </div>

                      <!-- 软卧/动卧 -->
                      <div 
                          v-if="ticket.soft_sleeper !== '--'"
                          class="space-y-1 relative group/seat cursor-pointer flex flex-col items-center justify-center min-w-[60px]"
                          @click="fetchRealPrice(ticket, 'soft_sleeper')"
                      >
                        <div class="text-white/50">软卧/动卧</div>
                        <div :class="getSeatClass(ticket.soft_sleeper)">
                          {{ ticket.soft_sleeper }}
                        </div>
                        <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-xs rounded opacity-0 group-hover/seat:opacity-100 transition-opacity whitespace-nowrap pointer-events-none shadow-xl border border-white/10 z-10 flex items-center gap-2">
                          <span v-if="ticket.priceLoading?.soft_sleeper" class="animate-spin w-3 h-3 border-2 border-white/30 border-t-white rounded-full"></span>
                          <span v-else>{{ ticket.prices?.soft_sleeper || '--' }}</span>
                          <span v-if="ticket.isRealPrice?.soft_sleeper" class="text-[10px] text-green-400 bg-green-400/10 px-1 rounded">实</span>
                          <div class="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
                        </div>
                      </div>

                      <!-- 硬卧 -->
                      <div 
                          v-if="ticket.hard_sleeper !== '--'"
                          class="space-y-1 relative group/seat cursor-pointer flex flex-col items-center justify-center min-w-[60px]"
                          @click="fetchRealPrice(ticket, 'hard_sleeper')"
                      >
                        <div class="text-white/50">硬卧</div>
                        <div :class="getSeatClass(ticket.hard_sleeper)">
                          {{ ticket.hard_sleeper }}
                        </div>
                        <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-xs rounded opacity-0 group-hover/seat:opacity-100 transition-opacity whitespace-nowrap pointer-events-none shadow-xl border border-white/10 z-10 flex items-center gap-2">
                          <span v-if="ticket.priceLoading?.hard_sleeper" class="animate-spin w-3 h-3 border-2 border-white/30 border-t-white rounded-full"></span>
                          <span v-else>{{ ticket.prices?.hard_sleeper || '--' }}</span>
                          <span v-if="ticket.isRealPrice?.hard_sleeper" class="text-[10px] text-green-400 bg-green-400/10 px-1 rounded">实</span>
                          <div class="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
                        </div>
                      </div>
                      
                       <!-- 无座 -->
                       <div 
                          v-if="ticket.no_seat !== '--'"
                          class="space-y-1 relative group/seat cursor-pointer flex flex-col items-center justify-center min-w-[60px]"
                          @click="fetchRealPrice(ticket, 'no_seat')"
                      >
                        <div class="text-white/50">无座</div>
                        <div :class="getSeatClass(ticket.no_seat)">
                          {{ ticket.no_seat }}
                        </div>
                        <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-xs rounded opacity-0 group-hover/seat:opacity-100 transition-opacity whitespace-nowrap pointer-events-none shadow-xl border border-white/10 z-10 flex items-center gap-2">
                          <span v-if="ticket.priceLoading?.no_seat" class="animate-spin w-3 h-3 border-2 border-white/30 border-t-white rounded-full"></span>
                          <span v-else>{{ ticket.prices?.no_seat || '--' }}</span>
                          <span v-if="ticket.isRealPrice?.no_seat" class="text-[10px] text-green-400 bg-green-400/10 px-1 rounded">实</span>
                          <div class="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
                        </div>
                      </div>
                    </template>

                    <!-- Z/T/K/Other Train Seats -->
                    <template v-else>
                      <!-- 硬卧 -->
                      <div 
                          class="space-y-1 relative group/seat cursor-pointer flex flex-col items-center justify-center min-w-[60px]"
                          @click="ticket.hard_sleeper !== '--' && fetchRealPrice(ticket, 'hard_sleeper')"
                      >
                        <div class="text-white/50">硬卧</div>
                        <div :class="getSeatClass(ticket.hard_sleeper)">
                          {{ ticket.hard_sleeper === '--' ? '无' : ticket.hard_sleeper }}
                        </div>
                        <div v-if="ticket.hard_sleeper !== '--'" class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-xs rounded opacity-0 group-hover/seat:opacity-100 transition-opacity whitespace-nowrap pointer-events-none shadow-xl border border-white/10 z-10 flex items-center gap-2">
                          <span v-if="ticket.priceLoading?.hard_sleeper" class="animate-spin w-3 h-3 border-2 border-white/30 border-t-white rounded-full"></span>
                          <span v-else>{{ ticket.prices?.hard_sleeper || '--' }}</span>
                          <span v-if="ticket.isRealPrice?.hard_sleeper" class="text-[10px] text-green-400 bg-green-400/10 px-1 rounded">实</span>
                          <div class="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
                        </div>
                      </div>

                      <!-- 软卧 -->
                      <div 
                          class="space-y-1 relative group/seat cursor-pointer flex flex-col items-center justify-center min-w-[60px]"
                          @click="ticket.soft_sleeper !== '--' && fetchRealPrice(ticket, 'soft_sleeper')"
                      >
                        <div class="text-white/50">软卧</div>
                        <div :class="getSeatClass(ticket.soft_sleeper)">
                          {{ ticket.soft_sleeper === '--' ? '无' : ticket.soft_sleeper }}
                        </div>
                        <div v-if="ticket.soft_sleeper !== '--'" class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-xs rounded opacity-0 group-hover/seat:opacity-100 transition-opacity whitespace-nowrap pointer-events-none shadow-xl border border-white/10 z-10 flex items-center gap-2">
                          <span v-if="ticket.priceLoading?.soft_sleeper" class="animate-spin w-3 h-3 border-2 border-white/30 border-t-white rounded-full"></span>
                          <span v-else>{{ ticket.prices?.soft_sleeper || '--' }}</span>
                          <span v-if="ticket.isRealPrice?.soft_sleeper" class="text-[10px] text-green-400 bg-green-400/10 px-1 rounded">实</span>
                          <div class="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
                        </div>
                      </div>

                      <!-- 硬座 -->
                      <div 
                          class="space-y-1 relative group/seat cursor-pointer flex flex-col items-center justify-center min-w-[60px]"
                          @click="ticket.hard_seat !== '--' && fetchRealPrice(ticket, 'hard_seat')"
                      >
                        <div class="text-white/50">硬座</div>
                        <div :class="getSeatClass(ticket.hard_seat)">
                          {{ ticket.hard_seat === '--' ? '无' : ticket.hard_seat }}
                        </div>
                        <div v-if="ticket.hard_seat !== '--'" class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-xs rounded opacity-0 group-hover/seat:opacity-100 transition-opacity whitespace-nowrap pointer-events-none shadow-xl border border-white/10 z-10 flex items-center gap-2">
                          <span v-if="ticket.priceLoading?.hard_seat" class="animate-spin w-3 h-3 border-2 border-white/30 border-t-white rounded-full"></span>
                          <span v-else>{{ ticket.prices?.hard_seat || '--' }}</span>
                          <span v-if="ticket.isRealPrice?.hard_seat" class="text-[10px] text-green-400 bg-green-400/10 px-1 rounded">实</span>
                          <div class="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
                        </div>
                      </div>

                      <!-- 无座 -->
                      <div 
                          class="space-y-1 relative group/seat cursor-pointer flex flex-col items-center justify-center min-w-[60px]"
                          @click="ticket.no_seat !== '--' && fetchRealPrice(ticket, 'no_seat')"
                      >
                        <div class="text-white/50">无座</div>
                        <div :class="getSeatClass(ticket.no_seat)">
                          {{ ticket.no_seat === '--' ? '无' : ticket.no_seat }}
                        </div>
                        <div v-if="ticket.no_seat !== '--'" class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-xs rounded opacity-0 group-hover/seat:opacity-100 transition-opacity whitespace-nowrap pointer-events-none shadow-xl border border-white/10 z-10 flex items-center gap-2">
                          <span v-if="ticket.priceLoading?.no_seat" class="animate-spin w-3 h-3 border-2 border-white/30 border-t-white rounded-full"></span>
                          <span v-else>{{ ticket.prices?.no_seat || '--' }}</span>
                          <span v-if="ticket.isRealPrice?.no_seat" class="text-[10px] text-green-400 bg-green-400/10 px-1 rounded">实</span>
                          <div class="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
                        </div>
                      </div>
                    </template>
                  </div>

                  <!-- Action -->
                  <div class="w-full md:w-auto">
                    <button 
                      :disabled="!ticket.can_buy"
                      :class="[
                        'w-full md:w-32 py-2.5 rounded font-bold text-sm transition-all',
                        ticket.can_buy 
                          ? 'bg-accent text-primary hover:bg-accent/90' 
                          : 'bg-white/10 text-white/30 cursor-not-allowed'
                      ]"
                    >
                      {{ ticket.can_buy ? '预订' : '不可订' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <Footer />
  </div>
</template>
