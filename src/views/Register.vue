<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { supabase } from '@/utils/supabase';
import { profileService } from '@/services/profileService';
import AuthLayout from '@/components/AuthLayout.vue';
import InterestChromaGrid from '@/components/register/InterestChromaGrid.vue';
import RegisterStepper from '@/components/register/RegisterStepper.vue';
import { Loader2, User, Mail, Lock, ArrowRight, Check, Sparkles, MapPin, Camera, Coffee, Mountain, Gamepad2, Music, Eye, EyeOff, Briefcase, Upload, ArrowLeft, CheckCircle2, XCircle } from 'lucide-vue-next';

const registerVideo = '/video/register-visual.mp4?v=auth-balanced-2';

const router = useRouter();
const currentStep = ref(1);
const loading = ref(false);
const errorMsg = ref('');
const showPassword = ref(false);
const showConfirmPassword = ref(false);

// File input ref and trigger
const fileInput = ref<HTMLInputElement | null>(null);
const triggerFileInputClick = () => {
  fileInput.value?.click();
};

// Form Data
const formData = ref({
  email: '',
  password: '',
  confirmPassword: '',
  username: '',
  job: '',
  bio: '',
  avatarFile: null as File | null,
  avatarPreview: '',
  selectedVibes: [] as string[]
});

const vibes = [
  { id: 'adventure', label: '探险', icon: Mountain, color: 'bg-orange-100 text-orange-600' },
  { id: 'photography', label: '摄影', icon: Camera, color: 'bg-blue-100 text-blue-600' },
  { id: 'food', label: '美食', icon: Coffee, color: 'bg-yellow-100 text-yellow-600' },
  { id: 'nature', label: '自然', icon: Sparkles, color: 'bg-green-100 text-green-600' },
  { id: 'city', label: '城市', icon: MapPin, color: 'bg-purple-100 text-purple-600' },
  { id: 'music', label: '音乐', icon: Music, color: 'bg-pink-100 text-pink-600' },
];

const registerSteps = [
  { id: 1, code: '01', label: 'Introduction' },
  { id: 2, code: '02', label: 'Identity' },
  { id: 3, code: '03', label: 'Interests' },
  { id: 4, code: '04', label: 'Success' },
];

const toggleVibe = (vibeId: string) => {
  const index = formData.value.selectedVibes.indexOf(vibeId);
  if (index === -1) {
    if (formData.value.selectedVibes.length < 3) {
      formData.value.selectedVibes.push(vibeId);
    }
  } else {
    formData.value.selectedVibes.splice(index, 1);
  }
};

const handleAvatarChange = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    const file = input.files[0];
    formData.value.avatarFile = file;
    formData.value.avatarPreview = URL.createObjectURL(file);
  }
};

// Step 1: Create Account (Validate Only)
const handleStep1 = async () => {
  if (!formData.value.email || !formData.value.password || !formData.value.confirmPassword) {
    errorMsg.value = '请填写所有必填项';
    return;
  }

  if (formData.value.password !== formData.value.confirmPassword) {
    errorMsg.value = '两次输入的密码不一致';
    return;
  }

  if (formData.value.password.length < 6) {
    errorMsg.value = '密码长度至少需要6位';
    return;
  }

  // Clear errors and proceed
  errorMsg.value = '';
  currentStep.value = 2;
};

// Step 2: Identity Setup (Validate Only)
const handleStep2 = async () => {
  // Mark fields as touched to trigger validation UI
  isUsernameTouched.value = true;
  isJobTouched.value = true;

  const username = formData.value.username.trim();

  if (!username) {
    errorMsg.value = '请输入昵称';
    return;
  }

  if (username.length < 3) {
    errorMsg.value = '昵称至少需要3个字符';
    return;
  }

  if (!formData.value.job) {
    errorMsg.value = '请输入职业/身份';
    return;
  }

  formData.value.username = username;
  
  errorMsg.value = '';
  currentStep.value = 3;
};

// Step 3: Interests & Final Registration
const handleRegistration = async () => {
  try {
    loading.value = true;
    errorMsg.value = '';

    // Construct bio with vibes
    let finalBio = formData.value.bio || '';
    if (formData.value.selectedVibes.length > 0) {
      const vibeLabels = formData.value.selectedVibes
        .map(v => vibes.find(i => i.id === v)?.label)
        .join('、');
      finalBio = finalBio ? `${finalBio}\n\n兴趣: ${vibeLabels}` : `兴趣: ${vibeLabels}`;
    }

    // Prepare metadata for the trigger to insert
    const metaData = {
      username: formData.value.username,
      job: formData.value.job,
      bio: finalBio,
      // We can't upload avatar yet, so we can't pass avatar_url in metadata unless we use a public placeholder
    };

    // 1. Sign Up User
    const { data, error } = await supabase.auth.signUp({
      email: formData.value.email,
      password: formData.value.password,
      options: {
        data: metaData
      }
    });

    if (error) throw error;

    if (data.user) {
      // 2. If we have a session (user logged in automatically), try to upload avatar
      if (data.session) {
        if (formData.value.avatarFile) {
          try {
             const url = await profileService.uploadAvatar(formData.value.avatarFile);
             if (url) {
               await profileService.updateProfile(data.user.id, { avatar_url: url });
             }
          } catch (uploadError) {
            console.error('Avatar upload failed:', uploadError);
            // Non-critical error, continue
          }
        }
      } 
      
      // Proceed to success step
      currentStep.value = 4;
    }
  } catch (error: any) {
    console.error('Registration error:', error);
    errorMsg.value = error.message || '注册失败，请稍后重试';
    // If error (e.g. email taken), user stays on Step 3 or we could move them back?
    // Staying on Step 3 allows them to retry.
  } finally {
    loading.value = false;
  }
};

const handleFinish = () => {
  router.push('/');
};

const isUsernameTouched = ref(false);
const isJobTouched = ref(false);

const isUsernameValid = computed(() => formData.value.username.trim().length >= 3);

const handleBack = () => {
  if (currentStep.value > 1) {
    currentStep.value--;
  } else {
    router.push('/login');
  }
};
</script>

<template>
  <AuthLayout 
    :video-src="registerVideo" 
    :show-back="currentStep > 1"
    @back="handleBack"
  >
    <!-- Header/Title Area -->
    <template #title>
      <div class="mb-2 flex w-full flex-col items-start space-y-3 pr-12 pt-1 md:pr-14">
        <!-- Step Indicator (e.g., 01 — INTRODUCTION) -->
        <RegisterStepper class="md:mt-px" :current-step="currentStep" :steps="registerSteps" />

        <h1 class="text-3xl font-extrabold text-gray-900 leading-tight">
          <span v-if="currentStep === 1">加入 椿天社</span>
          <span v-else-if="currentStep === 2">完善身份</span>
          <span v-else-if="currentStep === 3">选择兴趣</span>
          <span v-else>欢迎加入!</span>
        </h1>
        <p class="text-gray-500 text-sm font-medium">
          <span v-if="currentStep === 1">开启您的专属旅程</span>
          <span v-else-if="currentStep === 2">让大家更好地认识您</span>
          <span v-else-if="currentStep === 3">发现志同道合的朋友</span>
          <span v-else>一切准备就绪</span>
        </p>
      </div>
    </template>
    
    <div class="mt-6 relative">


      <!-- Step 1: Account Info -->
      <form v-if="currentStep === 1" @submit.prevent="handleStep1" class="space-y-5 animate-in fade-in slide-in-from-right-4 duration-300">
        <div class="space-y-1">
          <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider ml-1">邮箱</label>
          <div class="relative">
            <Mail class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              v-model="formData.email"
              type="email"
              placeholder="name@example.com"
              class="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all"
              required
            />
          </div>
        </div>

        <div class="space-y-1">
          <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider ml-1">密码</label>
          <div class="relative">
            <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              v-model="formData.password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="••••••••"
              class="w-full pl-10 pr-12 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all"
              required
            />
            <button 
              type="button"
              v-show="formData.password"
              @click="showPassword = !showPassword"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-black hover:text-gray-700 focus:outline-none"
            >
              <EyeOff v-if="!showPassword" class="w-5 h-5" />
              <Eye v-else class="w-5 h-5" />
            </button>
          </div>
        </div>

        <div class="space-y-1">
          <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider ml-1">确认密码</label>
          <div class="relative">
            <Check class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              v-model="formData.confirmPassword"
              :type="showConfirmPassword ? 'text' : 'password'"
              placeholder="••••••••"
              class="w-full pl-10 pr-12 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all"
              required
            />
            <button 
              type="button"
              v-show="formData.confirmPassword"
              @click="showConfirmPassword = !showConfirmPassword"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-black hover:text-gray-700 focus:outline-none"
            >
              <EyeOff v-if="!showConfirmPassword" class="w-5 h-5" />
              <Eye v-else class="w-5 h-5" />
            </button>
          </div>
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3.5 px-4 bg-gray-900 text-white font-bold rounded-xl hover:bg-black focus:outline-none focus:ring-4 focus:ring-gray-900/20 transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center shadow-lg mt-6"
        >
          <Loader2 v-if="loading" class="w-5 h-5 mr-2 animate-spin" />
          {{ loading ? '处理中...' : '继续' }}
          <ArrowRight v-if="!loading" class="w-4 h-4 ml-2" />
        </button>

        <div class="text-center text-sm text-gray-500 pt-2">
          已有账号？
          <router-link to="/login" class="text-blue-600 font-semibold hover:underline">
            立即登录
          </router-link>
        </div>
      </form>

      <!-- Step 2: Identity (Username, Job, Avatar) -->
      <div v-else-if="currentStep === 2" class="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
        <!-- Avatar Upload -->
        <div class="flex justify-center mb-6">
          <div class="relative group cursor-pointer" @click="triggerFileInputClick">
            <div class="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center overflow-hidden border-2 border-dashed border-gray-300 group-hover:border-blue-500 transition-all">
              <img v-if="formData.avatarPreview" :src="formData.avatarPreview" class="w-full h-full object-cover" />
              <Camera v-else class="w-8 h-8 text-gray-400 group-hover:text-blue-500" />
            </div>
            <div class="absolute bottom-0 right-0 bg-blue-500 text-white p-1.5 rounded-full shadow-md group-hover:scale-110 transition-transform">
              <Upload class="w-4 h-4" />
            </div>
            <input 
              ref="fileInput" 
              type="file" 
              accept="image/*" 
              class="hidden" 
              @change="handleAvatarChange"
            />
          </div>
        </div>

        <div class="space-y-1">
          <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider ml-1">昵称</label>
          <div class="relative">
            <User class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              v-model="formData.username"
              type="text"
              placeholder="例如: 旅行家小明"
              class="w-full pl-10 pr-10 py-3 bg-gray-50 border rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:bg-white focus:ring-4 transition-all"
              :class="[
                isUsernameValid
                  ? 'border-green-500 focus:border-green-500 focus:ring-green-500/10' 
                  : (isUsernameTouched ? 'border-red-500 focus:border-red-500 focus:ring-red-500/10' : 'border-gray-200 focus:border-blue-500 focus:ring-blue-500/10')
              ]"
              @blur="isUsernameTouched = true"
            />
            <div class="absolute right-3 top-1/2 -translate-y-1/2">
              <CheckCircle2 v-if="isUsernameValid" class="w-5 h-5 text-green-500" />
              <XCircle v-else-if="isUsernameTouched" class="w-5 h-5 text-red-500" />
            </div>
          </div>
          <p v-if="isUsernameTouched && formData.username && !isUsernameValid" class="ml-1 text-xs font-medium text-red-500">
            昵称至少需要3个字符
          </p>
        </div>

        <div class="space-y-1">
          <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider ml-1">职业 / 身份</label>
          <div class="relative">
            <Briefcase class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              v-model="formData.job"
              type="text"
              placeholder="例如: 摄影师, 学生, 自由职业者"
              class="w-full pl-10 pr-10 py-3 bg-gray-50 border rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:bg-white focus:ring-4 transition-all"
              :class="[
                formData.job 
                  ? 'border-green-500 focus:border-green-500 focus:ring-green-500/10' 
                  : (isJobTouched ? 'border-red-500 focus:border-red-500 focus:ring-red-500/10' : 'border-gray-200 focus:border-blue-500 focus:ring-blue-500/10')
              ]"
              @blur="isJobTouched = true"
            />
            <div class="absolute right-3 top-1/2 -translate-y-1/2">
              <CheckCircle2 v-if="formData.job" class="w-5 h-5 text-green-500" />
              <XCircle v-else-if="isJobTouched" class="w-5 h-5 text-red-500" />
            </div>
          </div>
        </div>

        <button
          @click="handleStep2"
          :disabled="loading"
          class="w-full py-3.5 px-4 bg-gray-900 text-white font-bold rounded-xl hover:bg-black focus:outline-none focus:ring-4 focus:ring-gray-900/20 transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center shadow-lg"
        >
          <Loader2 v-if="loading" class="w-5 h-5 mr-2 animate-spin" />
          {{ loading ? '下一步' : '下一步' }}
        </button>
      </div>

      <!-- Step 3: Interests (Vibes) -->
      <div v-else-if="currentStep === 3" class="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
        <div class="text-center mb-6">
          <p class="text-sm text-gray-500">选择您感兴趣的领域 (最多选3个)</p>
        </div>

        <InterestChromaGrid
          :items="vibes"
          :selected="formData.selectedVibes"
          :max-selected="3"
          @toggle="toggleVibe"
        />

        <button
          @click="handleRegistration"
          :disabled="loading"
          class="w-full py-3.5 px-4 bg-gray-900 text-white font-bold rounded-xl hover:bg-black focus:outline-none focus:ring-4 focus:ring-gray-900/20 transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center shadow-lg mt-4 group"
        >
          <Loader2 v-if="loading" class="w-5 h-5 mr-2 animate-spin" />
          {{ loading ? '处理中...' : '完成注册' }}
          <ArrowRight v-if="!loading" class="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>

      <!-- Step 4: Success -->
      <div v-else class="text-center py-8 animate-in fade-in zoom-in-95 duration-500">
        <div class="w-24 h-24 bg-green-50 rounded-full mx-auto flex items-center justify-center mb-6 shadow-sm relative">
          <Sparkles class="w-10 h-10 text-green-500 absolute top-0 right-0 animate-bounce" style="animation-delay: 0.5s" />
          <Check class="w-12 h-12 text-green-600" />
        </div>
        
        <h2 class="text-2xl font-bold text-gray-900 mb-2">注册成功!</h2>
        <p class="text-gray-500 mb-8 max-w-xs mx-auto">
          欢迎您 <span class="text-gray-900 font-semibold">{{ formData.username || '新朋友' }}</span> 加入椿天社！<br>
          准备好开启您的精彩旅程了吗？
        </p>

        <button
          @click="handleFinish"
          class="w-full py-3.5 px-4 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-600/20 transition-all flex items-center justify-center shadow-lg shadow-blue-600/30 hover:scale-[1.02] active:scale-[0.98]"
        >
          开始探索
          <ArrowRight class="w-5 h-5 ml-2" />
        </button>
      </div>
      

    </div>
  </AuthLayout>
</template>

<style scoped>
/* 隐藏浏览器默认的密码查看/清除按钮 */
input::-ms-reveal,
input::-ms-clear {
  display: none;
}
</style>
