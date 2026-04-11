<script setup lang="ts">
import { ElButton, ElCard, ElEmpty, ElIcon, ElSkeleton } from 'element-plus'
import { Link } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'
import { fetchPublicFriendLinks } from '../../features/friend-links/api'
import type { FriendLinkRecord } from '../../features/friend-links/types'
import FriendLinkExchangeModal from '../../components/FriendLinkExchangeModal.vue'

const friendLinks = ref<FriendLinkRecord[]>([])
const initialLoading = ref(true)
const refreshing = ref(false)
const showExchangeModal = ref(false)
const showSkeleton = ref(true)

async function fetchFriendLinks(options: { silent?: boolean } = {}) {
  const silent = options.silent ?? !initialLoading.value
  if (silent) {
    refreshing.value = true
  } else {
    initialLoading.value = true
  }
  try {
    friendLinks.value = await fetchPublicFriendLinks()
  } catch {
    friendLinks.value = []
  } finally {
    if (silent) {
      refreshing.value = false
    } else {
      initialLoading.value = false
    }
    showSkeleton.value = initialLoading.value && friendLinks.value.length === 0
  }
}

function openExchangeModal() {
  showExchangeModal.value = true
}

function onExchangeSuccess() {
  void fetchFriendLinks({ silent: true })
}

onMounted(() => {
  void fetchFriendLinks()
})
</script>

<template>
  <div class="links-page">
    <div class="links-container">
      <ElCard class="links-card">
        <template #header>
          <div class="links-header">
            <div class="header-title">
              <ElIcon><Link /></ElIcon>
              <span>友情链接</span>
            </div>
            <ElButton type="primary" size="small" @click="openExchangeModal">
              申请友链
            </ElButton>
          </div>
        </template>

        <ElSkeleton :loading="showSkeleton" animated>
          <div v-if="friendLinks.length > 0" v-loading="refreshing" class="links-grid">
            <a
              v-for="friendLink in friendLinks"
              :key="friendLink.id"
              :href="friendLink.url"
              target="_blank"
              class="link-item"
            >
              <div class="link-logo">
                <img v-if="friendLink.logo_url" :src="friendLink.logo_url" :alt="friendLink.name">
                <div v-else class="logo-placeholder">{{ friendLink.name.charAt(0) }}</div>
              </div>
              <div class="link-info">
                <div class="link-name">{{ friendLink.name }}</div>
                <div class="link-desc">{{ friendLink.description || '暂无描述' }}</div>
              </div>
            </a>
          </div>
          <ElEmpty v-else description="暂无友链，快来申请吧！" />
        </ElSkeleton>

        <div class="exchange-info">
          <h4>友链交换说明</h4>
          <ul>
            <!-- <li>网站内容健康，无违法违规信息</li>
            <li>网站可以正常访问，加载速度良好</li>
            <li>建议先在您的网站添加本站链接，可自动添加</li> -->
            <li>测试测试测试</li>
            <li>
              本站信息：
              <ul>
                <li>名称：Sakurakuguの小窝</li>
                <li>链接：https://www.sakurakugu.top</li>
                <li>描述：还没想好</li>
              </ul>
            </li>
          </ul>
        </div>
      </ElCard>
    </div>
  </div>

  <FriendLinkExchangeModal v-model="showExchangeModal" @success="onExchangeSuccess" />
</template>

<style scoped>
@import '../../styles/media.css';

.links-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px 16px;
}

.links-container {
  width: 100%;
}

.links-card {
  border-radius: 12px;
}

.links-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.links-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.link-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  background: #f9f9f9;
  text-decoration: none;
  color: inherit;
  transition: all 0.2s;
}

.link-item:hover {
  background: #f0f0f0;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.dark .link-item {
  background: var(--bg-hover);
}

.dark .link-item:hover {
  background: var(--bg-secondary);
}

.link-logo {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  background: #e0e0e0;
}

.link-logo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.logo-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
  color: #666;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.link-info {
  flex: 1;
  min-width: 0;
}

.link-name {
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 4px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dark .link-name {
  color: var(--text-primary);
}

.link-desc {
  font-size: 13px;
  color: #888;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dark .link-desc {
  color: var(--text-tertiary);
}

.exchange-info {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e0e0e0;
}

.dark .exchange-info {
  border-top-color: var(--border-color);
}

.exchange-info h4 {
  margin-bottom: 12px;
  color: #333;
}

.dark .exchange-info h4 {
  color: var(--text-primary);
}

.exchange-info ul {
  padding-left: 20px;
  color: #666;
  line-height: 1.8;
}

.exchange-info li {
  margin-bottom: 4px;
}

.dark .exchange-info ul {
  color: var(--text-secondary);
}

@media (--mobile-viewport) {
  .links-grid {
    grid-template-columns: 1fr;
  }
}
</style>
