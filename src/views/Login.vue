<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { clearSupabaseAuthDegraded, isSupabaseNetworkError, supabase } from '@/utils/supabase';
import AuthLayout from '@/components/AuthLayout.vue';
import { Loader2 } from 'lucide-vue-next';

const loginVideo = '/video/login-visual.mp4?v=auth-balanced-2';

const router = useRouter();
const route = useRoute();
const email = ref('');
const password = ref('');
const loading = ref(false);
const LOGIN_TIMEOUT_MS = 12000;

const withLoginTimeout = async <T,>(promise: Promise<T>): Promise<T> => {
  let timeoutId: number | undefined;

  try {
    return await Promise.race([
      promise,
      new Promise<never>((_, reject) => {
        timeoutId = window.setTimeout(() => {
          reject(new Error('登录服务响应较慢，请刷新页面后重试。'));
        }, LOGIN_TIMEOUT_MS);
      }),
    ]);
  } finally {
    if (timeoutId) {
      window.clearTimeout(timeoutId);
    }
  }
};

const getLoginErrorMessage = (error: any) => {
  const message = String(error?.message || '');
  const status = Number(error?.status || 0);

  if (isSupabaseNetworkError(error)) {
    return '无法连接登录服务，请检查网络、代理，或确认 Supabase 项目地址 VITE_SUPABASE_URL 是否可用。';
  }

  if (message === 'Invalid login credentials' || error?.code === 'invalid_credentials') {
    return '邮箱或密码不正确，请检查后重试。';
  }

  if (message.includes('Email not confirmed')) {
    return '邮箱尚未验证，请先完成邮箱验证后再登录。';
  }

  if (status === 400) {
    return '登录请求未通过校验，请确认邮箱和密码填写正确。';
  }

  return message || '登录失败，请稍后再试。';
};

onMounted(() => {
  if (route.query.reason === 'banned') {
    window.alert('登录失败\n\n账号已被封禁，无法登录。');
  }
});

const handleLogin = async () => {
  const normalizedEmail = email.value.trim();
  const normalizedPassword = password.value;

  if (!normalizedEmail || !normalizedPassword) {
    window.alert('登录失败\n\n请输入邮箱和密码。');
    return;
  }

  try {
    loading.value = true;
    clearSupabaseAuthDegraded();

    const {
      data: { user },
      error,
    } = await withLoginTimeout(supabase.auth.signInWithPassword({
      email: normalizedEmail,
      password: normalizedPassword,
    }));

    if (error) throw error;

    if (user) {
      window.setTimeout(() => {
        void supabase
          .from('profiles')
          .select('role')
          .eq('id', user.id)
          .single()
          .then(({ error: profileError }) => {
            if (profileError) {
              console.warn('Profile role lookup failed after login:', profileError);
            }
          });
      }, 0);
    }

    await router.push('/');
  } catch (error: any) {
    console.error('Login error:', {
      name: error?.name,
      message: error?.message,
      status: error?.status,
      code: error?.code,
      error,
    });

    window.alert(`登录失败\n\n${getLoginErrorMessage(error)}`);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <AuthLayout :video-src="loginVideo" content-offset-class="md:-translate-y-8">
    <template #title>
      <span class="inline-flex items-baseline gap-2">
        <span>登录</span>
        <span>椿天社</span>
      </span>
    </template>

    <form @submit.prevent="handleLogin" class="space-y-5">
      <div class="space-y-1">
        <label for="email" class="ml-1 text-xs font-semibold uppercase tracking-wider text-gray-500">邮箱</label>
        <input
          id="email"
          v-model="email"
          name="email"
          type="email"
          autocomplete="email"
          placeholder="your@email.com"
          class="w-full rounded-lg border border-transparent bg-gray-50 px-4 py-3 text-gray-900 placeholder-gray-400 transition-all focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-4 focus:ring-blue-500/10"
          required
        />
      </div>

      <div class="space-y-1">
        <div class="ml-1 flex items-center justify-between">
          <label for="password" class="text-xs font-semibold uppercase tracking-wider text-gray-500">密码</label>
        </div>
        <input
          id="password"
          v-model="password"
          name="password"
          type="password"
          autocomplete="current-password"
          placeholder="请输入密码"
          class="w-full rounded-lg border border-transparent bg-gray-50 px-4 py-3 text-gray-900 placeholder-gray-400 transition-all focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-4 focus:ring-blue-500/10"
          required
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="mt-4 flex w-full items-center justify-center rounded-lg bg-blue-500 px-4 py-3 font-bold text-white shadow-lg shadow-blue-500/30 transition-all hover:bg-blue-600 focus:outline-none focus:ring-4 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-70"
      >
        <Loader2 v-if="loading" class="mr-2 h-5 w-5 animate-spin" />
        {{ loading ? '登录中...' : '登录' }}
      </button>

      <div class="mt-6 flex items-center justify-between text-sm">
        <router-link to="/forgot-password" class="text-gray-500 transition-colors hover:text-blue-500">
          忘记密码？
        </router-link>
        <div class="text-gray-500">
          还没有账号？
          <router-link to="/register" class="font-semibold text-blue-500 hover:underline">
            立即注册
          </router-link>
        </div>
      </div>
    </form>
  </AuthLayout>
</template>
