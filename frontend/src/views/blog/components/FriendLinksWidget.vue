<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { ElButton, ElEmpty, ElSkeleton } from 'element-plus'
import { onMounted, ref } from 'vue'
import { fetchPublicFriendLinks } from '../../../features/friend-links/api'
import type { FriendLinkRecord } from '../../../features/friend-links/types'
import FriendLinkExchangeModal from '../../../components/FriendLinkExchangeModal.vue'

const friendLinks = ref<FriendLinkRecord[]>([])
const loading = ref(true)
const showExchangeModal = ref(false)

async function loadFriendLinks() {
  try {
    friendLinks.value = await fetchPublicFriendLinks()
  } catch {
    friendLinks.value = []
  } finally {
    loading.value = false
  }
}

function openExchangeModal() {
  showExchangeModal.value = true
}

function onExchangeSuccess() {
  void loadFriendLinks()
}

onMounted(() => {
  void loadFriendLinks()
})
</script>

<template>
  <div id="friend-links" class="friend-links-section">
    <div class="friend-links-card">
      <!-- 标题区 -->
      <div class="friend-links-header">
        <div class="header-title-wrap">
          <div class="header-icon">
            <Icon icon="material-symbols:group" />
          </div>
          <div class="header-title">友情链接</div>
        </div>
        <ElButton type="primary" text size="small" @click="openExchangeModal">
          申请友链
        </ElButton>
      </div>

      <!-- 友链列表 -->
      <div class="friend-links-body">
        <ElSkeleton :loading="loading" animated>
          <div v-if="friendLinks.length > 0" class="friends-grid">
            <a
              v-for="friendLink in friendLinks"
              :key="friendLink.id"
              :href="friendLink.url"
              target="_blank"
              rel="noopener noreferrer"
              class="friend-card group"
            >
              <div class="friend-card-bg" aria-hidden="true" />
              <div class="friend-avatar">
                <img v-if="friendLink.logo_url" :src="friendLink.logo_url" :alt="friendLink.name">
                <div v-else class="avatar-placeholder">{{ friendLink.name.charAt(0) }}</div>
              </div>
              <div class="friend-info">
                <div class="friend-title-row">
                  <div class="friend-name">{{ friendLink.name }}</div>
                  <Icon icon="material-symbols:arrow-outward-rounded" class="friend-arrow" />
                </div>
                <div class="friend-desc" :title="friendLink.description || '暂无描述'">
                  {{ friendLink.description || '暂无描述' }}
                </div>
              </div>
            </a>
          </div>
          <ElEmpty v-else description="暂无友链，快来申请吧！" />
        </ElSkeleton>
      </div>
    </div>

    <FriendLinkExchangeModal v-model="showExchangeModal" @success="onExchangeSuccess" />
  </div>
</template>

<style scoped>
.friend-links-section {
  width: 100%;
}

.friend-links-card {
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s, border-color 0.2s;
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
  padding: 1.5rem;
}

.dark .friend-links-card {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.friend-links-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.header-title-wrap {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-icon {
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  background: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 1.25rem;
}

.header-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.friend-links-body :deep(.el-empty) {
  padding: 2rem 0;
}

.friends-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 0.75rem;
}

.friend-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem;
  border-radius: 0.75rem;
  border: 1px solid var(--line-divider);
  text-decoration: none;
  overflow: hidden;
  transition: all 0.3s;
}

.friend-card:hover {
  border-color: var(--primary);
  background: var(--card-bg-transparent);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.friend-card-bg {
  position: absolute;
  inset: 0;
  background: var(--primary);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s;
}

.friend-card:hover .friend-card-bg {
  opacity: 0.05;
}

.friend-avatar {
  position: relative;
  width: 3.5rem;
  height: 3.5rem;
  flex-shrink: 0;
  border-radius: 0.75rem;
  overflow: hidden;
  background: #f4f4f5;
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: transform 0.3s;
}

.dark .friend-avatar {
  background: #27272a;
  border-color: rgba(255, 255, 255, 0.05);
}

.friend-card:hover .friend-avatar {
  transform: scale(1.05);
}

.friend-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.125rem;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.friend-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.125rem;
}

.friend-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.friend-name {
  font-weight: 700;
  font-size: 1rem;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 1rem;
  transition: color 0.3s;
}

.friend-card:hover .friend-name {
  color: var(--primary);
}

.friend-arrow {
  font-size: 1.125rem;
  color: var(--primary);
  opacity: 0;
  transform: translateX(-0.5rem);
  transition: all 0.3s;
  width: 1.125rem;
  height: 1.125rem;
  flex-shrink: 0;
}

.friend-card:hover .friend-arrow {
  opacity: 1;
  transform: translateX(0);
}

.friend-desc {
  font-size: 0.875rem;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.25rem;
}
</style>
