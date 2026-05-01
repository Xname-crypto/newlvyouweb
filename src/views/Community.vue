<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue';
import Sidebar from '@/components/community/Sidebar.vue';
import CommunityMasonry from '@/components/community/CommunityMasonry.vue';
import PostModal from '@/components/community/PostModal.vue';
import Navigation from '@/components/Navigation.vue';
import { Search } from 'lucide-vue-next';
import { publishService } from '@/services/publishService';
import { profileService } from '@/services/profileService';
import { supabase } from '@/utils/supabase';
import { DEFAULT_AVATAR } from '@/utils/avatar';

// Categories
const categories = ['推荐', '酒店', '线路', '美食', '景点', '穿搭', '攻略', '火车', '帖子'];
const activeCategory = ref('推荐');

const posts = ref<any[]>([]);
const userInterests = ref<string[]>([]);
const isLoggedIn = ref(false);
const searchQuery = ref('');

const categoryKeywords: Record<string, string[]> = {
  酒店: ['酒店', '民宿', '旅馆', '住宿', '入住', '房间', '客栈', '青旅', '前台', '退房', '早餐', '床品'],
  线路: ['线路', '路线', '行程', '打卡', '一日游', '路书', '路线图', '徒步', '自驾'],
  美食: ['美食', '餐厅', '吃', '菜', '小吃', '饮品', '咖啡', '咖啡馆', '酒吧', '餐馆', '早茶', '晚餐', '宵夜', '小馆'],
  景点: ['景点', '景区', '名胜', '地标', '公园', '博物馆', '古镇', '古城', '遗址', '寺', '庙', '山', '湖', '海', '沙滩', '瀑布', '森林', '国家公园', '风景', '景色', '观景台'],
  穿搭: ['穿搭', '服装', '穿衣', '搭配', 'OOTD', '鞋子', '背包', '外套', '配色'],
  攻略: ['攻略', '避坑', '建议', '必去', '注意', '经验', '干货', '指南', 'TIPS'],
  火车: ['火车', '高铁', '12306', '动车', '车次', '站点', '余票', '候车', '换乘'],
};

const categoryPriority = ['景点', '线路', '攻略', '美食', '酒店', '穿搭', '火车', '帖子'];

const vibesToTags: Record<string, string[]> = {
  探险: ['线路', '景点', '攻略'],
  摄影: ['景点', '攻略'],
  美食: ['美食'],
  自然: ['景点', '线路', '攻略'],
  城市: ['景点', '美食', '攻略'],
  音乐: ['攻略', '城市']
};

const getOccurrences = (text: string, kw: string) => {
  let i = -1, c = 0;
  while ((i = text.indexOf(kw, i + 1)) !== -1) c++;
  return c;
};

const classifyPost = (post: any) => {
  const title = post.title || '';
  const body = post.content || '';
  const scores: Record<string, number> = {};
  for (const [cat, kws] of Object.entries(categoryKeywords)) {
    let s = 0;
    for (const k of kws) {
      s += getOccurrences(title, k) * 2;
      s += getOccurrences(body, k);
    }
    scores[cat] = s;
  }
  let best = '帖子';
  let bestScore = 0;
  for (const cat of Object.keys(scores)) {
    if (scores[cat] > bestScore) {
      best = cat;
      bestScore = scores[cat];
    } else if (scores[cat] === bestScore && bestScore > 0) {
      if (categoryPriority.indexOf(cat) < categoryPriority.indexOf(best)) best = cat;
    }
  }
  if (bestScore === 0) {
    if (post.type === 'article') return '攻略';
    return '帖子';
  }
  return best;
};

const loadPosts = async () => {
  const data = await publishService.fetchPosts();
  if (data) {
    posts.value = data.map((post: any) => {
      const category = classifyPost(post);
      return {
        id: post.id,
        title: post.title,
        image: post.media_urls?.[0] || 'https://picsum.photos/seed/default/600/800',
        images: Array.isArray(post.media_urls) ? post.media_urls : (post.media_urls ? [post.media_urls] : []),
        content: post.content,
        type: post.type,
        category,
        created_at: post.created_at,
        tags: [category],
        location: post.location || '未知地点',
        user: {
          name: post.profiles?.username || '未知用户',
          avatar: post.profiles?.avatar_url || DEFAULT_AVATAR,
          isFollowing: false
        },
        likes: post.likes || 0,
        stars: 0,
        comments: 0,
      };
    });
  }
};

const loadInterests = async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return;
  const profile = await profileService.fetchProfile(session.user.id);
  if (!profile?.bio) return;
  const match = String(profile.bio).match(/兴趣[:：]\s*(.*)$/m);
  if (match && match[1]) {
    const list = match[1].split(/[、,，]/).map(s => s.trim()).filter(Boolean);
    userInterests.value = list;
  }
};

let authSubscription: any = null;

onMounted(async () => {
  // Check initial auth state
  const { data: { session } } = await supabase.auth.getSession();
  isLoggedIn.value = !!session;
  if (session) {
    loadInterests();
  }

  loadPosts();

  // Listen for auth changes
  const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
    isLoggedIn.value = !!session;
    if (session) {
      loadInterests();
    } else {
      userInterests.value = [];
      searchQuery.value = '';
    }
  });
  authSubscription = subscription;
});

onUnmounted(() => {
  if (authSubscription) authSubscription.unsubscribe();
});

const selectedPost = ref<any>(null);
const isModalOpen = ref(false);

const openPost = (post: any) => {
  selectedPost.value = post;
  isModalOpen.value = true;
  // Prevent body scroll
  document.body.style.overflow = 'hidden';
};

const closePost = () => {
  isModalOpen.value = false;
  // Restore body scroll
  document.body.style.overflow = '';
};

// Posts to display: filter by category or recommend by interests
const displayPosts = computed(() => {
  let filtered = posts.value;

  // Search filter
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase();
    filtered = filtered.filter(p => 
      (p.title && p.title.toLowerCase().includes(q)) || 
      (p.content && p.content.toLowerCase().includes(q))
    );
  }

  if (activeCategory.value !== '推荐') {
    return filtered.filter(p => p.category === activeCategory.value);
  }
  // 推荐：根据兴趣打分排序
  if (userInterests.value.length === 0) {
    return filtered;
  }
  const interestSet = new Set(userInterests.value);
  const inferredPreferredCats = new Set<string>();
  userInterests.value.forEach(v => {
    Object.entries(vibesToTags).forEach(([k, cats]) => {
      if (v.includes(k)) cats.forEach(c => inferredPreferredCats.add(c));
    });
  });

  return [...filtered]
    .map(p => {
      let score = 0;
      const text = `${p.title || ''} ${p.content || ''}`;
      interestSet.forEach(i => { if (text.includes(i)) score += 2; });
      if (inferredPreferredCats.has(p.category)) score += 3;
      if (p.type === 'article' && (inferredPreferredCats.has('攻略') || text.includes('攻略'))) score += 1;
      return { p, score };
    })
    .sort((a, b) => b.score - a.score)
    .map(x => x.p);
});
</script>

<template>
  <div class="min-h-screen bg-white flex flex-col pt-24">
    <!-- Top Navigation -->
    <Navigation class="!bg-white/95 !backdrop-blur-sm shadow-sm text-black">
      <template #logo>
        <router-link to="/" class="text-4xl font-black text-red-500 tracking-tighter flex items-center" style="font-family: 'PangMenZhengDao', serif;">椿天社</router-link>
      </template>
    </Navigation>

    <div class="flex flex-1">
      <!-- Sidebar (Left) -->
      <div class="hidden lg:block w-[240px] flex-shrink-0 h-[calc(100vh-96px)] sticky top-24">
          <Sidebar />
      </div>

    <!-- Main Content (Right) -->
    <main class="flex-1 min-w-0">
      <div class="mx-auto max-w-[1320px] px-4 pt-8 pb-12 sm:px-6 lg:px-8">
        <!-- Search & Categories Header -->
      <div class="flex flex-col items-start mb-8 space-y-6 sticky top-0 bg-white/95 backdrop-blur-sm z-30 py-4">
        <!-- Search Bar (Centered) -->
        <div class="w-full flex justify-center">
            <div class="relative w-full max-w-lg">
                <input 
                    type="text" 
                    v-model="searchQuery"
                    :placeholder="isLoggedIn ? '搜索你感兴趣的内容' : '登录探索更多内容'" 
                    class="w-full pl-10 pr-4 py-3 bg-gray-100/80 hover:bg-gray-100 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-gray-200 transition-all placeholder-gray-400 text-center"
                >
                <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            </div>
        </div>

        <!-- Categories (Left Aligned) -->
        <div class="flex flex-wrap justify-start gap-x-8 gap-y-2 text-[15px] text-gray-500 font-medium">
                <button 
                    v-for="cat in categories" 
                    :key="cat"
                    @click="activeCategory = cat"
                    class="hover:text-gray-900 transition-colors relative py-1"
                    :class="{ 'text-gray-900 font-bold': activeCategory === cat }"
                >
                    {{ cat }}
                    <span v-if="activeCategory === cat" class="absolute bottom-0 left-1/2 -translate-x-1/2 w-full h-0.5 bg-red-500 rounded-full"></span>
                </button>
            </div>
        </div>

        <CommunityMasonry
          :posts="displayPosts"
          animate-from="bottom"
          :duration="0.78"
          :stagger="0.05"
          :blur-to-focus="true"
          @select="openPost"
        />
      </div>
    </main>

    <!-- Post Detail Modal -->
    <PostModal 
      v-if="selectedPost"
      :post="selectedPost"
      :is-open="isModalOpen"
      @close="closePost"
    />
    </div>
  </div>
</template>

<style scoped>
/* No overrides needed */
</style>
