<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { computed, onMounted, ref } from 'vue'
import { 获取博客统计, type BlogStats } from '@personal-system/domain/system'

// 站点开始日期，可配置
const SITE_START_DATE = '2026-03-26'

const statsData = ref<BlogStats | null>(null)

const runningDays = computed(() => {
  const start = new Date(SITE_START_DATE)
  const today = new Date()
  const diff = Math.ceil((today.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
  return Math.max(0, diff)
})

const lastUpdateDays = computed(() => {
  if (!statsData.value?.last_published_at) return null
  const last = new Date(statsData.value.last_published_at)
  const today = new Date()
  const diff = Math.floor((today.getTime() - last.getTime()) / (1000 * 60 * 60 * 24))
  return diff
})

const statItems = computed(() => {
  const data = statsData.value
  return [
    {
      icon: 'material-symbols:article-outline',
      label: '文章总数',
      value: data?.total_articles ?? 0,
    },
    {
      icon: 'material-symbols:folder-outline',
      label: '分类总数',
      value: data?.total_categories ?? 0,
    },
    {
      icon: 'material-symbols:label-outline',
      label: '标签总数',
      value: data?.total_tags ?? 0,
    },
    {
      icon: 'material-symbols:text-ad-outline-rounded',
      label: '总字数',
      value: (data?.total_words ?? 0).toLocaleString(),
    },
    {
      icon: 'material-symbols:calendar-clock-outline',
      label: '运行天数',
      value: runningDays.value,
      suffix: '天',
    },
    {
      icon: 'mingcute:heartbeat-line',
      label: '最后更新',
      value: lastUpdateDays.value === null ? '-' : lastUpdateDays.value === 0 ? '今天' : lastUpdateDays.value,
      suffix: lastUpdateDays.value === null || lastUpdateDays.value === 0 ? '' : '天前',
    },
  ]
})

onMounted(async () => {
  try {
    statsData.value = await 获取博客统计()
  } catch {
    statsData.value = null
  }
})
</script>

<template>
  <div class="widget-card">
    <div class="widget-header">
      <span>站点统计</span>
    </div>
    <div class="stats-list">
      <div
        v-for="item in statItems"
        :key="item.label"
        class="stat-row"
      >
        <div class="stat-left">
          <div class="stat-icon">
            <Icon :icon="item.icon" />
          </div>
          <span class="stat-label">{{ item.label }}</span>
        </div>
        <div class="stat-right">
          <span class="stat-value">{{ item.value }}</span>
          <span v-if="item.suffix" class="stat-suffix">{{ item.suffix }}</span>
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

.stats-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 6px 12px 16px;
}

.stat-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 8px 8px 16px;
  border-radius: 8px;
  transition: background 0.2s;
}

.stat-row:hover {
  background: rgba(0, 0, 0, 0.03);
}

.dark .stat-row:hover {
  background: rgba(255, 255, 255, 0.04);
}

.stat-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stat-icon {
  font-size: 1.25rem;
  color: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.stat-right {
  display: flex;
  align-items: center;
  gap: 2px;
}

.stat-value {
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-suffix {
  font-size: 0.8125rem;
  color: var(--text-tertiary);
  margin-left: 2px;
}
</style>
