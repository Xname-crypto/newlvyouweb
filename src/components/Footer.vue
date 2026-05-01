<script setup lang="ts">
withDefaults(defineProps<{ variant?: 'dark' | 'light' | 'white' }>(), {
  variant: 'dark',
})

const blogLinks = ['关于椿天社', '贡献者与作者', '为我们写作', '联系我们', '隐私政策']
const mntnLinks = ['团队', '工作', '新闻']
</script>

<template>
  <footer
    class="w-full px-4 pb-32 pt-24 lg:px-20"
    :class="
      variant === 'light'
        ? 'border-t border-[#d9e3d4] bg-[#e8efe5]'
        : variant === 'white'
          ? 'border-t border-[#edf0f3] bg-white'
          : 'border-t border-white/10 bg-primary'
    "
  >
    <div class="container mx-auto grid grid-cols-1 gap-16 md:grid-cols-2 lg:grid-cols-5">
      <div class="lg:col-span-3 flex h-full flex-col justify-between space-y-8">
        <div>
          <div
            class="mb-6 text-3xl font-bold tracking-wide"
            style="font-family: 'PangMenZhengDao', serif;"
            :class="
              variant === 'white'
                ? 'text-[#243251]'
                : variant === 'light'
                  ? 'text-[#213126]'
                  : 'text-text-main'
            "
          >
            椿天社
          </div>
          <p
            class="max-w-xs text-lg font-bold leading-relaxed"
            :class="
              variant === 'white'
                ? 'text-[#4b5563]'
                : variant === 'light'
                  ? 'text-[#2e3f34]'
                  : 'text-text-main'
            "
          >
            走出去，发现你的下一处斜坡、山脉和目的地。
          </p>
        </div>
        <div
          class="font-medium"
          :class="
            variant === 'white'
              ? 'text-[#6b7280]'
              : variant === 'light'
                ? 'text-[#708070]'
                : 'text-white/50'
          "
        >
          项目作者 许博钧 | © 2026 椿天社 | 条款与隐私
        </div>
      </div>

      <div class="lg:col-span-1">
        <h3 class="mb-6 text-2xl font-bold" :class="variant === 'white' ? 'text-[#243251]' : 'text-accent'">
          博客上的更多信息
        </h3>
        <ul class="space-y-4">
          <li v-for="link in blogLinks" :key="link">
            <a
              href="#"
              class="font-medium transition-colors hover:text-accent"
              :class="
                variant === 'white'
                  ? 'text-[#4b5563]'
                  : variant === 'light'
                    ? 'text-[#2e3f34]'
                    : 'text-text-main'
              "
            >
              {{ link }}
            </a>
          </li>
        </ul>
      </div>

      <div class="lg:col-span-1">
        <h3 class="mb-6 text-2xl font-bold" :class="variant === 'white' ? 'text-[#243251]' : 'text-accent'">
          关于椿天社的更多信息
        </h3>
        <ul class="space-y-4">
          <li v-for="link in mntnLinks" :key="link">
            <a
              href="#"
              class="font-medium transition-colors hover:text-accent"
              :class="
                variant === 'white'
                  ? 'text-[#4b5563]'
                  : variant === 'light'
                    ? 'text-[#2e3f34]'
                    : 'text-text-main'
              "
            >
              {{ link }}
            </a>
          </li>
        </ul>
      </div>
    </div>
  </footer>
</template>
