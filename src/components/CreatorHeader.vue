<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { supabase } from '@/utils/supabase';
import { Bell, AlertCircle } from 'lucide-vue-next';
import { useRouter } from 'vue-router';
import { useToast } from '@/composables/useToast';
import { DEFAULT_AVATAR } from '@/utils/avatar';

const router = useRouter();
const { showToast } = useToast();
const user = ref<any>(null);
const profile = ref<any>(null);

const handleNotificationClick = async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    showToast('请先登录后再查看通知', 'warning');
    return;
  }
  router.push('/notifications');
};

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session) {
    user.value = session.user;
    // Fetch minimal profile info
    const { data } = await supabase
      .from('profiles')
      .select('username, avatar_url')
      .eq('id', session.user.id)
      .single();
    profile.value = data;
  }
});
</script>

<template>
  <header class="h-16 bg-white border-b border-gray-100 flex items-center justify-between px-6 sticky top-0 z-50">
    <div class="flex items-center space-x-2">
      <router-link to="/community" class="text-3xl font-black text-red-500 tracking-tighter" style="font-family: 'PangMenZhengDao', serif;">椿天社</router-link>
      <span class="text-sm text-gray-500 pl-2 border-l border-gray-300 ml-2">创作服务平台</span>
    </div>
    
    <div class="flex items-center space-x-6">
      <div v-if="profile" class="flex items-center text-gray-500 hover:text-gray-900 cursor-pointer text-sm">
          <AlertCircle class="w-4 h-4 mr-1" />
          <span>{{ profile.username || '小红薯' }}</span>
      </div>
      <button 
        class="text-gray-400 hover:text-gray-600"
        @click="handleNotificationClick"
      >
          <Bell class="w-5 h-5" />
      </button>
      <div class="w-8 h-8 rounded-full bg-gray-200 overflow-hidden cursor-pointer">
          <img :src="profile?.avatar_url || DEFAULT_AVATAR" />
      </div>
    </div>
  </header>
</template>
