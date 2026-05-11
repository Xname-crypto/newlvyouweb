<script setup lang="ts">
import { ref } from 'vue';
import { supabase } from '@/utils/supabase';
import AuthLayout from '@/components/AuthLayout.vue';
import { Loader2, ArrowLeft } from 'lucide-vue-next';

const forgotPasswordVideo = '/video/fp_v3.mp4?v=auth-balanced-2';

const email = ref('');
const loading = ref(false);
const errorMsg = ref('');
const successMsg = ref('');

const handleReset = async () => {
  if (!email.value) {
    errorMsg.value = '请输入您的电子邮箱';
    return;
  }

  try {
    loading.value = true;
    errorMsg.value = '';
    successMsg.value = '';
    
    // Configure the redirect URL to point to the ResetPassword page
    const redirectTo = `${window.location.origin}/reset-password`;

    const { error } = await supabase.auth.resetPasswordForEmail(email.value, {
      redirectTo,
    });

    if (error) throw error;

    successMsg.value = '重置链接已发送到您的邮箱，请查收。';
    email.value = ''; // Clear input
  } catch (error: any) {
    console.error('Reset password error:', error);
    errorMsg.value = error.message || '发送重置邮件失败，请稍后重试';
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <AuthLayout :video-src="forgotPasswordVideo">
    <template #title>找回密码</template>
    <template #subtitle>输入您的邮箱以重置密码</template>

    <form @submit.prevent="handleReset" class="space-y-6">
      <div v-if="errorMsg" class="p-3 rounded bg-red-50 text-red-600 text-sm border border-red-100">
        {{ errorMsg }}
      </div>
      <div v-if="successMsg" class="p-3 rounded bg-green-50 text-green-600 text-sm border border-green-100">
        {{ successMsg }}
      </div>

      <div class="space-y-1">
        <label for="email" class="text-xs font-semibold text-gray-500 uppercase tracking-wider ml-1">电子邮箱</label>
        <input
          id="email"
          name="email"
          v-model="email"
          type="email"
          placeholder="your@email.com"
          class="w-full px-4 py-3 bg-gray-50 border border-transparent rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all"
          required
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full py-3 px-4 bg-blue-500 text-white font-bold rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-4 focus:ring-blue-500/20 transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center shadow-lg shadow-blue-500/30"
      >
        <Loader2 v-if="loading" class="w-5 h-5 mr-2 animate-spin" />
        {{ loading ? '发送重置链接' : '发送' }}
      </button>

      <div class="text-center text-sm mt-6">
        <router-link to="/login" class="inline-flex items-center text-blue-500 font-semibold hover:underline">
          <ArrowLeft class="w-4 h-4 mr-1" />
          返回登录
        </router-link>
      </div>
    </form>
  </AuthLayout>
</template>
