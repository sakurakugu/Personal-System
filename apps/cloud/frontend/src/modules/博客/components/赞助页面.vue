<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { UniversalAvatar } from '@personal-system/ui'
import { ElCard, ElEmpty } from 'element-plus'
import { computed } from 'vue'
import { sponsorConfig } from '../constants/sponsorConfig'

const title = computed(() => sponsorConfig.title || '赞助支持')
const description = computed(() => sponsorConfig.description || '如果我的文章对你有帮助，欢迎赞助支持！')
const enabledMethods = computed(() => sponsorConfig.methods.filter((m) => m.enabled))
const showSponsorsList = computed(() => sponsorConfig.showSponsorsList)
const sponsors = computed(() => sponsorConfig.sponsors || [])
</script>

<template>
  <div class="sponsor-view">
    <!-- 赞助方式 -->
    <ElCard class="sponsor-card" :body-style="{ padding: '24px' }">
      <div class="sponsor-header">
        <div class="sponsor-icon-box">
          <Icon icon="material-symbols:favorite" class="sponsor-icon" />
        </div>
        <h1 class="sponsor-title">{{ title }}</h1>
      </div>

      <p v-if="description" class="sponsor-desc">{{ description }}</p>

      <div v-if="sponsorConfig.usage" class="usage-info-box">
        <div class="usage-info-inner">
          <Icon icon="material-symbols:info-outline" class="usage-info-icon" />
          <p class="usage-info-text">{{ sponsorConfig.usage }}</p>
        </div>
      </div>

      <div class="methods-grid">
        <div v-for="method in enabledMethods" :key="method.name" class="method-item">
          <div class="method-header">
            <Icon v-if="method.icon" :icon="method.icon" class="method-icon" />
            <h3 class="method-name">{{ method.name }}</h3>
          </div>

          <p v-if="method.description" class="method-desc">{{ method.description }}</p>

          <div v-if="method.qrCode" class="method-qr-wrapper">
            <img :src="method.qrCode" :alt="`${method.name} 扫码赞助`" class="method-qr" loading="lazy">
          </div>

          <a
            v-if="method.link"
            :href="method.link"
            target="_blank"
            rel="noopener noreferrer"
            class="method-link"
          >
            <span>前往赞助</span>
            <Icon icon="material-symbols:open-in-new" class="method-link-icon" />
          </a>
        </div>
      </div>
    </ElCard>

    <!-- 赞助者列表 -->
    <ElCard v-if="showSponsorsList" class="sponsor-card" :body-style="{ padding: '24px' }">
      <div class="sponsor-list-header">
        <div class="sponsor-list-title-wrap">
          <div class="sponsor-icon-box small">
            <Icon icon="material-symbols:emoji-people-rounded" class="sponsor-icon" />
          </div>
          <h2 class="sponsor-list-title">赞助者列表</h2>
        </div>
        <span v-if="sponsors.length > 0" class="sponsor-count">{{ sponsors.length }}</span>
      </div>

      <div v-if="sponsors.length > 0" class="sponsor-grid">
        <div v-for="sponsor in sponsors" :key="sponsor.name + (sponsor.date || '')" class="sponsor-item">
          <UniversalAvatar
            :text="sponsor.name.charAt(0)"
            :size="36"
            :alt="`${sponsor.name} 的头像`"
            class="sponsor-avatar"
            background="rgba(var(--el-color-primary-rgb), 0.1)"
            color="var(--el-color-primary)"
            font-size="14px"
          />
          <div class="sponsor-info">
            <div class="sponsor-info-top">
              <span class="sponsor-name">{{ sponsor.name }}</span>
              <span v-if="sponsor.amount" class="sponsor-amount">{{ sponsor.amount }}</span>
            </div>
            <span v-if="sponsor.date" class="sponsor-date">{{ new Date(sponsor.date).toLocaleDateString() }}</span>
          </div>
        </div>
      </div>

      <ElEmpty v-else description="还没有人赞助，来做第一位支持者吧！" />
    </ElCard>
  </div>
</template>

<style scoped>
.sponsor-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sponsor-card {
  border-radius: var(--radius-large);
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  background-color: rgba(255, 255, 255, var(--overlay-card-opacity)) !important;
}

.dark .sponsor-card {
  border-color: rgba(148, 163, 184, 0.16);
  background-color: rgba(15, 23, 42, var(--overlay-card-opacity)) !important;
}

.sponsor-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.sponsor-icon-box {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--el-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.dark .sponsor-icon-box {
  color: rgba(0, 0, 0, 0.7);
}

.sponsor-icon-box.small {
  background: rgba(var(--el-color-primary-rgb), 0.1);
  color: var(--el-color-primary);
}

.dark .sponsor-icon-box.small {
  color: var(--el-color-primary-light-5);
}

.sponsor-icon {
  font-size: 1.25rem;
}

.sponsor-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
}

.sponsor-desc {
  font-size: 0.9375rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 16px;
}

.usage-info-box {
  margin-bottom: 24px;
  padding: 16px;
  border-radius: 10px;
  background: rgba(var(--el-color-primary-rgb), 0.08);
  border: 1px solid rgba(var(--el-color-primary-rgb), 0.3);
  backdrop-filter: blur(4px);
}

.dark .usage-info-box {
  background: var(--btn-regular-bg);
  border: none;
}

.usage-info-inner {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.usage-info-icon {
  font-size: 1.125rem;
  color: var(--el-color-primary);
  margin-top: 2px;
  flex-shrink: 0;
}

.usage-info-text {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.methods-grid {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 16px;
}

@media (min-width: 640px) {
  .methods-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.method-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  border-radius: var(--radius-large);
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(0, 0, 0, 0.06);
  transition: border-color 0.2s;
}

.dark .method-item {
  background: rgba(15, 23, 42, 0.4);
  border-color: rgba(148, 163, 184, 0.1);
}

.method-item:hover {
  border-color: var(--el-color-primary);
}

.method-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.method-icon {
  font-size: 1.5rem;
  color: var(--text-primary);
}

.method-name {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.method-desc {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  text-align: center;
  margin: 0 0 16px;
}

.method-qr-wrapper {
  position: relative;
  width: 100%;
  max-width: 180px;
  aspect-ratio: 1;
  background: white;
  border-radius: 10px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  margin-bottom: 16px;
}

.method-qr {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.method-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--el-color-primary);
  color: white;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  text-decoration: none;
  transition: opacity 0.2s, transform 0.15s;
}

.method-link:hover {
  opacity: 0.9;
}

.method-link:active {
  transform: scale(0.97);
}

.method-link-icon {
  font-size: 0.875rem;
}

.sponsor-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.sponsor-list-title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sponsor-list-title {
  font-size: 1.125rem;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
}

.sponsor-count {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.sponsor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
}

.sponsor-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid var(--line-divider);
  transition: border-color 0.2s;
}

.sponsor-item:hover {
  border-color: var(--el-color-primary);
}

.sponsor-avatar {
  flex-shrink: 0;
}

.sponsor-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sponsor-info-top {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sponsor-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sponsor-amount {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.sponsor-date {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}
</style>
