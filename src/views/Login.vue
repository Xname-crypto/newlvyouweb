<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { supabase } from '@/utils/supabase';
import AuthLayout from '@/components/AuthLayout.vue';
import { Loader2 } from 'lucide-vue-next';

const loginVideo = '/video/login-visual.mp4';

const router = useRouter();
const route = useRoute();
const email = ref('');
const password = ref('');
const loading = ref(false);
const errorMsg = ref('');

onMounted(() => {
  if (route.query.reason === 'banned') {
    errorMsg.value = '您的账号已被封禁，无法登录。如有疑问请联系管理员。';
  }
});

const handleLogin = async () => {
  if (!email.value || !password.value) {
    errorMsg.value = '请输入邮箱和密码';
    return;
  }

  try {
    loading.value = true;
    errorMsg.value = '';
    
    const { data: { user }, error } = await supabase.auth.signInWithPassword({
      email: email.value,
      password: password.value,
    });

    if (error) throw error;

    if (user) {
      // Check if user is admin
      const { data: profile } = await supabase
        .from('profiles')
        .select('role')
        .eq('id', user.id)
        .single();
      
      if (profile?.role === 'admin' || profile?.role === 'moderator') {
        router.push('/');
      } else {
        router.push('/');
      }
    } else {
      router.push('/');
    }
  } catch (error: any) {
    console.error('Login error:', error);
    if (error.message === 'Invalid login credentials') {
      errorMsg.value = '账号或密码错误';
    } else if (error.message.includes('Email not confirmed')) {
      errorMsg.value = '邮箱未验证，请检查您的邮箱完成验证';
    } else {
      errorMsg.value = error.message || '登录失败，请检查您的凭证';
    }
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <AuthLayout :video-src="loginVideo">
    <template #title>登录 椿天社</template>
    
    <form @submit.prevent="handleLogin" class="space-y-5">
      <div v-if="errorMsg" class="p-3 rounded bg-red-50 text-red-600 text-sm border border-red-100">
        {{ errorMsg }}
      </div>

      <div class="space-y-1">
        <label for="email" class="text-xs font-semibold text-gray-500 uppercase tracking-wider ml-1">邮箱</label>
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

      <div class="space-y-1">
        <div class="flex justify-between items-center ml-1">
          <label for="password" class="text-xs font-semibold text-gray-500 uppercase tracking-wider">密码</label>
        </div>
        <input
          id="password"
          name="password"
          v-model="password"
          type="password"
          placeholder="••••••••"
          class="w-full px-4 py-3 bg-gray-50 border border-transparent rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all"
          required
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full py-3 px-4 bg-blue-500 text-white font-bold rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-4 focus:ring-blue-500/20 transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center shadow-lg shadow-blue-500/30 mt-4"
      >
        <Loader2 v-if="loading" class="w-5 h-5 mr-2 animate-spin" />
        {{ loading ? '登录中...' : '登录' }}
      </button>

      <div class="flex items-center justify-between text-sm mt-6">
         <router-link to="/forgot-password" class="text-gray-500 hover:text-blue-500 transition-colors">
            忘记密码？
          </router-link>
        <div class="text-gray-500">
          还没有账号？
          <router-link to="/register" class="text-blue-500 font-semibold hover:underline">
            立即注册
          </router-link>
        </div>
      </div>
    </form>
  </AuthLayout>
</template>
