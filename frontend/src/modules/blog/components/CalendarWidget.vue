<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchAllArticleMeta } from '../../../modules/articles/api'
import type { ArticleMetaRecord } from '../../../modules/articles/types'

const router = useRouter()

const articles = ref<ArticleMetaRecord[]>([])
const displayYear = ref(new Date().getFullYear())
const displayMonth = ref(new Date().getMonth())
type ViewType = 'day' | 'month' | 'year'
const currentView = ref<ViewType>('day')
const selectedDateKey = ref<string | null>(null)

const weekDays = ['日', '一', '二', '三', '四', '五', '六']
const monthNames = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']

const postDateMap = computed(() => {
  const map: Record<string, ArticleMetaRecord[]> = {}
  articles.value.forEach((post) => {
    if (!post.published_at) return
    const date = new Date(post.published_at)
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    if (!map[key]) map[key] = []
    map[key].push(post)
  })
  return map
})

const availableYears = computed(() => {
  const years = new Set<number>()
  articles.value.forEach((post) => {
    if (post.published_at) {
      years.add(new Date(post.published_at).getFullYear())
    }
  })
  return Array.from(years).sort((a, b) => b - a)
})

const headerText = computed(() => {
  if (currentView.value === 'day') {
    return `${displayYear.value}年${monthNames[displayMonth.value]}`
  }
  if (currentView.value === 'month') {
    return `${displayYear.value}年`
  }
  return '年份'
})

const isCurrentMonth = computed(() => {
  const now = new Date()
  return displayYear.value === now.getFullYear() && displayMonth.value === now.getMonth()
})

const calendarDays = computed(() => {
  const year = displayYear.value
  const month = displayMonth.value
  const firstDay = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const today = new Date()
  const isTodayMonth = year === today.getFullYear() && month === today.getMonth()

  const days: { day: number | null; dateKey: string; hasPost: boolean; count: number; isToday: boolean }[] = []

  for (let i = 0; i < firstDay; i++) {
    days.push({ day: null, dateKey: '', hasPost: false, count: 0, isToday: false })
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const dateKey = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const list = postDateMap.value[dateKey] || []
    days.push({
      day: d,
      dateKey,
      hasPost: list.length > 0,
      count: list.length,
      isToday: isTodayMonth && d === today.getDate(),
    })
  }

  return days
})

const currentMonthPosts = computed(() => {
  return articles.value.filter((post) => {
    if (!post.published_at) return false
    const date = new Date(post.published_at)
    return date.getFullYear() === displayYear.value && date.getMonth() === displayMonth.value
  })
})

const displayedPosts = computed(() => {
  if (selectedDateKey.value && postDateMap.value[selectedDateKey.value]) {
    return postDateMap.value[selectedDateKey.value]
  }
  return currentMonthPosts.value
})

function goArticle(slug: string) {
  void router.push(`/blog/${slug}`)
}

function changeMonth(delta: number) {
  if (currentView.value === 'day') {
    let newMonth = displayMonth.value + delta
    let newYear = displayYear.value
    if (newMonth > 11) {
      newMonth = 0
      newYear++
    } else if (newMonth < 0) {
      newMonth = 11
      newYear--
    }
    displayMonth.value = newMonth
    displayYear.value = newYear
  } else if (currentView.value === 'month') {
    displayYear.value += delta
  }
}

function resetToToday() {
  const now = new Date()
  displayYear.value = now.getFullYear()
  displayMonth.value = now.getMonth()
  currentView.value = 'day'
  selectedDateKey.value = null
}

function onHeaderClick() {
  if (currentView.value === 'day') {
    currentView.value = 'month'
  } else if (currentView.value === 'month') {
    currentView.value = 'year'
  }
}

function onMonthSelect(m: number) {
  displayMonth.value = m
  currentView.value = 'day'
}

function onYearSelect(y: number) {
  displayYear.value = y
  currentView.value = 'month'
}

function onDayClick(dateKey: string, hasPost: boolean) {
  if (!hasPost || !dateKey) return
  if (selectedDateKey.value === dateKey) {
    selectedDateKey.value = null
  } else {
    selectedDateKey.value = dateKey
  }
}

function formatPostDate(publishedAt: string) {
  const date = new Date(publishedAt)
  return `${date.getMonth() + 1}-${date.getDate()}`
}

const monthsWithPosts = computed(() => {
  const set = new Set<number>()
  articles.value.forEach((post) => {
    if (!post.published_at) return
    const date = new Date(post.published_at)
    if (date.getFullYear() === displayYear.value) {
      set.add(date.getMonth())
    }
  })
  return set
})

onMounted(async () => {
  try {
    articles.value = await fetchAllArticleMeta()
  } catch {
    articles.value = []
  }
})
</script>

<template>
  <div class="widget-card">
    <div class="widget-header">
      <span>日期归档</span>
    </div>
    <div class="calendar-body">
      <div class="calendar-nav">
        <button
          class="nav-btn"
          :style="{ visibility: currentView === 'year' ? 'hidden' : 'visible' }"
          @click="changeMonth(-1)"
        >
          <Icon icon="fa7-solid:chevron-left" />
        </button>
        <div class="nav-title" @click="onHeaderClick">
          {{ headerText }}
        </div>
        <div class="nav-actions">
          <button
            v-if="!(currentView === 'day' && isCurrentMonth)"
            class="nav-btn"
            @click="resetToToday"
          >
            <Icon icon="fa7-solid:arrow-rotate-left" />
          </button>
          <button
            class="nav-btn"
            :style="{ visibility: currentView === 'year' ? 'hidden' : 'visible' }"
            @click="changeMonth(1)"
          >
            <Icon icon="fa7-solid:chevron-right" />
          </button>
        </div>
      </div>

      <!-- Day View -->
      <div v-if="currentView === 'day'" class="day-view">
        <div class="weekdays">
          <div v-for="d in weekDays" :key="d" class="weekday-cell">
            {{ d }}
          </div>
        </div>
        <div class="days-grid">
          <div
            v-for="(cell, idx) in calendarDays"
            :key="idx"
            class="day-cell"
            :class="{
              'is-empty': cell.day === null,
              'has-post': cell.hasPost,
              'is-today': cell.isToday,
              'is-selected': selectedDateKey === cell.dateKey,
            }"
            @click="cell.day !== null && onDayClick(cell.dateKey, cell.hasPost)"
          >
            <template v-if="cell.day !== null">
              <span class="day-number">{{ cell.day }}</span>
              <span v-if="cell.hasPost" class="post-dot" />
              <span v-if="cell.hasPost && cell.count > 1" class="post-count">{{ cell.count }}</span>
            </template>
          </div>
        </div>
      </div>

      <!-- Month View -->
      <div v-else-if="currentView === 'month'" class="month-view">
        <div
          v-for="(name, idx) in monthNames"
          :key="idx"
          class="month-cell"
          :class="{
            'is-current': idx === displayMonth,
            'has-post': monthsWithPosts.has(idx),
          }"
          @click="onMonthSelect(idx)"
        >
          {{ name }}
          <span v-if="monthsWithPosts.has(idx)" class="post-dot" />
        </div>
      </div>

      <!-- Year View -->
      <div v-else-if="currentView === 'year'" class="year-view">
        <div
          v-for="year in availableYears"
          :key="year"
          class="year-cell"
          :class="{ 'is-current': year === displayYear }"
          @click="onYearSelect(year)"
        >
          {{ year }}
          <span class="post-dot" />
        </div>
      </div>

      <!-- Posts List -->
      <div v-if="currentView === 'day'" class="posts-section">
        <div v-if="displayedPosts.length > 0" class="posts-divider" />
        <div v-if="displayedPosts.length > 0" class="posts-list">
          <div
            v-for="post in displayedPosts"
            :key="post.id"
            class="post-item"
            @click="goArticle(post.slug)"
          >
            <span class="post-title">{{ post.title }}</span>
            <span v-if="post.published_at" class="post-date">{{ formatPostDate(post.published_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.widget-card {
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s, border-color 0.2s;
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
}

.dark .widget-card {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.widget-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  font-weight: 700;
  font-size: 1.125rem;
  color: var(--text-primary);
  position: relative;
  margin-left: 32px;
  margin-top: 16px;
  margin-bottom: 8px;
  border-bottom: none;
}

.widget-header::before {
  content: '';
  position: absolute;
  left: -16px;
  top: 5.5px;
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--primary);
}

.calendar-body {
  padding: 4px 12px 12px;
}

.calendar-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.nav-btn {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  font-size: 0.75rem;
}

.nav-btn:hover {
  background: var(--btn-plain-bg-hover, rgba(0, 0, 0, 0.05));
  color: var(--text-primary);
}

.nav-title {
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--text-primary);
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
}

.nav-title:hover {
  color: var(--primary);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: 6px;
}

.weekday-cell {
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-tertiary);
  font-weight: 500;
}

.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.day-cell {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  font-size: 0.8125rem;
  position: relative;
  cursor: default;
  color: var(--text-secondary);
  transition: background 0.2s, transform 0.15s;
}

.day-cell:not(.is-empty) {
  cursor: pointer;
}

.day-cell:not(.is-empty):hover {
  background: var(--btn-plain-bg-hover, rgba(0, 0, 0, 0.05));
}

.day-cell.has-post {
  color: var(--text-primary);
  font-weight: 600;
}

.day-cell.is-today {
  border: 2px solid var(--primary);
}

.day-cell.is-selected {
  background: var(--btn-regular-bg);
  color: var(--btn-content);
}

.day-number {
  position: relative;
  z-index: 1;
}

.post-dot {
  position: absolute;
  bottom: 3px;
  left: 50%;
  transform: translateX(-50%);
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--primary);
}

.post-count {
  position: absolute;
  top: 1px;
  right: 1px;
  font-size: 0.625rem;
  color: var(--primary);
  font-weight: 700;
  line-height: 1;
}

.month-view,
.year-view {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}

.month-cell,
.year-cell {
  padding: 10px 4px;
  text-align: center;
  font-size: 0.8125rem;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-secondary);
  position: relative;
  transition: background 0.2s, color 0.2s;
}

.month-cell:hover,
.year-cell:hover {
  background: var(--btn-plain-bg-hover, rgba(0, 0, 0, 0.05));
}

.month-cell.is-current,
.year-cell.is-current {
  color: var(--primary);
  font-weight: 700;
  background: var(--btn-plain-bg-hover, rgba(0, 0, 0, 0.05));
}

.posts-section {
  margin-top: 10px;
}

.posts-divider {
  height: 1px;
  background: var(--line-divider);
  margin-bottom: 8px;
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 160px;
  overflow-y: auto;
}

.post-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 8px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8125rem;
  color: var(--text-secondary);
  transition: background 0.2s, color 0.2s;
}

.post-item:hover {
  background: var(--btn-plain-bg-hover, rgba(0, 0, 0, 0.05));
  color: var(--primary);
}

.post-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 70%;
}

.post-date {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  white-space: nowrap;
}

.post-item:hover .post-date {
  color: var(--primary);
}
</style>
