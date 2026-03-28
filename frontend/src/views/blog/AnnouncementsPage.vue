<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { BellFilled, ArrowLeft } from '@element-plus/icons-vue'
import { ElButton, ElCard, ElEmpty, ElIcon, ElSkeleton, ElTag } from 'element-plus'
import { useRouter } from 'vue-router'
import { fetchPublicAnnouncements } from '../../features/system/api'
import type { AnnouncementRecord } from '../../features/system/types'

const router = useRouter()
const announcements = ref<AnnouncementRecord[]>([])
const loading = ref(false)

async function fetchAnnouncements() {
  loading.value = true
  try {
    announcements.value = await fetchPublicAnnouncements(50)
  } catch {
    announcements.value = []
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/blog')
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
          shadow="hover"
        >
          <div class="announcement-header">
            <ElTag type="warning" size="small">公告</ElTag>
            <span class="announcement-date">{{ new Date(item.created_at).toLocaleString() }}</span>
          </div>
          <h3 class="announcement-title">{{ item.title }}</h3>
          <p class="announcement-content">{{ item.content }}</p>
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
}

.announcement-item :deep(.el-card__body) {
  padding: 16px 20px;
}

.announcement-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.announcement-date {
  color: #999;
  font-size: 13px;
}

.dark .announcement-date {
  color: var(--text-tertiary);
}

.announcement-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
  line-height: 1.5;
}

.dark .announcement-title {
  color: #fbbf24;
}

.announcement-content {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.dark .announcement-content {
  color: var(--text-secondary);
}
</style>
