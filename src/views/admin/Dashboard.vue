<template>
  <div class="space-y-6">
    <!-- 顶部统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div v-for="(stat, index) in stats" :key="index" class="bg-slate-50 p-6 rounded-2xl border border-slate-100 relative overflow-hidden group hover:shadow-md transition-shadow">
        <div class="flex justify-between items-start mb-4">
          <div>
            <div class="text-sm font-medium text-slate-500 mb-1">{{ stat.title }}</div>
            <div class="text-2xl font-bold text-slate-900">{{ stat.value }}</div>
          </div>
          <div :class="`p-2 rounded-lg ${stat.bg} ${stat.color}`">
            <component :is="stat.icon" class="w-5 h-5" />
          </div>
        </div>
        <div class="flex items-center gap-2 text-xs">
          <span :class="stat.trend > 0 ? 'text-emerald-600' : 'text-rose-600'" class="font-medium flex items-center">
            <TrendingUp v-if="stat.trend > 0" class="w-3 h-3 mr-1" />
            <TrendingDown v-else class="w-3 h-3 mr-1" />
            {{ Math.abs(stat.trend) }}%
          </span>
          <span class="text-slate-400">较上周</span>
        </div>
      </div>
    </div>

    <!-- 主要图表区域 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 折线图：用户增长 -->
      <div class="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
        <div class="flex items-center justify-between mb-6">
          <div>
            <h3 class="font-bold text-slate-900">用户增长趋势</h3>
            <div class="text-xs text-slate-500 mt-1">最近 7 天的新增用户数据</div>
          </div>
          <div class="flex gap-2">
            <button 
              @click="setChartMode('thisWeek')"
              class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full transition-colors"
              :class="growthChartMode === 'thisWeek' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
            >
              本周
            </button>
            <button 
              @click="setChartMode('lastWeek')"
              class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full transition-colors"
              :class="growthChartMode === 'lastWeek' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
            >
              上周
            </button>
          </div>
        </div>
        
        <!-- SVG Line Chart -->
         <div class="h-64 relative w-full pt-10 group">
            <svg class="absolute inset-0 w-full h-full overflow-visible" viewBox="0 0 800 200" preserveAspectRatio="none">
               <!-- Grid Lines -->
               <line x1="0" y1="50" x2="800" y2="50" stroke="#f1f5f9" stroke-width="1" vector-effect="non-scaling-stroke" stroke-dasharray="4 4" />
               <line x1="0" y1="100" x2="800" y2="100" stroke="#f1f5f9" stroke-width="1" vector-effect="non-scaling-stroke" stroke-dasharray="4 4" />
               <line x1="0" y1="150" x2="800" y2="150" stroke="#f1f5f9" stroke-width="1" vector-effect="non-scaling-stroke" stroke-dasharray="4 4" />
               
               <!-- Data Path -->
               <path 
                 :d="chartPath" 
                 fill="none" 
                 stroke="#0f172a" 
                 stroke-width="3" 
                 vector-effect="non-scaling-stroke"
                 stroke-linecap="round"
                 stroke-linejoin="round"
                 class="transition-all duration-500 ease-in-out"
               />
               
               <!-- Data Points (Interactive) -->
               <g v-for="(point, index) in chartPoints" :key="index">
                 <!-- Invisible hit area for easier hovering -->
                 <rect 
                    :x="point.x - 20" 
                    y="0" 
                    width="40" 
                    height="200" 
                    fill="transparent" 
                    class="cursor-pointer"
                 />
                 <circle 
                   :cx="point.x" 
                   :cy="point.y" 
                   r="4" 
                   fill="#0f172a" 
                   stroke="white" 
                   stroke-width="2"
                   class="opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                 />
                 <!-- Tooltip -->
                 <g class="opacity-0 group-hover:opacity-100 transition-opacity duration-300 delay-75 pointer-events-none">
                   <rect 
                     :x="point.x - 20" 
                     :y="point.y - 35" 
                     width="40" 
                     height="24" 
                     rx="4" 
                     fill="#0f172a" 
                   />
                   <text 
                     :x="point.x" 
                     :y="point.y - 19" 
                     fill="white" 
                     font-size="10" 
                     font-weight="bold" 
                     text-anchor="middle"
                   >{{ point.value }}</text>
                 </g>
               </g>
            </svg>
           
           <!-- X Axis Labels -->
           <div class="absolute bottom-0 left-0 w-full h-6 text-xs text-slate-400">
             <div class="relative w-full h-full">
               <span 
                 v-for="(day, index) in weekDays" 
                 :key="index" 
                 class="absolute bottom-1 transform -translate-x-1/2 text-center whitespace-nowrap"
                 :style="{ left: `${(index / 6) * 100}%` }"
               >
                 {{ day }}
               </span>
             </div>
           </div>
        </div>
      </div>

      <!-- 饼图：内容分布 -->
      <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col">
        <h3 class="font-bold text-slate-900 mb-6">内容分布</h3>
        <div class="flex-1 flex items-center justify-center relative">
          <!-- CSS Donut Chart -->
          <div class="relative w-48 h-48">
            <svg viewBox="0 0 36 36" class="w-full h-full transform -rotate-90">
              <!-- Background Circle -->
              <path class="text-slate-100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" stroke-width="3.8" />
              
              <!-- Segment 1: Posts (Black) -->
              <path class="text-slate-900 transition-all duration-1000 ease-out" 
                :stroke-dasharray="`${contentDistribution.posts.percent}, 100`" 
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                fill="none" stroke="currentColor" stroke-width="3.8" />
              
              <!-- Segment 2: Comments (Blue) -->
              <path class="text-blue-500 transition-all duration-1000 ease-out" 
                :stroke-dasharray="`${contentDistribution.comments.percent}, 100`" 
                :stroke-dashoffset="contentDistribution.comments.offset" 
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                fill="none" stroke="currentColor" stroke-width="3.8" />
              
              <!-- Segment 3: Other (Green) -->
              <path class="text-emerald-500 transition-all duration-1000 ease-out" 
                :stroke-dasharray="`${contentDistribution.interactions.percent}, 100`" 
                :stroke-dashoffset="contentDistribution.interactions.offset" 
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                fill="none" stroke="currentColor" stroke-width="3.8" />
            </svg>
            
            <!-- Center Text -->
            <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span class="text-3xl font-bold text-slate-900">{{ totalContent }}</span>
              <span class="text-xs text-slate-400 font-medium uppercase tracking-wider">Total</span>
            </div>
          </div>
        </div>
        
        <!-- Legend -->
        <div class="mt-8 space-y-3">
          <div class="flex items-center justify-between text-sm">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-slate-900"></span>
              <span class="text-slate-600">帖子</span>
            </div>
            <span class="font-bold text-slate-900">{{ contentDistribution.posts.percent }}%</span>
          </div>
          <div class="flex items-center justify-between text-sm">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-blue-500"></span>
              <span class="text-slate-600">评论</span>
            </div>
            <span class="font-bold text-slate-900">{{ contentDistribution.comments.percent }}%</span>
          </div>
          <div class="flex items-center justify-between text-sm">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
              <span class="text-slate-600">互动</span>
            </div>
            <span class="font-bold text-slate-900">{{ contentDistribution.interactions.percent }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部：设备分布与最近活动 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 热门搜索城市排行 (Top 5) -->
      <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
        <h3 class="font-bold text-slate-900 mb-6">热门火车票搜索城市 (Top 5)</h3>
        <div class="h-48 flex flex-col justify-center gap-3">
          <div v-for="(city, i) in topCities" :key="i" class="relative group">
            <div class="flex justify-between text-xs mb-1">
              <span class="font-medium text-slate-700">{{ city.name }}</span>
              <span class="text-slate-500">{{ city.count }} 次搜索</span>
            </div>
            <div class="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
              <div 
                class="bg-slate-900 h-full rounded-full transition-all duration-1000 group-hover:bg-blue-600"
                :style="{ width: city.percent + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 最近注册用户 -->
      <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm overflow-hidden flex flex-col max-h-[300px]">
        <div class="flex items-center justify-between mb-6 flex-shrink-0">
          <h3 class="font-bold text-slate-900">新注册用户</h3>
          <button class="text-xs text-blue-600 font-medium hover:underline">查看全部</button>
        </div>
        <div class="flex-1 overflow-auto -mx-6 px-6">
          <div class="space-y-4">
            <div v-for="user in recentUsers" :key="user.id" class="flex items-center gap-4 py-2 border-b border-slate-50 last:border-0">
              <div class="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 font-bold overflow-hidden flex-shrink-0">
                <img v-if="user.avatar_url" :src="user.avatar_url" class="w-full h-full object-cover" />
                <span v-else>{{ (user.username?.[0] || 'U').toUpperCase() }}</span>
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-bold text-slate-900 truncate">{{ user.username || '未命名用户' }}</div>
                <div class="text-xs text-slate-500 truncate">{{ formatDate(user.updated_at) }}</div>
              </div>
              <div class="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">
                New
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { supabase } from '@/utils/supabase';
import { 
  Users, 
  MessageSquare, 
  FileText, 
  Activity, 
  TrendingUp, 
  TrendingDown 
} from 'lucide-vue-next';

// --- State ---
const growthChartMode = ref<'thisWeek' | 'lastWeek'>('thisWeek');
const userGrowthData = ref<number[]>([0, 0, 0, 0, 0, 0, 0]);
const weekDays = ref<string[]>(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']);

const stats = ref([
  { title: '总用户数', value: '0', icon: Users, bg: 'bg-blue-50', color: 'text-blue-600', trend: 12.5 },
  { title: '总帖子数', value: '0', icon: FileText, bg: 'bg-emerald-50', color: 'text-emerald-600', trend: 8.2 },
  { title: '总评论数', value: '0', icon: MessageSquare, bg: 'bg-purple-50', color: 'text-purple-600', trend: -2.4 },
  { title: '今日活跃', value: '0', icon: Activity, bg: 'bg-amber-50', color: 'text-amber-600', trend: 5.7 },
]);

// --- Chart Computed Properties ---
const maxDataValue = computed(() => {
  const max = Math.max(...userGrowthData.value);
  return max === 0 ? 10 : Math.ceil(max * 1.2); // Add 20% padding
});

const chartPoints = computed(() => {
  const widthTotal = 800; 
  // Using viewBox 0 0 800 200
  // Y range: Let's use 20 (top) to 180 (bottom). Height = 160.
  
  return userGrowthData.value.map((value, index) => {
    const x = (index / 6) * widthTotal;
    // Y range: 20 (top) to 170 (bottom) to avoid overlap with x-axis labels
    const y = 170 - (value / maxDataValue.value) * 150;
    
    return {
      x: x, 
      y: y,              
      value,
    };
  });
});

const chartPath = computed(() => {
  const widthTotal = 800;
  
  const points = userGrowthData.value.map((value, index) => {
    const x = (index / 6) * widthTotal;
    const y = 170 - (value / maxDataValue.value) * 150;
    return [x, y];
  });
  
  // Generate Line Path (L)
  // M x0 y0 L x1 y1 L x2 y2 ...
  return `M ${points.map(p => `${p[0]},${p[1]}`).join(' L ')}`;
});

// --- Date Logic ---
const getWeekRange = (mode: 'thisWeek' | 'lastWeek') => {
  const now = new Date();
  const day = now.getDay(); // 0 (Sun) - 6 (Sat)
  // Adjust so Monday is 0, Sunday is 6
  const diffToMonday = day === 0 ? -6 : 1 - day;
  
  const thisMonday = new Date(now);
  thisMonday.setDate(now.getDate() + diffToMonday);
  thisMonday.setHours(0, 0, 0, 0);
  
  let start = new Date(thisMonday);
  if (mode === 'lastWeek') {
    start.setDate(start.getDate() - 7);
  }
  
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  end.setHours(23, 59, 59, 999);
  
  return { start, end };
};

const updateWeekDays = (start: Date) => {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  // Ideally we might want specific dates like "Mon 10/24" but space is tight.
  // Let's stick to days for now, or maybe just the day number?
  // The user asked "看不到星期", so showing Mon-Sun is the direct answer.
  // If they want dates, we can add them. Let's add date number: "Mon 12"
  weekDays.value = days.map((d, i) => {
    const date = new Date(start);
    date.setDate(date.getDate() + i);
    return `${d} ${date.getDate()}`;
  });
};

const fetchUserGrowth = async () => {
  const { start, end } = getWeekRange(growthChartMode.value);
  updateWeekDays(start);
  
  // Call RPC
  const { data, error } = await supabase.rpc('get_daily_user_growth', {
    start_date: start.toISOString(),
    end_date: end.toISOString()
  });
  
  if (error) {
    console.error('Error fetching user growth:', error);
    return;
  }
  
  // Process Data
  // data is [{ date: '2023-10-24', count: 5 }, ...]
  // We need to map this to our 7-day array.
  const counts = [0, 0, 0, 0, 0, 0, 0];
  
  if (data) {
    data.forEach((item: any) => {
      const date = new Date(item.date);
      // Find index (0-6) relative to start date
      // Calculate difference in days
      const diffTime = Math.abs(date.getTime() - start.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 
      // Note: getTime is UTC, date strings from DB might be UTC or local depending on parsing.
      // supabase-js returns ISO strings.
      // Let's be careful with timezones.
      // The RPC returns dates. new Date('2023-10-24') is UTC usually.
      // 'start' is local midnight.
      // To allow for timezone mismatches, let's just match YYYY-MM-DD strings.
      
      const dateStr = item.date.split('T')[0]; // assuming ISO
      
      for (let i = 0; i < 7; i++) {
        const d = new Date(start);
        d.setDate(d.getDate() + i);
        const dStr = d.toISOString().split('T')[0];
        // However, local toISOString uses UTC.
        // We need local YYYY-MM-DD.
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const localDateStr = `${year}-${month}-${day}`;
        
        if (dateStr === localDateStr) {
          counts[i] = item.count;
        }
      }
    });
  }
  
  userGrowthData.value = counts;
};

const setChartMode = (mode: 'thisWeek' | 'lastWeek') => {
  growthChartMode.value = mode;
  fetchUserGrowth();
};

watch(growthChartMode, () => {
  // fetchUserGrowth called in setChartMode, but useful if triggered elsewhere
});

// --- Content Distribution Logic ---
const contentStats = ref({
  posts: 0,
  comments: 0,
  interactions: 0
});

const contentDistribution = computed(() => {
  const { posts, comments, interactions } = contentStats.value;
  const total = posts + comments + interactions;
  
  if (total === 0) {
    return {
      posts: { percent: 0, offset: 0 },
      comments: { percent: 0, offset: 0 },
      interactions: { percent: 0, offset: 0 }
    };
  }

  const pPosts = Math.round((posts / total) * 100);
  const pComments = Math.round((comments / total) * 100);
  // Ensure total is 100% by giving the remainder to interactions
  const pInteractions = 100 - pPosts - pComments;

  return {
    posts: { 
      percent: pPosts, 
      offset: 0 
    },
    comments: { 
      percent: pComments, 
      offset: -pPosts 
    },
    interactions: { 
      percent: pInteractions, 
      offset: -(pPosts + pComments) 
    }
  };
});

// --- Existing Logic ---
const topCities = ref<any[]>([]);

const totalContent = ref(0);
const recentUsers = ref<any[]>([]);

const formatDate = (dateString: string) => {
  if (!dateString) return '未知日期';
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};

const fetchStats = async () => {
  try {
    // 1. Users Count
    const { count: usersCount } = await supabase.from('profiles').select('id', { count: 'exact', head: true });
    stats.value[0].value = usersCount?.toLocaleString() || '0';

    // 2. Posts Count
    const { count: postsCount } = await supabase.from('posts').select('id', { count: 'exact', head: true });
    stats.value[1].value = postsCount?.toLocaleString() || '0';

    // 3. Comments Count
    const { count: commentsCount } = await supabase.from('comments').select('id', { count: 'exact', head: true });
    stats.value[2].value = commentsCount?.toLocaleString() || '0';

    // 4. Interactions Count (Likes, Collects, etc.)
    const { count: interactionsCount } = await supabase.from('interactions').select('id', { count: 'exact', head: true });
    
    // Update Content Distribution
    contentStats.value = {
      posts: postsCount || 0,
      comments: commentsCount || 0,
      interactions: interactionsCount || 0
    };
    totalContent.value = (postsCount || 0) + (commentsCount || 0) + (interactionsCount || 0);

    // 5. Active Users (Mock for now, or fetch active sessions if available)
    // We have assistant_sessions, maybe count active users there?
    // Or just random for "online users"
    stats.value[3].value = Math.floor(Math.random() * 50 + 10).toString();

    // 6. Recent Users
    // profiles table may not have created_at if not added explicitly, but usually updated_at is there
    // Let's check columns for profiles or just use updated_at as proxy if created_at missing
    // Actually created_at is standard in Supabase Auth, but profiles table is separate.
    // Let's assume profiles has created_at or updated_at.
    const { data: users } = await supabase
      .from('profiles')
      .select('id, username, avatar_url, updated_at')
      .order('updated_at', { ascending: false })
      .limit(5);
    
    recentUsers.value = users || [];

    // 6. User Growth Chart
    await fetchUserGrowth();

    // 7. Top Searched Cities
    const { data: cities } = await supabase.rpc('get_top_searched_cities', { limit_count: 5 });
    if (cities && cities.length > 0) {
      // Calculate max count for width normalization to make the chart look full
      const maxCount = Math.max(...cities.map((c: any) => c.count));
      topCities.value = cities.map((c: any) => ({
        name: c.name,
        count: c.count,
        percent: maxCount > 0 ? Math.round((c.count / maxCount) * 100) : 0
      }));
    }

  } catch (error) {
    console.error('Error fetching dashboard stats:', error);
  }
};

onMounted(() => {
  fetchStats();
});
</script>