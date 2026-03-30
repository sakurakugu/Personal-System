<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { BellFilled, ArrowLeft, ArrowDown } from '@element-plus/icons-vue'
import { ElButton, ElCard, ElEmpty, ElIcon, ElSkeleton, ElTag } from 'element-plus'
import { useRouter } from 'vue-router'
import OverflowMarquee from '../../components/OverflowMarquee.vue'
import { fetchPublicAnnouncements } from '../../features/system/api'
import type { AnnouncementRecord } from '../../features/system/types'

const router = useRouter()
const announcements = ref<AnnouncementRecord[]>([])
const collapsedAnnouncementIds = ref<Set<string>>(new Set())
const loading = ref(false)

async function fetchAnnouncements() {
  loading.value = true
  try {
    announcements.value = await fetchPublicAnnouncements(50)
  } catch {
    announcements.value = []
  } finally {
    // 默认收起：将所有公告ID加入collapsed集合
    collapsedAnnouncementIds.value = new Set(announcements.value.map(a => a.id))
    loading.value = false
  }
}

function goBack() {
  router.push('/blog')
}

function isAnnouncementCollapsed(id: string) {
  return collapsedAnnouncementIds.value.has(id)
}

function toggleAnnouncement(id: string) {
  const nextCollapsedIds = new Set(collapsedAnnouncementIds.value)

  if (nextCollapsedIds.has(id)) {
    nextCollapsedIds.delete(id)
  } else {
    nextCollapsedIds.add(id)
  }

  collapsedAnnouncementIds.value = nextCollapsedIds
}

onMounted(() => {
  void fetchAnnouncements()
})
</script>

<template>
  <div class="announcements-page">
    <div class="page-header">
      <ElButton text :icon="ArrowLeft" @click="goBack">
        返回
      </ElButton>
      <h1 class="page-title">
        <ElIcon><BellFilled /></ElIcon>
        全部通知
      </h1>
      <div class="placeholder" />
    </div>

    <ElSkeleton :loading="loading" animated :rows="3">
      <div v-if="announcements.length === 0 && !loading" class="empty-state">
        <ElEmpty description="暂无通知" />
      </div>

      <div class="announcement-list">
        <ElCard
          v-for="item in announcements"
          :key="item.id"
          class="announcement-item"
          :class="{ 'is-collapsed': isAnnouncementCollapsed(item.id) }"
          shadow="hover"
          role="button"
          tabindex="0"
          :aria-expanded="String(!isAnnouncementCollapsed(item.id))"
          @click="toggleAnnouncement(item.id)"
          @keydown.enter.prevent="toggleAnnouncement(item.id)"
          @keydown.space.prevent="toggleAnnouncement(item.id)"
        >
          <div class="announcement-title-wrap">
            <ElTag type="warning" size="small">公告</ElTag>
            <OverflowMarquee
              tag="h3"
              class="announcement-title"
              :text="item.title"
            />
          </div>
          <div class="announcement-meta">
            <span class="announcement-date">{{ new Date(item.created_at).toLocaleString() }}</span>
            <ElIcon
              class="announcement-toggle-icon"
              :class="{ 'is-collapsed': isAnnouncementCollapsed(item.id) }"
            >
              <ArrowDown />
            </ElIcon>
          </div>
          <p v-if="!isAnnouncementCollapsed(item.id)" class="announcement-content">{{ item.content }}</p>
        </ElCard>
      </div>
    </ElSkeleton>
  </div>
</template>

<style scoped>
.announcements-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 16px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.dark .page-title {
  color: var(--text-primary);
}

.placeholder {
  width: 60px;
}

.empty-state {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.announcement-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.announcement-item {
  border-radius: 12px;
  cursor: pointer;
}

.announcement-item:focus-visible {
  outline: 2px solid var(--el-color-warning);
  outline-offset: 2px;
}

.announcement-item :deep(.el-card__body) {
  padding: 16px 20px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  grid-template-areas:
    'title date'
    'content content';
  column-gap: 16px;
  row-gap: 12px;
  align-items: start;
}

.announcement-item.is-collapsed :deep(.el-card__body) {
  grid-template-areas: 'title date';
  row-gap: 0;
}

.announcement-title-wrap {
  grid-area: title;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.announcement-meta {
  grid-area: date;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.announcement-date {
  color: #999;
  font-size: 13px;
  line-height: 1.6;
  white-space: nowrap;
  text-align: right;
}

.dark .announcement-date {
  color: var(--text-tertiary);
}

.announcement-toggle-icon {
  flex-shrink: 0;
  color: #999;
  font-size: 14px;
  transition: transform 0.2s ease;
}

.announcement-toggle-icon.is-collapsed {
  transform: rotate(-90deg);
}

.dark .announcement-toggle-icon {
  color: var(--text-tertiary);
}

.announcement-title {
  display: block;
  min-width: 0;
  flex: 1;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
  line-height: 1.5;
}

.dark .announcement-title {
  color: #fbbf24;
}

.announcement-content {
  grid-area: content;
  min-width: 0;
  margin: 0;
  color: #666;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.dark .announcement-content {
  color: var(--text-secondary);
}

@media (max-width: 640px) {
  .announcement-item :deep(.el-card__body) {
    grid-template-columns: minmax(0, 1fr);
    grid-template-areas:
      'title'
      'date'
      'content';
    row-gap: 10px;
  }

  .announcement-item.is-collapsed :deep(.el-card__body) {
    grid-template-areas:
      'title'
      'date';
    row-gap: 8px;
  }

  .announcement-meta {
    justify-content: space-between;
  }

  .announcement-date {
    text-align: left;
  }

  .announcement-title-wrap {
    align-items: flex-start;
  }

  .announcement-date {
    white-space: normal;
  }
}
</style>
