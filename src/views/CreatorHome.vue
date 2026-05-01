<script setup lang="ts">
import { ref, onMounted } from 'vue';
import CreatorHeader from '@/components/CreatorHeader.vue';
import PublishSidebar from '@/components/publish/PublishSidebar.vue';
import { supabase } from '@/utils/supabase';
import { profileService } from '@/services/profileService';
import { FileText, Video, Radio, HelpCircle } from 'lucide-vue-next';
import { DEFAULT_AVATAR } from '@/utils/avatar';

const user = ref<any>(null);
const profile = ref<any>(null);
const userStats = ref({
  following: 0,
  followers: 0,
  likesAndCollects: 0,
  likes: 0,
  collects: 0,
  comments: 0,
  shares: 0,
  views: 0,
  newFollowers: 0,
  netFollowers: 0,
  ctr: '0%',
  completionRate: '0%',
  unfollows: 0,
  profileVisits: 0
});
const activeTab = ref('notes');

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session) {
    user.value = session.user;
    profile.value = await profileService.fetchProfile(session.user.id);
    userStats.value = await profileService.fetchUserStats(session.user.id);
  }
});
</script>

<template>
  <div class="min-h-screen bg-[#f9f9f9] flex flex-col">
    <CreatorHeader />

    <div class="flex flex-1 overflow-hidden">
      <PublishSidebar />

      <main class="flex-1 overflow-y-auto p-6">
        <div class="max-w-[1200px] mx-auto space-y-6">
            <!-- User Info Card -->
            <div class="bg-white p-6 rounded-xl shadow-sm flex items-start justify-between">
                <div class="flex items-center space-x-4">
                    <div class="w-16 h-16 rounded-full border border-gray-100 p-0.5">
                        <img :src="profile?.avatar_url || DEFAULT_AVATAR" class="w-full h-full rounded-full" />
                    </div>
                    <div>
                        <div class="flex items-center space-x-2 mb-1">
                            <h2 class="text-lg font-bold text-gray-900">{{ profile?.username || '小红薯' }}</h2>
                            <span class="px-2 py-0.5 bg-green-50 text-green-600 text-xs rounded border border-green-100">账号状态正常</span>
                        </div>
                        <div class="flex items-center space-x-4 text-sm text-gray-500">
                            <span>{{ userStats.following }} 关注数</span>
                            <span>{{ userStats.followers }} 粉丝数</span>
                            <span>{{ userStats.likesAndCollects }} 获赞与收藏</span>
                        </div>
                        <div class="mt-1 text-xs text-gray-400">
                            小红书号：{{ profile?.id?.substring(0, 10) || '49688903080' }} | {{ profile?.bio || '还没简介' }}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Quick Actions -->
            <div class="bg-white p-6 rounded-xl shadow-sm">
                <h3 class="text-base font-bold text-gray-900 mb-4">新的创作</h3>
                <div class="grid grid-cols-2 gap-4">
                    <router-link to="/publish" class="flex items-center p-4 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors cursor-pointer group">
                        <div class="w-12 h-12 bg-orange-400 rounded-lg flex items-center justify-center text-white mr-4 shadow-sm group-hover:scale-105 transition-transform">
                            <FileText class="w-6 h-6" />
                        </div>
                        <div>
                            <div class="font-bold text-gray-900">发布图文笔记</div>
                            <div class="text-xs text-gray-500 mt-1">支持图片格式 png、jpg、jpeg</div>
                        </div>
                    </router-link>

                    <router-link to="/publish" class="flex items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors cursor-pointer group">
                        <div class="w-12 h-12 bg-blue-400 rounded-lg flex items-center justify-center text-white mr-4 shadow-sm group-hover:scale-105 transition-transform">
                            <Video class="w-6 h-6" />
                        </div>
                        <div>
                            <div class="font-bold text-gray-900">发布视频笔记</div>
                            <div class="text-xs text-gray-500 mt-1">支持视频格式 mp4、mov</div>
                        </div>
                    </router-link>
                </div>
            </div>

            <!-- Stats Overview -->
            <div class="bg-white p-6 rounded-xl shadow-sm">
                <div class="flex items-center justify-between mb-4 border-b border-gray-100 pb-2">
                    <div class="flex space-x-8">
                        <button 
                            @click="activeTab = 'notes'"
                            class="text-base font-bold pb-3 -mb-3 border-b-2 transition-colors"
                            :class="activeTab === 'notes' ? 'border-blue-500 text-gray-900' : 'border-transparent text-gray-500 hover:text-gray-900'"
                        >
                            笔记数据总览 <HelpCircle class="w-3 h-3 inline text-gray-300" />
                        </button>
                    </div>
                    <div class="text-sm text-gray-400 cursor-pointer hover:text-gray-600 flex items-center">
                        查看详情 <svg class="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                    </div>
                </div>

                <div class="flex items-center justify-between mb-8">
                    <div class="text-sm text-gray-500">
                        统计周期 01-08 至 01-14
                    </div>
                    <div class="flex text-sm border border-gray-200 rounded-md overflow-hidden">
                        <button class="px-3 py-1 bg-white text-gray-900 font-medium hover:bg-gray-50 border-r border-gray-200">近7日</button>
                        <button class="px-3 py-1 bg-gray-50 text-gray-500 hover:bg-gray-100">近30日</button>
                    </div>
                </div>

                <!-- Stats Grid -->
                <div class="grid grid-cols-6 gap-y-10 gap-x-4">
                    <div v-for="(item, i) in [
                        { label: '曝光数', value: userStats.views || 0 },
                        { label: '观看数', value: userStats.views || 0 },
                        { label: '点赞数', value: userStats.likes || 0 },
                        { label: '评论数', value: userStats.comments || 0 },
                        { label: '净涨粉', value: userStats.netFollowers || 0 },
                        { label: '新增关注', value: userStats.newFollowers || 0 },
                        { label: '封面点击率', value: userStats.ctr || '0%' },
                        { label: '视频完播率', value: userStats.completionRate || '0%' },
                        { label: '收藏数', value: userStats.collects || 0 },
                        { label: '分享数', value: userStats.shares || 0 },
                        { label: '取消关注', value: userStats.unfollows || 0 },
                        { label: '主页访客', value: userStats.profileVisits || 0 },
                    ]" :key="i" class="space-y-2 relative">
                        <div class="text-xs text-gray-500">{{ item.label }}</div>
                        <div class="text-2xl font-bold text-gray-900">{{ item.value }}</div>
                        <div class="text-xs text-gray-400">环比 -</div>
                        
                        <!-- Vertical Divider for specific columns -->
                        <div v-if="(i + 1) % 2 === 0 && (i + 1) % 6 !== 0" class="absolute right-0 top-2 bottom-2 w-px bg-gray-100 hidden"></div> 
                        <!-- Note: Implementing exact vertical dashed lines like screenshot requires more complex CSS or specific grid layout adjustments. 
                             Standard grid gap usually suffices for clean layout. -->
                    </div>
                </div>
            </div>
        </div>
      </main>
    </div>
  </div>
</template>
