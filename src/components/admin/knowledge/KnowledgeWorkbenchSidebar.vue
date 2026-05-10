<template>
  <aside class="atlas-sidebar" :class="{ 'is-open': open }">
    <div class="atlas-sidebar__mobile-head">
      <span>Knowledge Atlas</span>
      <button type="button" @click="$emit('close')">x</button>
    </div>

    <section class="atlas-account">
      <div class="atlas-avatar">KA</div>
      <div class="atlas-account__meta">
        <strong>Knowledge Atlas</strong>
        <p>Guest account</p>
      </div>
      <div class="atlas-account__actions">
        <button type="button">Login</button>
        <button type="button">Register</button>
      </div>
    </section>

    <div class="atlas-divider"></div>

    <div class="atlas-search">
      <input
        :value="searchQuery"
        type="text"
        placeholder="Search topics, papers, notes..."
        @input="$emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
      />
    </div>

    <div class="atlas-divider"></div>

    <section class="atlas-block">
      <div class="atlas-block__head">
        <span>REVISIT MOOD</span>
        <button type="button">Refresh</button>
      </div>

      <article class="atlas-mood-card">
        <div class="atlas-mood-card__face">
          <span class="atlas-mood-card__eye"></span>
          <span class="atlas-mood-card__mouth"></span>
          <span class="atlas-mood-card__eye"></span>
        </div>
        <h4>{{ moodTitle }}</h4>
        <p>{{ moodText }}</p>
      </article>
    </section>

    <div class="atlas-divider"></div>

    <section class="atlas-block atlas-block--nav">
      <div class="atlas-block__head">
        <span>NAVIGATION</span>
      </div>

      <ul class="atlas-nav">
        <li>
          <button class="atlas-nav__item" type="button" @click="$emit('selectCategory', '')">
            <span class="atlas-nav__diamond"></span>
            <strong>Tag / Libraries</strong>
          </button>
        </li>
        <li>
          <button class="atlas-nav__item" type="button">
            <span class="atlas-nav__dot atlas-nav__dot--solid"></span>
            <strong>Statistics</strong>
          </button>
        </li>
        <li>
          <button class="atlas-nav__item" type="button">
            <span class="atlas-nav__dot atlas-nav__dot--thin"></span>
            <strong>Recently Viewed</strong>
          </button>
        </li>
      </ul>
    </section>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { KnowledgeBaseItem, WorkspaceFacets, WorkspaceStats } from './types'

interface RecentItem {
  knowledgeBaseId: number
  datasetId: number
  name: string
  category: string
}

const props = defineProps<{
  open: boolean
  knowledgeBase: KnowledgeBaseItem | null
  facets: WorkspaceFacets
  stats: WorkspaceStats
  searchQuery: string
  activeCategory: string
  activeTag: string
  recentItems: RecentItem[]
}>()

defineEmits<{
  (e: 'close'): void
  (e: 'openAdmin'): void
  (e: 'update:searchQuery', value: string): void
  (e: 'selectCategory', value: string): void
  (e: 'selectTag', value: string): void
  (e: 'pickRecent', item: RecentItem): void
}>()

const moodTitle = computed(() => {
  if (props.stats.pending_count > 0) return 'Slow Return'
  if (props.knowledgeBase) return 'Quiet Focus'
  return 'Blank Space'
})

const moodText = computed(() => {
  if (props.stats.pending_count > 0) {
    return 'The feeling is a little distant right now, but a gentle pass will bring it back.'
  }
  if (props.knowledgeBase) {
    return 'The library is open. Keep refining the cards that matter most.'
  }
  return 'Create your first card to start building this library.'
})
</script>

<style scoped>
.atlas-sidebar {
  width: 100%;
  min-width: 0;
  height: 100%;
  padding: 18px 22px 22px;
  border-right: 1px solid rgba(28, 31, 44, 0.08);
  background: #fbfaf6;
  box-sizing: border-box;
  overflow-y: auto;
}

.atlas-sidebar__mobile-head {
  display: none;
}

.atlas-account {
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr) 72px;
  gap: 12px;
  align-items: start;
}

.atlas-avatar {
  width: 46px;
  height: 46px;
  border-radius: 999px;
  background: #252642;
  color: #fff8ef;
  display: grid;
  place-items: center;
  font-size: 18px;
  font-weight: 800;
}

.atlas-account__meta {
  min-width: 0;
  padding-top: 3px;
}

.atlas-account__meta strong {
  display: block;
  color: #151827;
  font-size: 16px;
  line-height: 1.2;
  font-weight: 800;
}

.atlas-account__meta p {
  margin: 5px 0 0;
  color: #8d857b;
  font-size: 12px;
}

.atlas-account__actions {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.atlas-account__actions button {
  width: 72px;
  height: 28px;
  border: 1px solid rgba(30, 32, 43, 0.12);
  border-radius: 999px;
  background: #fffdfa;
  color: #232638;
  font-size: 11px;
  cursor: pointer;
}

.atlas-divider {
  height: 1px;
  margin-top: 20px;
  background: rgba(30, 32, 43, 0.08);
}

.atlas-search {
  margin-top: 16px;
}

.atlas-search input {
  width: 100%;
  height: 40px;
  padding: 0 14px;
  border: 1px solid rgba(29, 29, 39, 0.12);
  border-radius: 10px;
  background: #fffdfa;
  color: #2f3138;
  font-size: 13px;
  outline: none;
  box-sizing: border-box;
}

.atlas-block {
  margin-top: 18px;
}

.atlas-block__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #9c9488;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.24em;
}

.atlas-block__head button {
  border: none;
  background: transparent;
  color: #9c9488;
  font-size: 10px;
  letter-spacing: 0.16em;
  cursor: pointer;
}

.atlas-mood-card {
  margin-top: 14px;
  padding: 14px 14px 16px;
  border-radius: 8px;
  background: #2d2a49;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
}

.atlas-mood-card__face {
  height: 68px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.07);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
}

.atlas-mood-card__eye {
  width: 11px;
  height: 11px;
  border-radius: 999px;
  border: 2px solid #fff0cb;
}

.atlas-mood-card__mouth {
  width: 16px;
  height: 2px;
  border-radius: 999px;
  background: #fff0cb;
}

.atlas-mood-card h4 {
  margin: 15px 0 7px;
  color: #fff8ef;
  font-size: 16px;
  font-weight: 800;
}

.atlas-mood-card p {
  margin: 0;
  color: rgba(255, 248, 239, 0.78);
  font-size: 12px;
  line-height: 1.55;
}

.atlas-nav {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin: 18px 0 0;
  padding: 0;
  list-style: none;
}

.atlas-nav__item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 24px;
  border: none;
  background: transparent;
  padding: 0;
  color: #202633;
  text-align: left;
  cursor: pointer;
}

.atlas-nav__item strong {
  font-size: 14px;
  font-weight: 700;
}

.atlas-nav__dot,
.atlas-nav__diamond {
  flex-shrink: 0;
}

.atlas-nav__diamond {
  width: 8px;
  height: 8px;
  border: 1px solid currentColor;
  transform: rotate(45deg);
}

.atlas-nav__dot {
  border-radius: 999px;
}

.atlas-nav__dot--solid {
  width: 6px;
  height: 6px;
  background: rgba(31, 33, 46, 0.92);
}

.atlas-nav__dot--thin {
  width: 6px;
  height: 6px;
  border: 1px solid rgba(31, 33, 46, 0.45);
}

@media (max-width: 1100px) {
  .atlas-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 50;
    width: min(320px, calc(100vw - 32px));
    transform: translateX(-105%);
    transition: transform 0.22s ease;
    box-shadow: 18px 0 40px rgba(15, 23, 42, 0.18);
  }

  .atlas-sidebar.is-open {
    transform: translateX(0);
  }

  .atlas-sidebar__mobile-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 18px;
  }

  .atlas-sidebar__mobile-head button {
    width: 30px;
    height: 30px;
    border: 1px solid rgba(30, 32, 43, 0.12);
    border-radius: 999px;
    background: #fffdfa;
  }
}
</style>
