<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { Compass, PlusSquare, Bell, User, Headset } from 'lucide-vue-next';
import { supabase } from '@/utils/supabase';
import { useRouter, useRoute } from 'vue-router';
import { useToast } from '@/composables/useToast';
import { notificationService } from '@/services/notificationService';

const activeItem = ref('discover');
const router = useRouter();
const route = useRoute();
const { showToast } = useToast();
const unreadCount = ref(0);
let countInterval: any = null;

const fetchUnread = async () => {
  const counts = await notificationService.fetchUnreadCounts();
  unreadCount.value = counts.total;
};

onMounted(() => {
  fetchUnread();
  // Poll for unread counts every 30 seconds
  countInterval = setInterval(fetchUnread, 30000);
  
  // Also listen for realtime notifications if needed, but polling is simpler for global badge
});

onUnmounted(() => {
  if (countInterval) clearInterval(countInterval);
});

const menuItems = [
  { id: 'discover', label: '发现', icon: Compass, route: '/community' },
  { id: 'notification', label: '通知', icon: Bell, route: '/notifications' },
];

// Watch route changes to update activeItem
watch(() => route.path, (path) => {
  if (path.startsWith('/community')) {
    activeItem.value = 'discover';
  } else if (path.startsWith('/notifications')) {
    activeItem.value = 'notification';
  } else if (path.startsWith('/assistant')) {
    activeItem.value = 'assistant';
  } else if (path.startsWith('/publish')) {
    activeItem.value = 'publish';
  } else if (path.startsWith('/profile')) {
    activeItem.value = 'me';
  } else {
    activeItem.value = '';
  }
}, { immediate: true });


const handleItemClick = async (item: any) => {
  if (item.id === 'notification') {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      showToast('请先登录后再查看通知', 'warning');
      return;
    }
  }
  
  activeItem.value = item.id;
  if (item.route) {
    router.push(item.route);
  }
};


const handlePublishClick = async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    showToast('请先登录后再发布内容', 'warning');
  } else {
    router.push('/publish');
  }
};

const handleAssistantClick = () => {
  activeItem.value = 'assistant';
  router.push('/assistant');
};

const handleMeClick = async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session) {
    router.push('/profile');
  } else {
    router.push('/login');
  }
};
</script>

<template>
  <aside class="w-[240px] h-screen sticky top-0 flex flex-col pt-8 pb-4 pl-4 lg:pl-8">
    <!-- Logo -->
    <div class="mb-10 pl-4">
      <div aria-hidden="true" class="text-4xl font-black text-red-500 tracking-tighter flex items-center invisible select-none" style="font-family: 'PangMenZhengDao', serif;">
         椿天社
      </div>
    </div>

    <!-- Menu Items -->
    <nav class="flex-1 space-y-2">
      <button
        v-for="item in menuItems"
        :key="item.id"
        @click="handleItemClick(item)"
        class="w-full flex items-center space-x-4 px-4 py-3.5 rounded-full text-lg font-medium transition-all duration-200 group relative"
        :class="activeItem === item.id ? 'bg-gray-100 font-bold text-gray-900' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'"
      >
        <div class="relative">
            <component 
                :is="item.icon" 
                class="w-7 h-7"
                :class="activeItem === item.id ? 'stroke-[2.5px]' : 'stroke-2'"
            />
            <span v-if="item.id === 'notification' && unreadCount > 0" class="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] text-white">
                {{ unreadCount > 99 ? '99+' : unreadCount }}
            </span>
        </div>
        <span>{{ item.label }}</span>
      </button>

      <!-- Separate "Publish" button as link with auth check -->
      <button
        @click="handlePublishClick"
        class="w-full flex items-center space-x-4 px-4 py-3.5 rounded-full text-lg font-medium transition-all duration-200 group"
        :class="activeItem === 'publish' ? 'bg-gray-100 font-bold text-gray-900' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'"
      >
        <PlusSquare class="w-7 h-7" :class="activeItem === 'publish' ? 'stroke-[2.5px]' : 'stroke-2'" />
        <span>发布</span>
      </button>

      <!-- Assistant button placed above "Me" -->
      <button
        @click="handleAssistantClick"
        class="w-full flex items-center space-x-4 px-4 py-3.5 rounded-full text-lg font-medium transition-all duration-200 group"
        :class="activeItem === 'assistant' ? 'bg-gray-100 font-bold text-gray-900' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'"
      >
        <Headset class="w-7 h-7" :class="activeItem === 'assistant' ? 'stroke-[2.5px]' : 'stroke-2'" />
        <span>客服</span>
      </button>

      <!-- Separate "Me" button as it might be a link -->
      <button
        @click="handleMeClick"
        class="w-full flex items-center space-x-4 px-4 py-3.5 rounded-full text-lg font-medium transition-all duration-200 group"
        :class="activeItem === 'me' ? 'bg-gray-100 font-bold text-gray-900' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'"
      >
        <User class="w-7 h-7" :class="activeItem === 'me' ? 'stroke-[2.5px]' : 'stroke-2'" />
        <span>我</span>
      </button>

    </nav>
    
    <!-- Bottom Menu (More) -->
    <div class="mt-auto px-4">
        <button class="flex items-center space-x-4 text-gray-500 hover:text-gray-900 font-medium text-base p-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-menu"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>
            <span>更多</span>
        </button>
    </div>
  </aside>
</template>
