<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { BlogTwikooPanel } from '@personal-system/module-blog/widgets'
import { ElEmpty, ElMessage, ElSkeleton } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { 获取公开友链 } from '../../../modules/友链/api'
import type { FriendLinkRecord } from '../../../modules/友链/types'
import { 使用设置存储 } from '../../../shared/stores/settings'

const friendLinks = ref<FriendLinkRecord[]>([])
const loading = ref(true)
const settings = 使用设置存储()

const selectedCategory = ref<string>('all')

const allCategories = computed(() => {
  const cats = new Set<string>()
  for (const link of friendLinks.value) {
    if (link.category) cats.add(link.category)
  }
  return [...cats].sort((a, b) => a.localeCompare(b, 'zh-CN'))
})

const filteredLinks = computed(() => {
  if (selectedCategory.value === 'all') return friendLinks.value
  return friendLinks.value.filter(link => link.category === selectedCategory.value)
})

async function loadFriendLinks() {
  try {
    friendLinks.value = await 获取公开友链()
  } catch {
    friendLinks.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadFriendLinks()
})

const site = {
  name: 'Sakurakuguの小窝',
  desc: '个人网站',
  url: 'https://www.sakurakugu.top',
  avatar: 'https://www.sakurakugu.top/头像.avif',
  email: 'sakurakugu@qq.com',
}

const notes = [
  { title: '互换原则', content: '希望能互相添加对方的友链即可，如果没这功能就算了' },
  { title: '链接维护', content: '如果网站长期无法访问，可能会被移除（自动的）' }, // TODO: 后端添加自动检测功能
  { title: '站点要求', content: '能够正常访问，别搞反动/暴力等违法违规内容即可' },
  { title: '其他注释', content: '这四个还有上面的都是占位的好看的内容，不用管' },
]

const 可以通过评论区申请 = computed(() => settings.commentVisibility !== 'hidden')
const 申请方式标题 = computed(() => {
  if (settings.commentVisibility === 'enabled') {
    return '评论区留言或发送申请邮件至：'
  }
  return '发送申请邮件至：'
})

const 第三步说明 = computed(() => {
  if (settings.commentVisibility === 'enabled') {
    return '不一定有时间看评论区，也可以直接发邮件'
  }
  return '发送后等待即可，我看到邮件后会尽快处理'
})

const copiedKey = ref<string | null>(null)

async function copyText(text: string, key?: string) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.left = '-9999px'
      textarea.style.top = '0'
      document.body.appendChild(textarea)
      textarea.focus()
      textarea.select()
      const successful = document.execCommand('copy')
      document.body.removeChild(textarea)
      if (!successful) throw new Error('execCommand copy failed')
    }
    if (key) {
      copiedKey.value = key
      setTimeout(() => { copiedKey.value = null }, 1500)
    }
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}
</script>

<template>
  <div id="friend-links" class="friend-links-section">
    <div class="friend-links-card">
      <!-- 标题区 -->
      <div class="header-wrap">
        <div class="header-row">
          <div class="header-icon">
            <Icon icon="material-symbols:group" />
          </div>
          <div class="header-title">
            友情链接
          </div>
        </div>
        <p class="header-desc">
          这里是我的朋友们，欢迎互相访问交流
        </p>
      </div>

      <!-- 友链列表 -->
      <div class="friend-links-body">
        <ElSkeleton :loading="loading" animated>
          <div v-if="friendLinks.length > 0">
            <!-- 分类筛选 -->
            <div class="category-filter">
              <button
                :class="['filter-btn', { active: selectedCategory === 'all' }]"
                @click="selectedCategory = 'all'"
              >
                全部
              </button>
              <button
                v-for="cat in allCategories"
                :key="cat"
                :class="['filter-btn', { active: selectedCategory === cat }]"
                @click="selectedCategory = cat"
              >
                {{ cat }}
              </button>
            </div>

            <div v-if="filteredLinks.length > 0" class="friends-grid">
              <a
                v-for="friendLink in filteredLinks"
                :key="friendLink.id"
                :href="friendLink.url"
                target="_blank"
                rel="noopener noreferrer"
                class="friend-card group"
              >
                <div class="friend-card-bg" aria-hidden="true" />
                <div class="friend-avatar">
                  <img
                    v-if="friendLink.logo_url"
                    :src="friendLink.logo_url"
                    :alt="friendLink.name"
                    loading="lazy"
                    decoding="async"
                  >
                  <div v-else class="avatar-placeholder">
                    {{ friendLink.name.charAt(0) }}
                  </div>
                </div>
                <div class="friend-info">
                  <div class="friend-title-row">
                    <div class="friend-name">
                      {{ friendLink.name }}
                    </div>
                    <Icon icon="material-symbols:arrow-outward-rounded" class="friend-arrow" />
                  </div>
                  <div class="friend-desc" :title="friendLink.description || '暂无描述'">
                    {{ friendLink.description || '暂无描述' }}
                  </div>
                  <div v-if="friendLink.category" class="friend-tags">
                    <span class="friend-tag">{{ friendLink.category }}</span>
                  </div>
                </div>
              </a>
            </div>
            <ElEmpty v-else description="暂无友链" />
          </div>
          <ElEmpty v-else description="暂无友链" />
        </ElSkeleton>
      </div>
    </div>

    <!-- 底部内容 -->
    <div class="bottom-card friend-links-card">
      <div class="info-grid">
        <!-- 左栏：本站信息 -->
        <div class="info-panel">
          <div class="panel-inner">
            <div class="site-header">
              <div class="avatar-wrap">
                <div class="site-avatar">
                  <img :src="site.avatar" :alt="site.name" loading="lazy" decoding="async">
                </div>
                <div class="verify-badge">
                  <svg class="verify-icon" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                  </svg>
                </div>
              </div>
              <div>
                <h3 class="site-name">{{ site.name }}</h3>
                <p class="site-desc">{{ site.desc }}</p>
              </div>
            </div>

            <div class="copy-list">
              <div
                v-for="item in [
                  { label: '站点名称', value: site.name },
                  { label: '站点描述', value: site.desc },
                  { label: '站点链接', value: site.url },
                  { label: '头像链接', value: site.avatar },
                ]"
                :key="item.label"
                class="copy-row"
              >
                <div class="min-w-0">
                  <p class="copy-label">{{ item.label }}</p>
                  <p class="copy-value">{{ item.value }}</p>
                </div>
                <button class="copy-btn" @click="copyText(item.value, item.label)">
                  <svg :class="['copy-icon', { hidden: copiedKey === item.label }]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <svg :class="['copy-icon', 'copy-success', { hidden: copiedKey !== item.label }]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 右栏：申请友链 -->
        <div class="info-panel">
          <div class="panel-inner">
            <h3 class="panel-title">
              <span class="title-icon">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                </svg>
              </span>
              申请友链
            </h3>
            <div class="steps">
              <div class="step">
                <div class="step-left">
                  <div class="step-number">1</div>
                  <div class="step-line" />
                </div>
                <div class="step-content pb-8">
                  <p class="step-title">添加本站友链</p>
                  <p class="step-text">希望您的网站友链页面添加本站信息，如果不行就算了，可直接复制左侧各字段</p>
                </div>
              </div>
              <div class="step">
                <div class="step-left">
                  <div class="step-number">2</div>
                  <div class="step-line" />
                </div>
                <div class="step-content pb-8">
                  <p class="step-title">
                    {{ 申请方式标题 }}<code class="inline-code">{{ site.email }}</code>
                  </p>
                  <p class="step-text" style="margin-bottom: 0.25rem;">
                    把以下内容复制修改后到{{ 可以通过评论区申请 ? '评论区或邮件' : '邮件' }}中发送
                  </p>
                  <div class="template-box">
                    <button class="template-copy-btn" @click="copyText('站点名称：您的站点名称\n站点描述：您的站点描述\n站点链接：您的站点链接\n头像链接：您的站点头像', 'template')">
                      <svg :class="['copy-icon', { hidden: copiedKey === 'template' }]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      <svg :class="['copy-icon', 'copy-success', { hidden: copiedKey !== 'template' }]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                    </button>
                    <pre class="template-pre">站点名称：您的站点名称
站点描述：您的站点描述
站点链接：您的站点链接
头像链接：您的站点头像</pre>
                  </div>
                </div>
              </div>
              <div class="step">
                <div class="step-left">
                  <div class="step-number">3</div>
                </div>
                <div class="step-content">
                  <p class="step-title">等待即可</p>
                  <p class="step-text">{{ 第三步说明 }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部：注意事项 -->
      <div class="info-panel" style="margin-top: 1rem;">
        <div class="panel-inner">
          <h3 class="panel-title">
            <svg class="notes-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            注意事项
          </h3>
          <div class="notes-list">
            <div v-for="note in notes" :key="note.title" class="note-item">
              <span class="note-dot" />
              <p>
                <strong class="note-strong">{{ note.title }}</strong>：{{ note.content }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <BlogTwikooPanel
      class="friend-links-comment-panel"
      path="/friends"
      title="友链评论区"
      empty-description="友链评论区尚未配置 Twikoo 服务地址"
      :hide-admin-entry="true"
      :visibility="settings.commentVisibility"
    />
  </div>
</template>

<style scoped>
.friend-links-section {
  width: 100%;
}

.bottom-card {
  margin-top: 1rem;
}

.friend-links-comment-panel {
  margin-top: 1rem;
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

.header-wrap {
  margin-bottom: 1rem;
}

.header-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
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
  font-size: 1.5rem;
}

.header-title {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--text-primary);
}

.header-desc {
  font-size: 1rem;
  color: var(--text-secondary);
  line-height: 1.625;
  margin-bottom: 1rem;
}

.friend-links-body :deep(.el-empty) {
  padding: 2rem 0;
}

.category-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.filter-btn {
  padding: 0.375rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  background: var(--btn-regular-bg);
  color: var(--btn-content);
  border: none;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
}

.filter-btn:hover {
  background: var(--btn-regular-bg-hover);
}

.filter-btn.active {
  background: var(--primary);
  color: #fff;
}

.filter-btn.active:hover {
  background: var(--primary);
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
  width: 4rem;
  height: 4rem;
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

.friend-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.25rem;
}

.friend-tag {
  font-size: 0.65rem;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  background: rgba(0, 0, 0, 0.05);
  color: var(--text-tertiary);
}

.dark .friend-tag {
  background: rgba(255, 255, 255, 0.05);
}

/* 底部内容 */
.info-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 992px) {
  .info-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.info-panel {
  border-radius: 1rem;
  border: 1px solid var(--line-divider);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.panel-inner {
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.site-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.avatar-wrap {
  position: relative;
  flex-shrink: 0;
}

.site-avatar {
  width: 4rem;
  height: 4rem;
  border-radius: 0.75rem;
  overflow: hidden;
  box-shadow: 0 0 0 2px rgba(var(--el-color-primary-rgb), 0.2);
}

.site-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.verify-badge {
  position: absolute;
  bottom: -0.25rem;
  right: -0.25rem;
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 9999px;
  background: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 0 2px var(--card-bg-transparent);
}

.verify-icon {
  width: 0.75rem;
  height: 0.75rem;
  color: #fff;
}

.site-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-primary);
}

.site-desc {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin-top: 0.125rem;
}

.copy-list {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  flex: 1;
}

.copy-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  border-radius: 0.5rem;
  background: rgba(0, 0, 0, 0.05);
  padding: 0.5rem 0.75rem;
}

.dark .copy-row {
  background: rgba(255, 255, 255, 0.05);
}

.copy-label {
  font-size: 0.65rem;
  color: var(--text-tertiary);
  margin-bottom: 0.125rem;
}

.copy-value {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.copy-btn {
  flex-shrink: 0;
  width: 1.75rem;
  height: 1.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.375rem;
  background: rgba(0, 0, 0, 0.1);
  color: var(--btn-content);
  transition: opacity 0.2s;
  cursor: pointer;
  border: none;
  padding: 0;
}

.dark .copy-btn {
  background: rgba(255, 255, 255, 0.1);
}

.copy-btn:hover {
  opacity: 0.8;
}

.copy-icon {
  width: 0.875rem;
  height: 0.875rem;
}

.copy-success {
  color: #22c55e;
}

.panel-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.title-icon {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 0.5rem;
  background: rgba(var(--el-color-primary-rgb), 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
  font-size: 0.875rem;
}

.title-icon svg {
  width: 1rem;
  height: 1rem;
}

.steps {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.step {
  display: flex;
  gap: 0.875rem;
}

.step-left {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.step-number {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 9999px;
  background: var(--primary);
  color: #fff;
  font-size: 0.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.step-line {
  width: 0.125rem;
  flex: 1;
  background: var(--line-divider);
  margin: 0.375rem 0;
}

.step-content {
  flex: 1;
  min-width: 0;
}

.step-title {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.step-text {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  line-height: 1.625;
  margin-bottom: 0.75rem;
}

.inline-code {
  font-size: 0.7rem;
  vertical-align: middle;
  color: var(--primary);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  background: rgba(0, 0, 0, 0.05);
}

.dark .inline-code {
  background: rgba(255, 255, 255, 0.05);
}

.template-box {
  position: relative;
  margin-top: 0.25rem;
  margin-bottom: 1rem;
  border-radius: 0.5rem;
  background: rgba(0, 0, 0, 0.05);
  padding: 1rem 2.5rem 1rem 1rem;
  font-size: 0.7rem;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre;
}

.dark .template-box {
  background: rgba(255, 255, 255, 0.05);
}

.template-copy-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  width: 1.75rem;
  height: 1.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.375rem;
  background: rgba(0, 0, 0, 0.1);
  color: var(--btn-content);
  transition: opacity 0.2s;
  cursor: pointer;
  border: none;
  padding: 0;
}

.dark .template-copy-btn {
  background: rgba(255, 255, 255, 0.1);
}

.template-copy-btn:hover {
  opacity: 0.8;
}

.template-pre {
  margin: 0;
  font-family: inherit;
  white-space: pre;
  color: var(--text-secondary);
}

.notes-icon {
  width: 1.125rem;
  height: 1.125rem;
  color: var(--primary);
}

.notes-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.note-item {
  display: flex;
  align-items: baseline;
  gap: 0.625rem;
}

.note-dot {
  width: 0.375rem;
  height: 0.375rem;
  border-radius: 9999px;
  background: var(--primary);
  flex-shrink: 0;
  transform: translateY(-2px);
}

.note-strong {
  font-weight: 600;
  color: var(--text-primary);
}

.min-w-0 {
  min-width: 0;
}

:deep(.el-skeleton) {
  width: 100%;
}

.hidden {
  display: none;
}
</style>
