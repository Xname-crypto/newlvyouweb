<script setup lang="ts">
import { ref, watch } from 'vue';
import { 
  Home, FileText, BarChart2, Activity, MessageSquare, 
  BookOpen, HelpCircle, PenTool
} from 'lucide-vue-next';
import { supabase } from '@/utils/supabase';
import { useRouter, useRoute } from 'vue-router';
import { useToast } from '@/composables/useToast';

const activeItem = ref('publish');
const router = useRouter();
const route = useRoute();
const { showToast } = useToast();

const menuItems = [
  { id: 'home', label: '首页', icon: Home, route: '/creator' },
  { id: 'publish', label: '发布笔记', icon: PenTool, route: '/publish' },
  { id: 'manage', label: '笔记管理', icon: FileText, route: '/publish/notes' },
];

watch(() => route.path, (path) => {
  if (path === '/creator') {
    activeItem.value = 'home';
  } else if (path === '/publish') {
    activeItem.value = 'publish';
  } else if (path === '/publish/notes') {
    activeItem.value = 'manage';
  }
}, { immediate: true });

const handleItemClick = (item: any) => {
  activeItem.value = item.id;
  if (item.route) {
    router.push(item.route);
  }
};


const handlePublishClick = async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    showToast('请先登录后再发布内容', 'warning');
    return;
  }
  // Logic to focus publish area or just stay here since we are already on /publish
};
</script>

<template>
  <aside class="w-[240px] h-[calc(100vh-64px)] bg-white border-r border-gray-100 flex flex-col py-6">
    <!-- Publish Button -->
    <div class="px-4 mb-6">
      <button 
        @click="handlePublishClick"
        class="w-full bg-red-500 hover:bg-red-600 text-white font-bold py-3 rounded-lg flex items-center justify-center space-x-2 transition-colors shadow-sm"
      >
        <PenTool class="w-5 h-5" />
        <span>发布笔记</span>
      </button>
    </div>

    <!-- Menu Items -->
    <nav class="flex-1 overflow-y-auto px-2 space-y-1">
      <button
        v-for="item in menuItems"
        :key="item.id"
        @click="handleItemClick(item)"
        class="w-full flex items-center px-4 py-3 rounded-lg text-sm font-medium transition-colors group"
        :class="activeItem === item.id ? 'text-red-500 bg-red-50' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'"
      >
        <component 
            :is="item.icon" 
            class="w-5 h-5 mr-3"
            :class="activeItem === item.id ? 'text-red-500' : 'text-gray-400 group-hover:text-gray-600'"
        />
        <span class="flex-1 text-left">{{ item.label }}</span>
      </button>
    </nav>
  </aside>
</template>
