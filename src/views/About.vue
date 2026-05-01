<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import Navigation from '@/components/Navigation.vue';
import SocialSidebar from '@/components/SocialSidebar.vue';
import Footer from '@/components/Footer.vue';
import ScrollFloatText from '@/components/animations/ScrollFloatText.vue';
import { Heart, Users, MapPin, ArrowDown } from 'lucide-vue-next';

const scrollY = ref(0);
const founderAvatar = ref('/founder-avatar.jpg');

const handleAvatarError = (event: Event) => {
  (event.target as HTMLImageElement).src =
    'https://images.unsplash.com/photo-1547425260-76bcadfb4f2c?w=160&h=160&fit=crop';
};

const handleScroll = () => {
  scrollY.value = window.scrollY;
};

onMounted(() => {
  window.addEventListener('scroll', handleScroll);
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
});
</script>

<template>
  <div class="bg-primary min-h-screen text-text-main overflow-x-hidden selection:bg-accent selection:text-primary">
    <Navigation>
      <template #logo>
        <router-link
          to="/"
          class="text-text-main font-bold text-4xl tracking-wide"
          style="font-family: 'PangMenZhengDao', serif;"
        >
          椿天社
        </router-link>
      </template>
    </Navigation>

    <SocialSidebar />

    <main>
      <div id="hero" class="relative flex h-[1200px] w-full flex-col items-center overflow-hidden pt-32 lg:pt-64">
        <div
          class="absolute top-0 left-0 z-0 h-full w-full bg-cover bg-center pointer-events-none"
          :style="{
            backgroundImage: `url('https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=2070&auto=format&fit=crop')`,
            transform: `translateY(${scrollY * 0.5}px)`,
          }"
        >
          <div class="absolute inset-0 bg-gradient-to-b from-transparent via-primary/30 to-primary"></div>
          <div class="absolute inset-0 bg-gradient-to-t from-primary via-transparent to-transparent opacity-80"></div>
        </div>

        <div class="relative z-10 container mx-auto flex max-w-5xl flex-col items-start px-4 lg:px-20">
          <div class="mb-8 flex items-center gap-4">
            <div class="h-[2px] w-[72px] bg-accent"></div>
            <span class="font-sans text-lg font-bold uppercase tracking-[6px] text-accent">关于我们</span>
          </div>

          <ScrollFloatText
            tag="h1"
            text="让旅行更温暖，更有连接"
            container-class="mb-8 max-w-4xl"
            text-class="font-serif text-5xl md:text-7xl lg:text-[88px] leading-[0.95] tracking-[0.02em] text-text-main"
            :stagger="0.045"
            :duration="0.8"
            :once="false"
          />

          <div class="mt-8 flex cursor-pointer items-center gap-4 font-bold text-text-main animate-bounce">
            <span>加入我们</span>
            <ArrowDown :size="20" />
          </div>
        </div>
      </div>

      <div class="relative z-20 -mt-32 space-y-28 bg-gradient-to-b from-transparent to-primary pb-32">
        <div class="container mx-auto max-w-6xl px-4 lg:px-20">
          <div class="grid grid-cols-1 gap-12 rounded-3xl border border-white/10 bg-white/5 p-10 lg:grid-cols-2">
            <div>
              <div class="mb-3 text-sm font-bold uppercase tracking-[6px] text-accent">我们的使命</div>
              <ScrollFloatText
                tag="h2"
                text="用社区的力量，连接每一次出发"
                container-class="mb-4"
                text-class="font-serif text-3xl md:text-4xl leading-snug text-text-main"
                :stagger="0.024"
                :duration="0.68"
                :once="false"
              />
              <p class="leading-7 text-white/80">
                我们希望通过真实、温暖、彼此互助的社区，让旅行变得更简单、更安全、更有意义。椿天社不仅是攻略集合地，更是人与人之间的连接器。
              </p>
            </div>

            <div>
              <div class="mb-3 text-sm font-bold uppercase tracking-[6px] text-accent">我们的愿景</div>
              <ScrollFloatText
                tag="h2"
                text="成为最值得信任的中文旅行社群"
                container-class="mb-4"
                text-class="font-serif text-3xl md:text-4xl leading-snug text-text-main"
                :stagger="0.024"
                :duration="0.68"
                :once="false"
              />
              <p class="leading-7 text-white/80">
                让每一次旅行都能遇见共鸣的同伴、获取真实的建议与灵感，并在归来后留下你的故事和影响力。
              </p>
            </div>
          </div>
        </div>

        <div class="container mx-auto max-w-6xl px-4 lg:px-20">
          <div class="mb-8">
            <div class="text-sm font-bold uppercase tracking-[6px] text-accent">价值观</div>
            <ScrollFloatText
              tag="h3"
              text="我们坚信的三件事"
              container-class="mt-2"
              text-class="font-serif text-2xl md:text-3xl text-text-main"
              :stagger="0.022"
              :duration="0.62"
              :once="false"
            />
          </div>

          <div class="grid grid-cols-1 gap-6 md:grid-cols-3">
            <div class="rounded-2xl border border-white/10 bg-white/5 p-6">
              <Heart class="mb-4 h-8 w-8 text-accent" />
              <div class="mb-2 text-xl font-semibold text-text-main">真实与善意</div>
              <p class="leading-7 text-white/70">
                信息真实，氛围友好。每一条分享都值得被尊重，每一次互动都充满善意。
              </p>
            </div>

            <div class="rounded-2xl border border-white/10 bg-white/5 p-6">
              <Users class="mb-4 h-8 w-8 text-accent" />
              <div class="mb-2 text-xl font-semibold text-text-main">连接与共创</div>
              <p class="leading-7 text-white/70">
                帮助你找到同路人，一起完成更远的目的地，共同建设更好的内容与工具。
              </p>
            </div>

            <div class="rounded-2xl border border-white/10 bg-white/5 p-6">
              <MapPin class="mb-4 h-8 w-8 text-accent" />
              <div class="mb-2 text-xl font-semibold text-text-main">探索与成长</div>
              <p class="leading-7 text-white/70">
                旅行不是逃离，而是回到生活本身。我们鼓励有节奏、有深度的探索。
              </p>
            </div>
          </div>
        </div>

        <div class="container mx-auto max-w-6xl px-4 lg:px-20">
          <div class="mb-8">
            <div class="text-sm font-bold uppercase tracking-[6px] text-accent">关于创始人</div>
            <ScrollFloatText
              tag="h3"
              text="“椿天社”是我的毕设项目"
              container-class="mt-2"
              text-class="font-serif text-2xl md:text-3xl text-text-main"
              :stagger="0.022"
              :duration="0.62"
              :once="false"
            />
            <p class="mt-2 leading-7 text-white/70">
              由 许博钧 发起与打造，你也可以叫我：S̶ᴜ̶ɴ̶s̶ᴛ̶ᴇ̶༣🥥。
            </p>
          </div>

          <div class="grid grid-cols-1 items-center gap-10 lg:grid-cols-2">
            <div class="space-y-4">
              <div class="text-xs font-bold uppercase tracking-[6px] text-accent">灵感历程</div>
              <p class="text-justify indent-[2em] leading-8 text-white/80">
                我的毕业设计选题“椿天社”，灵感来源于对当代旅游方式的观察与思考。传统的旅游平台往往侧重于“机票+酒店”的标准化交易，旅行者与目的地之间缺乏深度的情感连接。而“椿”字，取自古代对父亲的尊称（椿庭），也有“椿萱并茂”指代父母长寿安康之意，象征着一种根基、一种归属感。我希望打造的平台，不仅仅是提供出行服务，更是为了让用户在旅途中找到“家”的温暖和文化的归属感，所以取名为“椿天社”。
              </p>
            </div>

            <div class="flex justify-center lg:justify-end">
              <img
                :src="founderAvatar"
                @error="handleAvatarError"
                alt="许博钧头像"
                class="h-64 w-64 rounded-2xl object-cover shadow-xl ring-1 ring-black/10 md:h-80 md:w-80"
              />
            </div>
          </div>
        </div>

        <div class="container mx-auto max-w-6xl px-4 lg:px-20">
          <div class="flex flex-col items-start justify-between gap-6 rounded-3xl bg-accent p-10 text-primary md:flex-row md:items-center md:p-12">
            <div>
              <div class="text-xs font-bold uppercase tracking-[6px]">加入我们</div>
              <div class="mt-2 font-serif text-2xl md:text-3xl">和我们一起把旅行故事讲给世界听</div>
            </div>

            <router-link
              to="/register"
              class="rounded-full bg-primary px-6 py-3 font-bold text-accent transition-colors hover:bg-white hover:text-accent"
            >
              开始加入
            </router-link>
          </div>
        </div>
      </div>
    </main>

    <Footer />
  </div>
</template>
