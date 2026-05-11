<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { supabase } from '@/utils/supabase';
import AuthLayout from '@/components/AuthLayout.vue';
import { Loader2 } from 'lucide-vue-next';

const forgotPasswordVideo = '/video/fp_v3.mp4?v=auth-balanced-2';

const router = useRouter();
const password = ref('');
const confirmPassword = ref('');
const loading = ref(false);
const errorMsg = ref('');
const successMsg = ref('');

onMounted(async () => {
  // Check if we have a session. If the user clicked the reset link, 
  // Supabase client should have handled the hash and set the session.
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    errorMsg.value = '无效或过期的链接。请重新请求重置密码。';
  }
});

const handleUpdatePassword = async () => {
  if (!password.value || !confirmPassword.value) {
    errorMsg.value = '请填写所有必填项';
    return;
  }

  if (password.value !== confirmPassword.value) {
    errorMsg.value = '两次输入的密码不一致';
    return;
  }

  if (password.value.length < 6) {
    errorMsg.value = '密码长度至少需要6位';
    return;
  }

  try {
    loading.value = true;
    errorMsg.value = '';
    
    const { error } = await supabase.auth.updateUser({
      password: password.value
    });

    if (error) throw error;

    successMsg.value = '密码已成功修改！正在跳转到登录页...';
    
    setTimeout(() => {
      router.push('/login');
    }, 2000);

  } catch (error: any) {
    console.error('Update password error:', error);
    errorMsg.value = error.message || '密码修改失败，请稍后重试';
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <AuthLayout :video-src="forgotPasswordVideo">
    <template #title>重置密码</template>
    <template #subtitle>请输入您的新密码</template>

    <form @submit.prevent="handleUpdatePassword" class="space-y-6">
      <div v-if="errorMsg" class="p-3 rounded bg-red-50 text-red-600 text-sm border border-red-100">
        {{ errorMsg }}
      </div>
      <div v-if="successMsg" class="p-3 rounded bg-green-50 text-green-600 text-sm border border-green-100">
        {{ successMsg }}
      </div>

      <div class="space-y-1">
        <label for="password" class="text-xs font-semibold text-gray-500 uppercase tracking-wider ml-1">新密码</label>
        <input
          id="password"
          name="password"
          v-model="password"
          type="password"
          placeholder="••••••••"
          class="w-full px-4 py-3 bg-gray-50 border border-transparent rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all"
          required
          :disabled="!!successMsg"
        />
      </div>

      <div class="space-y-1">
        <label for="confirmPassword" class="text-xs font-semibold text-gray-500 uppercase tracking-wider ml-1">确认新密码</label>
        <input
          id="confirmPassword"
          name="confirmPassword"
          v-model="confirmPassword"
          type="password"
          placeholder="••••••••"
          class="w-full px-4 py-3 bg-gray-50 border border-transparent rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all"
          required
          :disabled="!!successMsg"
        />
      </div>

      <button
        type="submit"
        :disabled="loading || !!successMsg"
        class="w-full py-3 px-4 bg-blue-500 text-white font-bold rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-4 focus:ring-blue-500/20 transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center shadow-lg shadow-blue-500/30"
      >
        <Loader2 v-if="loading" class="w-5 h-5 mr-2 animate-spin" />
        {{ loading ? '更新中...' : '更新密码' }}
      </button>
    </form>
  </AuthLayout>
</template>
