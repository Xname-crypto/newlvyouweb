<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import CreatorHeader from '@/components/CreatorHeader.vue';
import PublishSidebar from '@/components/publish/PublishSidebar.vue';
import { publishService } from '@/services/publishService';
import { Edit, Trash2, FileText, Video, Image as ImageIcon, Eye, EyeOff } from 'lucide-vue-next';

const router = useRouter();
const loading = ref(true);
const posts = ref<any[]>([]);
const activeTab = ref('all');

const tabs = [
  { id: 'all', label: '全部笔记' },
  { id: 'published', label: '已发布' },
  { id: 'draft', label: '草稿箱' },
];

const fetchPosts = async () => {
  loading.value = true;
  try {
    const data = await publishService.fetchUserPosts();
    posts.value = data || [];
  } catch (error) {
    console.error('Error fetching posts:', error);
  } finally {
    loading.value = false;
  }
};

const filteredPosts = computed(() => {
  if (activeTab.value === 'all') return posts.value;
  return posts.value.filter(post => post.status === activeTab.value);
});

const handleEdit = (post: any) => {
  router.push({
    path: '/publish',
    query: { id: post.id }
  });
};

const handleDelete = async (post: any) => {
  if (!confirm('确定要删除这条笔记吗？此操作不可恢复。')) return;
  
  try {
    const success = await publishService.deletePost(post.id);
    if (success) {
      posts.value = posts.value.filter(p => p.id !== post.id);
    } else {
      alert('删除失败，请重试');
    }
  } catch (error) {
    console.error('Error deleting post:', error);
    alert('删除出错');
  }
};

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getStatusLabel = (status: string) => {
  return status === 'published' ? '已发布' : '草稿';
};

const getStatusClass = (status: string) => {
  return status === 'published' 
    ? 'bg-green-100 text-green-700' 
    : 'bg-gray-100 text-gray-700';
};

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'video': return Video;
    case 'image': return ImageIcon;
    case 'article': return FileText;
    default: return FileText;
  }
};

onMounted(() => {
  fetchPosts();
});
</script>

<template>
  <div class="min-h-screen bg-[#f9f9f9] flex flex-col">
    <!-- Header -->
    <CreatorHeader />

    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar -->
      <PublishSidebar />

      <!-- Main Content -->
      <main class="flex-1 overflow-y-auto p-6">
        <div class="bg-white rounded-xl shadow-sm min-h-[600px] p-8">
          <h1 class="text-2xl font-bold text-gray-900 mb-6">笔记管理</h1>
          
          <!-- Tabs -->
          <div class="flex space-x-1 mb-6 border-b border-gray-100">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              class="px-4 py-2 text-sm font-medium transition-colors relative"
              :class="activeTab === tab.id ? 'text-red-500' : 'text-gray-500 hover:text-gray-900'"
            >
              {{ tab.label }}
              <span v-if="activeTab === tab.id" class="absolute bottom-0 left-0 w-full h-0.5 bg-red-500 rounded-full"></span>
            </button>
          </div>

          <!-- List -->
          <div v-if="loading" class="flex justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-red-500"></div>
          </div>

          <div v-else-if="filteredPosts.length === 0" class="flex flex-col items-center justify-center py-20 text-gray-400">
            <FileText class="w-16 h-16 mb-4 text-gray-200" />
            <p>暂无相关笔记</p>
            <button @click="router.push('/publish')" class="mt-4 px-6 py-2 bg-red-500 text-white rounded-full text-sm hover:bg-red-600 transition-colors">
              去发布
            </button>
          </div>

          <div v-else class="space-y-4">
            <div 
              v-for="post in filteredPosts" 
              :key="post.id"
              class="flex items-center p-4 border border-gray-100 rounded-lg hover:border-gray-200 hover:shadow-sm transition-all group"
            >
              <!-- Cover/Icon -->
              <div class="w-16 h-16 bg-gray-100 rounded-lg flex-shrink-0 overflow-hidden flex items-center justify-center mr-4 relative">
                <img 
                  v-if="post.media_urls && post.media_urls.length > 0 && post.type !== 'video'" 
                  :src="post.media_urls[0]" 
                  class="w-full h-full object-cover"
                />
                <video 
                  v-else-if="post.media_urls && post.media_urls.length > 0 && post.type === 'video'" 
                  :src="post.media_urls[0]" 
                  class="w-full h-full object-cover"
                ></video>
                <component :is="getTypeIcon(post.type)" v-else class="w-6 h-6 text-gray-400" />
                
                <!-- Type Badge -->
                <div class="absolute top-1 right-1 bg-black/50 p-0.5 rounded text-white">
                    <component :is="getTypeIcon(post.type)" class="w-3 h-3" />
                </div>
              </div>

              <!-- Content -->
              <div class="flex-1 min-w-0 mr-4">
                <div class="flex items-center mb-1">
                  <h3 class="text-base font-medium text-gray-900 truncate pr-2">{{ post.title || '无标题' }}</h3>
                  <span 
                    class="px-2 py-0.5 rounded text-xs font-medium flex-shrink-0"
                    :class="getStatusClass(post.status)"
                  >
                    {{ getStatusLabel(post.status) }}
                  </span>
                </div>
                <p class="text-sm text-gray-500 truncate mb-1">{{ post.content || '无内容' }}</p>
                <div class="text-xs text-gray-400 flex items-center">
                  <span>{{ formatDate(post.created_at) }}</span>
                </div>
              </div>

              <!-- Actions -->
              <div class="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button 
                  @click="handleEdit(post)"
                  class="p-2 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded-full transition-colors"
                  title="编辑"
                >
                  <Edit class="w-4 h-4" />
                </button>
                <button 
                  @click="handleDelete(post)"
                  class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
                  title="删除"
                >
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  </div>
</template>
