<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';
import { safeGetSupabaseSession, safeGetSupabaseUser, safeSupabaseSignOut, supabase } from '@/utils/supabase';
import { useRouter } from 'vue-router';
import Toast from '@/components/Toast.vue';
import { useToast } from '@/composables/useToast';
import { usePresence } from '@/composables/usePresence';
import { RealtimeChannel } from '@supabase/supabase-js';

const { showToast } = useToast();
const { initPresence, cleanupPresence } = usePresence();
const router = useRouter();
const banChannel = ref<RealtimeChannel | null>(null);
const isProcessingBan = ref(false);

// 监听当前用户的状态变化（被封禁）
const setupBanListener = async () => {
  const user = await safeGetSupabaseUser();
  if (!user) return;

  // Cleanup existing channel
  if (banChannel.value) {
    await supabase.removeChannel(banChannel.value as any);
    banChannel.value = null;
  }

  console.log('Setting up ban listener for user:', user.id);

  const handleBan = async () => {
    if (isProcessingBan.value) return;
    isProcessingBan.value = true;
    
    showToast('您的账号已被封禁，即将退出登录。', 'error', 5000);
    
    // Give a small delay for toast to be seen, but not blocking
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    await safeSupabaseSignOut();
    router.push('/login');
    isProcessingBan.value = false;
  };

  // 1. Realtime Listener
  banChannel.value = supabase
    .channel(`ban-check:${user.id}`)
    .on('postgres_changes', { 
      event: 'UPDATE', 
      schema: 'public', 
      table: 'profiles',
      filter: `id=eq.${user.id}`
    }, async (payload) => {
      console.log('Profile update received:', payload);
      // Check if new row has 'banned' role directly from payload if available
      const newRole = (payload.new as any)?.role;
      if (newRole === 'banned') {
         await handleBan();
         return;
      }

      // Always refetch profile to be safe and accurate
      const { data } = await supabase.from('profiles').select('role').eq('id', user.id).single();
      if (data?.role === 'banned') {
        await handleBan();
      }
    })
    .subscribe((status) => {
      console.log('Ban listener status:', status);
    });

  // 2. Polling Fallback (Every 10 seconds) - Reduced frequency to avoid AbortError
  // This handles cases where Realtime might disconnect or be blocked
  const intervalId = setInterval(async () => {
    // Check local user state directly (sync) to avoid async locking issues
    const session = await safeGetSupabaseSession();
    if (!session) {
      clearInterval(intervalId);
      return;
    }

    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('role')
        .eq('id', user.id)
        .single();

      if (error) {
        // Ignore 406 Not Acceptable errors which might happen during transitions
        // Ignore AbortError which happens on navigation/unload
        if (error.code !== '406' && error.message !== 'Fetch is aborted' && !error.message.includes('AbortError')) {
          console.warn('Ban check polling error (ignored):', error.message);
        }
        return;
      }

      if (data?.role === 'banned') {
        clearInterval(intervalId);
        await handleBan();
      }
    } catch (err) {
      // Catch any other errors to prevent loop crash
      // console.warn('Ban polling exception:', err);
    }
  }, 10000); // Check every 10 seconds instead of 3

  // Attach interval ID to channel object for cleanup (hacky but works with local ref)
  (banChannel.value as any)._pollingInterval = intervalId;
}

onMounted(async () => {
  // Check if already banned on load
  const user = await safeGetSupabaseUser();
  if (user) {
    const { data } = await supabase.from('profiles').select('role').eq('id', user.id).single();
    if (data?.role === 'banned') {
      showToast('您的账号已被封禁，无法登录。', 'error');
      await safeSupabaseSignOut();
      router.push('/login');
      return;
    }
  }

  // Initial presence tracking
  initPresence();
  setupBanListener();

  // Listen for auth changes
  supabase.auth.onAuthStateChange(async (event, session) => {
    console.log('Auth state changed:', event);
    if (event === 'SIGNED_IN' && session?.user) {
      initPresence();
      setupBanListener();
      
      // Check ban status on login
      const { data } = await supabase.from('profiles').select('role').eq('id', session.user.id).single();
      if (data?.role === 'banned') {
        showToast('您的账号已被封禁，无法登录。', 'error');
        await safeSupabaseSignOut();
        router.push('/login');
      }
    } else if (event === 'SIGNED_OUT') {
      cleanupPresence();
      if (banChannel.value) {
        // Clear polling interval
        if ((banChannel.value as any)._pollingInterval) {
          clearInterval((banChannel.value as any)._pollingInterval);
        }
        await supabase.removeChannel(banChannel.value as any);
        banChannel.value = null;
      }
    }
  });
});

onUnmounted(() => {
  cleanupPresence();
  if (banChannel.value) {
    if ((banChannel.value as any)._pollingInterval) {
      clearInterval((banChannel.value as any)._pollingInterval);
    }
    supabase.removeChannel(banChannel.value as any);
  }
});
</script>

<template>
  <Toast />
  <!-- 封禁遮罩层：防止用户在被封禁后继续操作 -->
  <div v-if="isProcessingBan" class="fixed inset-0 z-[9998] bg-black/50 backdrop-blur-sm flex items-center justify-center">
    <div class="bg-white p-6 rounded-xl shadow-2xl max-w-sm w-full mx-4 text-center">
      <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-red-600"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
      </div>
      <h3 class="text-lg font-bold text-gray-900 mb-2">账号已被封禁</h3>
      <p class="text-gray-500 mb-4">您的账号因违反社区规定已被封禁，系统正在为您安全退出...</p>
      <div class="animate-pulse h-1 bg-red-200 rounded-full w-full overflow-hidden">
        <div class="h-full bg-red-500 w-2/3 animate-[loading_1s_ease-in-out_infinite]"></div>
      </div>
    </div>
  </div>
  <router-view />
</template>
