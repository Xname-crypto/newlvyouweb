<script setup lang="ts">
import { computed, ref } from 'vue';
import type { Component } from 'vue';
import { Check } from 'lucide-vue-next';

interface InterestItem {
  id: string;
  label: string;
  icon: Component;
}

interface ChromaTheme {
  accent: string;
  glow: string;
  gradient: string;
}

const props = withDefaults(
  defineProps<{
    items: InterestItem[];
    selected: string[];
    maxSelected?: number;
  }>(),
  {
    maxSelected: 3,
  }
);

const emit = defineEmits<{
  toggle: [id: string];
}>();

const stageRef = ref<HTMLElement | null>(null);
const spotlightRef = ref<HTMLElement | null>(null);

const themeMap: Record<string, ChromaTheme> = {
  adventure: {
    accent: '#ff9551',
    glow: 'rgba(255, 149, 81, 0.24)',
    gradient:
      'linear-gradient(155deg, rgba(255, 191, 150, 0.8) 0%, rgba(255, 246, 239, 0.98) 52%, rgba(255, 255, 255, 0.96) 100%)',
  },
  photography: {
    accent: '#61b4ff',
    glow: 'rgba(97, 180, 255, 0.24)',
    gradient:
      'linear-gradient(155deg, rgba(179, 221, 255, 0.82) 0%, rgba(241, 248, 255, 0.98) 50%, rgba(255, 255, 255, 0.96) 100%)',
  },
  food: {
    accent: '#ffcf5a',
    glow: 'rgba(255, 207, 90, 0.24)',
    gradient:
      'linear-gradient(155deg, rgba(255, 226, 151, 0.82) 0%, rgba(255, 251, 237, 0.98) 50%, rgba(255, 255, 255, 0.96) 100%)',
  },
  nature: {
    accent: '#57d98c',
    glow: 'rgba(87, 217, 140, 0.22)',
    gradient:
      'linear-gradient(155deg, rgba(174, 238, 198, 0.8) 0%, rgba(243, 252, 247, 0.98) 50%, rgba(255, 255, 255, 0.96) 100%)',
  },
  city: {
    accent: '#a88cff',
    glow: 'rgba(168, 140, 255, 0.24)',
    gradient:
      'linear-gradient(155deg, rgba(212, 198, 255, 0.82) 0%, rgba(248, 244, 255, 0.98) 50%, rgba(255, 255, 255, 0.96) 100%)',
  },
  music: {
    accent: '#ff78b8',
    glow: 'rgba(255, 120, 184, 0.24)',
    gradient:
      'linear-gradient(155deg, rgba(255, 195, 222, 0.82) 0%, rgba(255, 243, 248, 0.98) 50%, rgba(255, 255, 255, 0.96) 100%)',
  },
};

const selectedSet = computed(() => new Set(props.selected));

const getTheme = (id: string): ChromaTheme =>
  themeMap[id] ?? {
    accent: '#61b4ff',
    glow: 'rgba(97, 180, 255, 0.4)',
    gradient:
      'linear-gradient(160deg, rgba(97, 180, 255, 0.38) 0%, rgba(8, 31, 56, 0.92) 44%, rgba(5, 7, 12, 1) 100%)',
  };

const isSelected = (id: string) => selectedSet.value.has(id);

const isLocked = (id: string) =>
  props.selected.length >= props.maxSelected && !isSelected(id);

const updateSpotlight = (event: PointerEvent) => {
  const stage = stageRef.value;
  const spotlight = spotlightRef.value;

  if (!stage || !spotlight) {
    return;
  }

  const rect = stage.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;

  spotlight.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
  spotlight.style.opacity = '1';
  stage.style.setProperty('--grid-x', `${x}px`);
  stage.style.setProperty('--grid-y', `${y}px`);
};

const hideSpotlight = () => {
  if (spotlightRef.value) {
    spotlightRef.value.style.opacity = '0';
  }
};

const updateCardGlow = (event: MouseEvent) => {
  const card = event.currentTarget as HTMLElement;
  const rect = card.getBoundingClientRect();
  card.style.setProperty('--pointer-x', `${event.clientX - rect.left}px`);
  card.style.setProperty('--pointer-y', `${event.clientY - rect.top}px`);
};

const resetCardGlow = (event: MouseEvent) => {
  const card = event.currentTarget as HTMLElement;
  card.style.setProperty('--pointer-x', '50%');
  card.style.setProperty('--pointer-y', '50%');
};

const handleCardClick = (id: string, event: MouseEvent) => {
  const card = event.currentTarget as HTMLElement;
  const icon = card.querySelector('.interest-chroma__icon-shell') as HTMLElement | null;
  const wave = card.querySelector('.interest-chroma__tap-wave') as HTMLElement | null;
  const willSelect = !isSelected(id);

  emit('toggle', id);

  card.animate(
    [
      { transform: 'translateY(0) scale(1)' },
      { transform: 'translateY(1px) scale(0.97)' },
      { transform: willSelect ? 'translateY(-6px) scale(1.035)' : 'translateY(-3px) scale(1.01)' },
      { transform: 'translateY(0) scale(1)' },
    ],
    {
      duration: 420,
      easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
    }
  );

  icon?.animate(
    [
      { transform: 'scale(1)', offset: 0 },
      { transform: 'scale(0.92)', offset: 0.22 },
      { transform: 'scale(1.12)', offset: 0.55 },
      { transform: 'scale(1)', offset: 1 },
    ],
    {
      duration: 420,
      easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
    }
  );

  wave?.animate(
    [
      { opacity: 0, transform: 'scale(0.4)' },
      { opacity: willSelect ? 0.5 : 0.32, transform: 'scale(1)' },
      { opacity: 0, transform: 'scale(1.85)' },
    ],
    {
      duration: 520,
      easing: 'cubic-bezier(0.16, 1, 0.3, 1)',
    }
  );
};

const cardStyle = (item: InterestItem, index: number) => {
  const theme = getTheme(item.id);

  return {
    '--card-accent': theme.accent,
    '--card-glow': theme.glow,
    '--card-gradient': theme.gradient,
    animationDelay: `${index * 120}ms`,
  } as Record<string, string>;
};
</script>

<template>
  <div class="interest-chroma">
    <div class="interest-chroma__toolbar">
      <span class="interest-chroma__eyebrow">CHROMA</span>
      <span class="interest-chroma__counter">{{ selected.length }}/{{ maxSelected }}</span>
    </div>

    <div
      ref="stageRef"
      class="interest-chroma__stage"
      @pointermove="updateSpotlight"
      @pointerleave="hideSpotlight"
    >
      <div ref="spotlightRef" class="interest-chroma__spotlight"></div>

      <div class="interest-chroma__grid">
        <button
          v-for="(item, index) in items"
          :key="item.id"
          type="button"
          class="interest-chroma__card"
          :class="{
            'is-selected': isSelected(item.id),
            'is-locked': isLocked(item.id),
          }"
          :style="cardStyle(item, index)"
          :aria-pressed="isSelected(item.id)"
          :disabled="isLocked(item.id)"
          @click="handleCardClick(item.id, $event)"
          @mousemove="updateCardGlow"
          @mouseleave="resetCardGlow"
        >
          <span class="interest-chroma__tap-wave"></span>
          <span class="interest-chroma__card-shine"></span>

          <span class="interest-chroma__card-content">
            <span class="interest-chroma__icon-shell">
              <component :is="item.icon" class="h-5 w-5" />
            </span>
            <span class="interest-chroma__label">{{ item.label }}</span>
          </span>

          <span class="interest-chroma__check">
            <Check class="h-3.5 w-3.5" />
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.interest-chroma {
  position: relative;
}

.interest-chroma__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0 0.25rem 0.35rem;
}

.interest-chroma__eyebrow {
  font-size: 0.64rem;
  font-weight: 700;
  letter-spacing: 0.36em;
  color: #94a3b8;
}

.interest-chroma__counter {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2.75rem;
  border-radius: 999px;
  border: 1px solid rgba(191, 219, 254, 0.7);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.92));
  padding: 0.34rem 0.72rem;
  font-size: 0.72rem;
  font-weight: 700;
  color: #475569;
  box-shadow: 0 10px 24px rgba(148, 163, 184, 0.12);
}

.interest-chroma__stage {
  --grid-x: 50%;
  --grid-y: 50%;
  position: relative;
  overflow: visible;
  padding: 0.15rem 0 0.3rem;
}

.interest-chroma__stage::before {
  content: '';
  position: absolute;
  inset: 0.15rem -0.35rem -0.2rem;
  z-index: 0;
  background:
    radial-gradient(circle at 14% 18%, rgba(255, 212, 186, 0.38), transparent 28%),
    radial-gradient(circle at 84% 88%, rgba(191, 219, 254, 0.34), transparent 30%),
    radial-gradient(circle at var(--grid-x) var(--grid-y), rgba(125, 211, 252, 0.12), transparent 36%);
  filter: blur(18px);
  opacity: 0.9;
  pointer-events: none;
}

.interest-chroma__stage::after {
  content: none;
}

.interest-chroma__spotlight {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 0;
  width: 240px;
  height: 240px;
  border-radius: 999px;
  pointer-events: none;
  opacity: 0;
  background:
    radial-gradient(circle, rgba(255, 255, 255, 0.6) 0%, rgba(255, 255, 255, 0.18) 26%, rgba(96, 165, 250, 0.12) 50%, rgba(251, 146, 60, 0.08) 64%, transparent 76%);
  filter: blur(20px);
  transition:
    transform 320ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 240ms ease;
  transform: translate(-50%, -50%);
}

.interest-chroma__grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.9rem;
}

.interest-chroma__card {
  --pointer-x: 50%;
  --pointer-y: 50%;
  position: relative;
  isolation: isolate;
  display: block;
  aspect-ratio: 1 / 1;
  overflow: hidden;
  border-radius: 1.35rem;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94) 0%, rgba(255, 255, 255, 0.82) 48%, rgba(248, 250, 252, 0.7) 100%),
    var(--card-gradient);
  background-size: 160% 160%;
  padding: 0.85rem 0.55rem 0.7rem;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.94),
    0 12px 26px rgba(148, 163, 184, 0.12),
    0 1px 0 rgba(255, 255, 255, 0.75);
  transition:
    transform 360ms cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 320ms ease,
    opacity 240ms ease,
    filter 240ms ease;
  animation: chroma-drift 11s ease-in-out infinite alternate;
}

.interest-chroma__card::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  background:
    radial-gradient(circle at var(--pointer-x) var(--pointer-y), rgba(255, 255, 255, 0.94), transparent 42%),
    radial-gradient(circle at 50% 100%, rgba(255, 255, 255, 0.42), transparent 60%);
  opacity: 0;
  transition: opacity 240ms ease;
}

.interest-chroma__card::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  background:
    radial-gradient(circle at top left, var(--card-glow) 0%, transparent 54%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.18) 0%, transparent 64%);
  opacity: 0.75;
  pointer-events: none;
}

.interest-chroma__card:hover,
.interest-chroma__card:focus-visible,
.interest-chroma__card.is-selected {
  transform: translateY(-5px) scale(1.025);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.96),
    0 18px 32px rgba(148, 163, 184, 0.16),
    0 0 22px var(--card-glow);
}

.interest-chroma__card:hover::before,
.interest-chroma__card:focus-visible::before,
.interest-chroma__card.is-selected::before {
  opacity: 1;
}

.interest-chroma__card.is-selected {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 255, 255, 0.9) 48%, rgba(248, 250, 252, 0.78) 100%),
    var(--card-gradient);
}

.interest-chroma__card.is-locked {
  opacity: 0.5;
  filter: saturate(0.74) grayscale(0.08);
  cursor: not-allowed;
}

.interest-chroma__tap-wave,
.interest-chroma__card-shine {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
}

.interest-chroma__tap-wave {
  z-index: 1;
  opacity: 0;
  background:
    radial-gradient(circle at var(--pointer-x) var(--pointer-y), rgba(255, 255, 255, 0.95) 0%, var(--card-glow) 20%, transparent 52%);
  transform: scale(0.4);
}

.interest-chroma__card-shine {
  z-index: 1;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.54), transparent 42%);
  opacity: 0.44;
}

.interest-chroma__card-content {
  position: relative;
  z-index: 2;
  display: flex;
  height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.7rem;
}

.interest-chroma__icon-shell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  border-radius: 999px;
  color: var(--card-accent);
  background:
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 1) 0%, rgba(255, 255, 255, 0.94) 44%, rgba(255, 255, 255, 0.86) 100%),
    radial-gradient(circle at 72% 76%, var(--card-glow) 0%, transparent 72%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.98),
    0 10px 18px rgba(148, 163, 184, 0.12),
    0 0 18px var(--card-glow);
}

.interest-chroma__label {
  font-size: 0.8rem;
  font-weight: 700;
  line-height: 1.1;
  color: #334155;
  letter-spacing: 0.08em;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.6);
}

.interest-chroma__card.is-selected .interest-chroma__label {
  color: #0f172a;
}

.interest-chroma__check {
  position: absolute;
  top: 0.55rem;
  right: 0.55rem;
  z-index: 3;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.55rem;
  height: 1.55rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  color: #2563eb;
  backdrop-filter: blur(8px);
  box-shadow: 0 8px 16px rgba(148, 163, 184, 0.14);
  opacity: 0;
  transform: scale(0.72);
  transition:
    opacity 220ms ease,
    transform 280ms cubic-bezier(0.22, 1, 0.36, 1);
}

.interest-chroma__card.is-selected .interest-chroma__check {
  opacity: 1;
  transform: scale(1);
}

@keyframes chroma-drift {
  0% {
    background-position: 0% 12%;
  }

  100% {
    background-position: 100% 88%;
  }
}

@media (max-width: 420px) {
  .interest-chroma__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
