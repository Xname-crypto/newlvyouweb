<script setup lang="ts">
import { ref, onMounted } from 'vue';
import Sidebar from '@/components/community/Sidebar.vue';
import { Search } from 'lucide-vue-next';
import { notificationService } from '@/services/notificationService';
import { useToast } from '@/composables/useToast';
import { supabase } from '@/utils/supabase';
import { useRouter } from 'vue-router';
import { DEFAULT_AVATAR } from '@/utils/avatar';

const router = useRouter();
const { showToast } = useToast();

const activeTab = ref('comments'); // 'comments', 'likes', 'follows'
const notifications = ref<any[]>([]);
const loading = ref(false);
const isLoggedIn = ref(true);

const checkAuth = async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    isLoggedIn.value = false;
    showToast('请先登录以查看通知', 'warning');
    router.push('/login');
    return false;
  }
  return true;
};

const handleFollowBack = async (item: any) => {
  try {
    // Optimistic update
    item.is_following = !item.is_following;

    if (item.is_following) {
        await notificationService.followUser(item.user.id);
        showToast('已关注', 'success');
    } else {
        await notificationService.unfollowUser(item.user.id);
        showToast('已取消关注', 'success');
    }
  } catch (error) {
    // Revert
    item.is_following = !item.is_following;
    showToast('操作失败', 'error');
  }
};

const unreadCounts = ref({ likes: 0, comments: 0, follows: 0 });const fetchUnread = async () => {
  unreadCounts.value = await notificationService.fetchUnreadCounts();
};

const loadNotifications = async () => {
  loading.value = true;
  notifications.value = [];
  
  // Mark current tab as read
  if (activeTab.value === 'likes') await notificationService.markAsRead('like');
  else if (activeTab.value === 'comments') await notificationService.markAsRead('comment');
  else if (activeTab.value === 'follows') await notificationService.markAsRead('follow');
  
  // Refresh counts
  await fetchUnread();

  try {
    if (activeTab.value === 'likes') {
      const data = await notificationService.fetchLikesAndCollects();
      notifications.value = data.map((item: any) => {
        let actionText = '';
        let postTitle = '';
        let postImage = '';

        if (item.type === 'like') {
            actionText = item.comment_id ? '赞了你的评论' : '赞了你的笔记';
        } else if (item.type === 'collect') {
            actionText = '收藏了你的笔记';
        }

        if (item.posts) {
            postTitle = item.posts.title;
            postImage = item.posts.media_urls?.[0] || 'https://picsum.photos/seed/default/100/100';
        } else if (item.comments) {
            // If it's a comment like, we might want to show comment content or fetch post info
            // For now, let's show comment content if available
             postTitle = item.comments.content; 
        }

        return {
          id: item.id,
          user: {
            name: item.profiles?.username || '未知用户',
            avatar: item.profiles?.avatar_url || DEFAULT_AVATAR
          },
          action: actionText,
          content: item.comment_id ? item.comments?.content : null, // Show comment content if it's a comment like
          time: new Date(item.created_at).toLocaleString(),
          count: 1, // Placeholder for aggregation if needed
          post: item.posts ? {
            title: postTitle,
            image: postImage
          } : null
        };
      });
    } else if (activeTab.value === 'comments') {
      const data = await notificationService.fetchCommentsAndMentions();
      notifications.value = data.map((item: any) => ({
        id: item.id,
        user: {
          id: item.user_id, // Added id for navigation/actions
          name: item.profiles?.username || '未知用户',
          avatar: item.profiles?.avatar_url || DEFAULT_AVATAR
        },
        action: item.is_reply ? '回复了你的评论' : '评论了你的笔记',
        content: item.content,
        time: new Date(item.created_at).toLocaleString(),
        post: {
          title: item.posts?.title,
          image: item.posts?.media_urls?.[0] || 'https://picsum.photos/seed/default/100/100'
        }
      }));
    } else if (activeTab.value === 'follows') {
      const data = await notificationService.fetchNewFollowers();
      notifications.value = data.map((item: any) => ({
        id: item.id,
        user: {
          id: item.follower_id, // Added id for navigation/actions (using follower_id from follows table)
          name: item.profiles?.username || '未知用户',
          avatar: item.profiles?.avatar_url || DEFAULT_AVATAR,
          bio: item.profiles?.bio || '这个人很懒，什么都没写'
        },
        action: '关注了你',
        time: new Date(item.created_at).toLocaleString(),
        is_following: item.is_following
      }));
    }
  } catch (error) {
    console.error('Failed to load notifications:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  const authenticated = await checkAuth();
  if (authenticated) {
    fetchUnread();
    loadNotifications();
  }
});
</script>

<template>
  <div class="min-h-screen bg-white flex">
    <!-- Sidebar -->
    <div class="hidden lg:block w-[240px] flex-shrink-0">
        <Sidebar />
    </div>

    <!-- Main Content -->
    <main class="flex-1 min-w-0">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <!-- Header -->
        <div class="flex items-center justify-between mb-8">
           <div class="relative w-64">
                <input 
                    type="text" 
                    placeholder="搜索消息" 
                    class="w-full pl-10 pr-4 py-2 bg-gray-100 rounded-full text-sm focus:outline-none focus:ring-1 focus:ring-gray-200"
                >
                <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
           </div>
           <div class="text-sm text-gray-500 space-x-4">
               <a href="#" class="hover:text-gray-900">创作中心</a>
               <a href="#" class="hover:text-gray-900">业务合作</a>
           </div>
        </div>

        <!-- Tabs -->
        <div class="flex space-x-8 border-b border-gray-100 mb-6">
            <button 
                @click="activeTab = 'comments'; loadNotifications()"
                class="pb-3 text-sm font-medium transition-colors relative"
                :class="activeTab === 'comments' ? 'text-gray-900' : 'text-gray-500 hover:text-gray-700'"
            >
                <div class="relative">
                    评论和@
                    <span v-if="unreadCounts.comments > 0" class="absolute -top-1.5 -right-3 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] text-white font-medium shadow-sm">
                        {{ unreadCounts.comments > 99 ? '99+' : unreadCounts.comments }}
                    </span>
                </div>
                <span v-if="activeTab === 'comments'" class="absolute bottom-0 left-1/2 -translate-x-1/2 w-full h-0.5 bg-red-500 rounded-full"></span>
            </button>
            <button 
                @click="activeTab = 'likes'; loadNotifications()"
                class="pb-3 text-sm font-medium transition-colors relative"
                :class="activeTab === 'likes' ? 'text-gray-900' : 'text-gray-500 hover:text-gray-700'"
            >
                <div class="relative">
                    赞和收藏
                    <span v-if="unreadCounts.likes > 0" class="absolute -top-1.5 -right-3 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] text-white font-medium shadow-sm">
                        {{ unreadCounts.likes > 99 ? '99+' : unreadCounts.likes }}
                    </span>
                </div>
                <span v-if="activeTab === 'likes'" class="absolute bottom-0 left-1/2 -translate-x-1/2 w-full h-0.5 bg-red-500 rounded-full"></span>
            </button>
            <button 
                @click="activeTab = 'follows'; loadNotifications()"
                class="pb-3 text-sm font-medium transition-colors relative"
                :class="activeTab === 'follows' ? 'text-gray-900' : 'text-gray-500 hover:text-gray-700'"
            >
                <div class="relative">
                    新增关注
                    <span v-if="unreadCounts.follows > 0" class="absolute -top-1.5 -right-3 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] text-white font-medium shadow-sm">
                        {{ unreadCounts.follows > 99 ? '99+' : unreadCounts.follows }}
                    </span>
                </div>
                <span v-if="activeTab === 'follows'" class="absolute bottom-0 left-1/2 -translate-x-1/2 w-full h-0.5 bg-red-500 rounded-full"></span>
            </button>
        </div>

        <!-- Content List -->
        <div v-if="loading" class="flex justify-center py-12">
            <div class="w-6 h-6 border-2 border-gray-200 border-t-blue-500 rounded-full animate-spin"></div>
        </div>

        <div v-else-if="notifications.length === 0" class="flex flex-col items-center justify-center py-20 text-gray-400">
            <p>暂无消息</p>
        </div>

        <div v-else class="space-y-0">
            <div v-for="(item, index) in notifications" :key="item.id">
                <div class="flex items-start justify-between group py-6">
                    <!-- Left: Avatar & Info -->
                    <div class="flex items-start space-x-3">
                        <img :src="item.user.avatar" class="w-10 h-10 rounded-full object-cover border border-gray-100 flex-shrink-0" />
                        <div class="pt-0.5">
                            <div class="flex items-baseline space-x-2">
                                <span class="text-sm font-semibold text-gray-900">{{ item.user.name }}</span>
                            </div>
                            <div class="flex items-center text-xs text-gray-500 mt-0.5">
                                <span>{{ item.action }}</span>
                                <span class="text-gray-400 ml-2">{{ item.time }}</span>
                            </div>
                            <div v-if="activeTab === 'likes' && item.count" class="text-xs text-gray-400 mt-1 pl-3 border-l-2 border-gray-200 hidden">
                                 {{ item.count }}
                            </div>
                            <p v-if="item.content" class="text-sm text-gray-500 mt-2 pl-3 border-l-2 border-gray-200 line-clamp-2">
                                {{ item.content.replace(/^回复 @[^：]+：/, '') }}
                            </p>
                            <p v-if="item.user.bio" class="text-xs text-gray-400 mt-1">{{ item.user.bio }}</p>
                        </div>
                    </div>

                    <!-- Right: Post Thumbnail or Button -->
                    <div v-if="item.post" class="w-12 h-12 rounded overflow-hidden bg-gray-100 flex-shrink-0 ml-4">
                        <img :src="item.post.image" class="w-full h-full object-cover" />
                    </div>
                    <button 
                        v-else-if="activeTab === 'follows'"
                        class="px-4 py-1.5 text-xs font-medium rounded-full transition-colors flex-shrink-0 ml-4"
                        :class="item.is_following ? 'text-gray-500 bg-gray-100 hover:bg-gray-200' : 'text-white bg-red-500 hover:bg-red-600'"
                        @click="handleFollowBack(item)"
                    >
                        {{ item.is_following ? '互相关注' : '回关' }}
                    </button>
                </div>
                <!-- Divider -->
                <div class="h-px bg-gray-100 w-full"></div>
            </div>
            
            <!-- Footer -->
            <div class="py-8 text-center">
                <div class="flex items-center justify-center space-x-4">
                    <div class="h-px bg-gray-200 w-16"></div>
                    <span class="text-xs text-gray-400 uppercase tracking-widest">- THE END -</span>
                    <div class="h-px bg-gray-200 w-16"></div>
                </div>
            </div>
        </div>
      </div>
    </main>
  </div>
</template>
