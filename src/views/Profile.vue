<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import Sidebar from '@/components/community/Sidebar.vue';
import PostCard from '@/components/community/PostCard.vue';
import { Search, MoreHorizontal, Edit2, Loader2, Camera, LogOut } from 'lucide-vue-next';
import { supabase } from '@/utils/supabase';
import { useRouter } from 'vue-router';
import { profileService } from '@/services/profileService';
import { useToast } from '@/composables/useToast';
import { DEFAULT_AVATAR } from '@/utils/avatar';

const router = useRouter();
const { showToast } = useToast();
const user = ref<any>(null);
const profile = ref<any>(null);
const activeTab = ref('notes');
const isEditModalOpen = ref(false);
const isSaving = ref(false);
const userPosts = ref<any[]>([]);

// Edit Form State
const editForm = ref({
  username: '',
  bio: '',
  avatar_url: ''
});
const avatarFile = ref<File | null>(null);
const avatarPreview = ref<string | null>(null);

const tabs = [
  { id: 'notes', label: '笔记' },
  { id: 'collect', label: '收藏' },
  { id: 'like', label: '点赞' },
];

const fetchProfile = async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    router.push('/login');
    return;
  }
  user.value = session.user;
  
  profile.value = await profileService.fetchProfile(session.user.id);
    
  if (!profile.value) profile.value = {};
  
  // Initialize form
  editForm.value = {
    username: profile.value.username || '',
    bio: profile.value.bio || '',
    avatar_url: profile.value.avatar_url || ''
  };

  // Fetch user's posts
  await fetchContent();
};

const fetchContent = async () => {
  if (!user.value) return;

  let posts = [];
  if (activeTab.value === 'notes') {
    posts = await profileService.fetchUserPosts(user.value.id);
  } else if (activeTab.value === 'collect') {
    posts = await profileService.fetchCollectedPosts(user.value.id);
  } else if (activeTab.value === 'like') {
    posts = await profileService.fetchLikedPosts(user.value.id);
  } else {
    posts = [];
  }

  if (posts) {
    userPosts.value = posts.map((post: any) => ({
      id: post.id,
      title: post.title,
      image: post.media_urls?.[0] || 'https://picsum.photos/seed/default/600/800',
      content: post.content,
      type: post.type, // Pass type (video/image)
      tags: ['旅行'],
      location: '未知地点',
      user: {
        name: profile.value.username || '我',
        avatar: profile.value.avatar_url || DEFAULT_AVATAR,
        isFollowing: false
      },
      likes: 0,
      stars: 0,
      comments: 0,
    }));
  } else {
      userPosts.value = [];
  }
};

watch(activeTab, () => {
    fetchContent();
});

onMounted(() => {
  fetchProfile();
});

const openEditModal = () => {
  isEditModalOpen.value = true;
  avatarFile.value = null;
  avatarPreview.value = null;
  editForm.value = {
    username: profile.value.username || '',
    bio: profile.value.bio || '',
    avatar_url: profile.value.avatar_url || ''
  };
};

const handleAvatarChange = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    avatarFile.value = input.files[0];
    avatarPreview.value = URL.createObjectURL(input.files[0]);
  }
};

const saveProfile = async () => {
  try {
    isSaving.value = true;
    let avatarUrl = editForm.value.avatar_url;

    if (avatarFile.value) {
      const url = await profileService.uploadAvatar(avatarFile.value);
      if (url) avatarUrl = url;
    }

    await profileService.updateProfile(user.value.id, {
      username: editForm.value.username,
      bio: editForm.value.bio,
      avatar_url: avatarUrl
    });

    await fetchProfile(); // Refresh data
    isEditModalOpen.value = false;
    showToast('个人资料已更新', 'success');
  } catch (error: any) {
    showToast(error.message || '更新失败', 'error');
  } finally {
    isSaving.value = false;
  }
};

const handleLogout = async () => {
  try {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
    showToast('已退出登录', 'success');
    router.push('/login');
  } catch (error: any) {
    showToast(error.message || '退出失败', 'error');
  }
};
</script>

<template>
  <div class="min-h-screen bg-white flex">
    <!-- Sidebar -->
    <div class="hidden lg:block w-[240px] flex-shrink-0">
        <Sidebar />
    </div>

    <!-- Main Content -->
    <main class="flex-1 min-w-0">
      <div class="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 pt-8 pb-12">
        <!-- Search Bar (Reused) -->
        <div class="w-full flex justify-center mb-12">
            <div class="relative w-full max-w-lg">
                <input 
                    type="text" 
                    placeholder="搜索小红书" 
                    class="w-full pl-10 pr-4 py-3 bg-gray-100/80 hover:bg-gray-100 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-gray-200 transition-all placeholder-gray-400 text-center"
                >
                <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            </div>
        </div>

        <!-- User Header -->
        <div v-if="user" class="flex flex-col items-center justify-center mb-16">
            <div class="flex items-start space-x-8">
                <!-- Avatar -->
                <div class="w-40 h-40 rounded-full border-2 border-gray-100 p-1 overflow-hidden flex-shrink-0">
                    <img 
                        :src="profile?.avatar_url || DEFAULT_AVATAR" 
                        class="w-full h-full rounded-full object-cover"
                    />
                </div>

                <!-- Info -->
                <div class="pt-4 max-w-lg">
                    <div class="flex items-center space-x-4 mb-3">
                        <h1 class="text-2xl font-bold text-gray-900">{{ profile?.username || user.email?.split('@')[0] }}</h1>
                        <!-- Edit Button -->
                        <button @click="openEditModal" class="p-1.5 hover:bg-gray-100 rounded-full transition-colors text-gray-500">
                            <Edit2 class="w-4 h-4" />
                        </button>
                    </div>
                    
                    <div class="text-xs text-gray-400 mb-4 flex items-center space-x-4">
                        <span>小红书号：{{ profile?.id?.substring(0, 8) || '49688903080' }}</span>
                        <div class="relative">
                            <button @click="handleLogout" class="hover:text-red-600 focus:outline-none" title="退出登录">
                                <LogOut class="w-4 h-4" />
                            </button>
                        </div>
                    </div>

                    <p class="text-sm text-gray-500 mb-6">{{ profile?.bio || '还没简介' }}</p>

                    <div class="flex items-center space-x-6 text-sm">
                        <div class="flex items-center space-x-1 cursor-pointer hover:text-gray-900 transition-colors">
                            <span class="text-gray-900 font-medium">0</span>
                            <span class="text-gray-500">关注</span>
                        </div>
                        <div class="flex items-center space-x-1 cursor-pointer hover:text-gray-900 transition-colors">
                            <span class="text-gray-900 font-medium">0</span>
                            <span class="text-gray-500">粉丝</span>
                        </div>
                        <div class="flex items-center space-x-1 cursor-pointer hover:text-gray-900 transition-colors">
                            <span class="text-gray-900 font-medium">0</span>
                            <span class="text-gray-500">获赞与收藏</span>
                        </div>
                    </div>

                    <div class="mt-6 flex flex-wrap gap-3">
                        <router-link
                            to="/itinerary"
                            class="inline-flex items-center rounded-full bg-red-500 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-red-600"
                        >
                            我的行程单
                        </router-link>
                        <router-link
                            to="/discovery"
                            class="inline-flex items-center rounded-full border border-gray-200 px-5 py-2.5 text-sm font-medium text-gray-600 transition-colors hover:border-gray-300 hover:text-gray-900"
                        >
                            去旅游发现
                        </router-link>
                    </div>
                </div>
            </div>
        </div>

        <!-- Edit Profile Modal -->
        <div v-if="isEditModalOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div class="bg-white rounded-xl w-full max-w-md p-6 relative">
                <h3 class="text-lg font-bold text-gray-900 mb-6 text-center">编辑个人资料</h3>
                
                <div class="space-y-6">
                    <!-- Avatar Upload -->
                    <div class="flex justify-center">
                        <div class="relative w-24 h-24 group cursor-pointer">
                            <img 
                                :src="avatarPreview || profile?.avatar_url || DEFAULT_AVATAR" 
                                class="w-full h-full rounded-full object-cover border-2 border-gray-100"
                            />
                            <div class="absolute inset-0 bg-black/30 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                <Camera class="w-8 h-8 text-white" />
                            </div>
                            <input type="file" accept="image/*" class="absolute inset-0 opacity-0 cursor-pointer" @change="handleAvatarChange" />
                        </div>
                    </div>

                    <!-- Username -->
                    <div class="space-y-2">
                        <label class="text-sm font-medium text-gray-700">名字</label>
                        <input 
                            v-model="editForm.username"
                            type="text" 
                            class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition-all"
                            placeholder="填写你的名字"
                        >
                    </div>

                    <!-- Bio -->
                    <div class="space-y-2">
                        <label class="text-sm font-medium text-gray-700">简介</label>
                        <textarea 
                            v-model="editForm.bio"
                            rows="3"
                            class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition-all resize-none"
                            placeholder="填写简介，让大家更了解你"
                        ></textarea>
                    </div>
                </div>

                <div class="flex space-x-4 mt-8">
                    <button 
                        @click="isEditModalOpen = false" 
                        class="flex-1 py-2.5 border border-gray-200 text-gray-600 rounded-full font-medium hover:bg-gray-50 transition-colors"
                    >
                        取消
                    </button>
                    <button 
                        @click="saveProfile"
                        :disabled="isSaving"
                        class="flex-1 py-2.5 bg-red-500 text-white rounded-full font-medium hover:bg-red-600 transition-colors disabled:opacity-70 flex items-center justify-center"
                    >
                        <Loader2 v-if="isSaving" class="w-4 h-4 mr-2 animate-spin" />
                        {{ isSaving ? '保存中...' : '保存' }}
                    </button>
                </div>
            </div>
        </div>

        <!-- Tabs -->
        <div class="flex justify-center border-b border-gray-100 mb-12">
            <div class="flex space-x-12">
                <button 
                    v-for="tab in tabs" 
                    :key="tab.id"
                    @click="activeTab = tab.id"
                    class="pb-3 text-base font-medium transition-colors relative px-2"
                    :class="activeTab === tab.id ? 'text-gray-900 font-bold' : 'text-gray-500 hover:text-gray-900'"
                >
                    {{ tab.label }}
                    <span v-if="activeTab === tab.id" class="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-red-500 rounded-full"></span>
                </button>
            </div>
        </div>

        <!-- Content Area -->
        <div v-if="userPosts.length === 0" class="flex flex-col items-center justify-center py-12 text-gray-300">
            <div class="w-32 h-32 mb-4 bg-gray-50 rounded-full flex items-center justify-center">
                 <!-- Simple placeholder illustration -->
                 <svg xmlns="http://www.w3.org/2000/svg" class="w-16 h-16 text-gray-200" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
            </div>
            <p class="text-sm">TA 还没有发布任何内容哦</p>
        </div>

        <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <PostCard 
                v-for="post in userPosts" 
                :key="post.id" 
                :post="post" 
            />
        </div>

      </div>
    </main>
  </div>
</template>
