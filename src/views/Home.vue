<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import Navigation from '@/components/Navigation.vue';
import HeroSection from '@/components/HeroSection.vue';
import SocialSidebar from '@/components/SocialSidebar.vue';
import ScrollIndicator from '@/components/ScrollIndicator.vue';
import ContentSection from '@/components/ContentSection.vue';
import Footer from '@/components/Footer.vue';

const activeSection = ref(0);

const handleScroll = () => {
  const sections = ['hero', '01', '02', '03'];
  const scrollY = window.scrollY;
  const windowHeight = window.innerHeight;
  
  // Simple logic to determine active section based on scroll position
  // Adjust threshold as needed
  const index = sections.findIndex((id) => {
    const element = document.getElementById(id);
    if (!element) return false;
    const rect = element.getBoundingClientRect();
    return rect.top <= windowHeight / 2 && rect.bottom >= windowHeight / 2;
  });

  if (index !== -1) {
    activeSection.value = index;
  }
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
        <router-link to="/" class="text-text-main font-bold text-4xl tracking-wide" style="font-family: 'PangMenZhengDao', serif;">
          椿天社
        </router-link>
      </template>
    </Navigation>
    <SocialSidebar />
    <ScrollIndicator :active-section="activeSection" />

    <main>
      <div id="hero">
        <HeroSection />
      </div>

      <div class="relative z-20 -mt-32 space-y-32 pb-32 bg-gradient-to-b from-transparent to-primary">
        <ContentSection
          id="01"
          step="01"
          tag="开始"
          title="你是什么级别的徒步旅行者？"
          description="确定你是什么级别的徒步旅行者是规划未来徒步旅行的重要工具。本徒步等级指南将帮助你根据 All Trails 和 Modern Hiker 等各种网站设定的不同徒步评级来规划徒步旅行。你是什么类型的徒步旅行者——新手、中级、高级中级、专家还是背包客专家？"
          image-src="https://images.unsplash.com/photo-1551632811-561732d1e306?q=80&w=800&auto=format&fit=crop"
          image-alt="山脊上的徒步者"
        />

        <ContentSection
          id="02"
          step="02"
          tag="徒步必备"
          title="选择正确的徒步装备！"
          description="开始徒步旅行的好处是你真的不需要任何特殊的装备，你可能可以用你已经拥有的东西。让我们从衣服开始。徒步初学者常犯的一个错误是穿牛仔裤和普通衣服，如果出汗或弄湿，这些衣服会变重并引起摩擦。"
          image-src="https://images.unsplash.com/photo-1501555088652-021faa106b9b?q=80&w=800&auto=format&fit=crop"
          image-alt="徒步装备"
          :reverse="true"
        />

        <ContentSection
          id="03"
          step="03"
          tag="关键在于你去哪里"
          title="了解您的地图和时间安排"
          description="首先，打印出徒步指南和地图。如果下雨，把它们扔进自封袋里。阅读指南，研究地图，并对预期内容有一个很好的了解。我喜欢在徒步时知道我的下一个地标是什么。例如，我会阅读指南并知道，比如说，在一英里处，我在路口右转。"
          image-src="https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?q=80&w=800&auto=format&fit=crop"
          image-alt="指南针和地图"
        />
      </div>
    </main>

    <Footer />
  </div>
</template>
