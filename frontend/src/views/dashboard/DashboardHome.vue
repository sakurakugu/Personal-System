<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { Component } from 'vue'
import { useRouter } from 'vue-router'
import { ElAvatar, ElButton, ElCard, ElEmpty, ElIcon, ElInput, ElMessage, ElPagination, ElPopconfirm, ElSkeleton, ElSpace, ElSwitch, ElTag, ElText, ElTooltip } from 'element-plus'
import {
  User,
  EditPen,
  Checked,
  CreditCard,
  Document,
  Folder,
  DataAnalysis,
  Link,
  ChatLineRound,
  Monitor,
  Setting,
  Bell,
  House,
  DocumentChecked,
  Plus,
  RefreshLeft,
  View,
} from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { fetchFeedList } from '../../features/feed/api'
import type { FeedItemRecord } from '../../features/feed/types'
import { useMomentStore } from '../../stores/moment'

type ShortcutCard = {
  key: string
  title: string
  description: string
  path: string
  icon: Component
  badge?: string
}

const auth = useAuthStore()
const router = useRouter()
const momentStore = useMomentStore()
const loading = ref(true)
const feedLoading = ref(false)
const feedItems = ref<FeedItemRecord[]>([])
const currentPage = ref(1)
const totalPages = ref(0)
const selectedFeedFilter = ref<'all' | 'article'>('all')
const hidePrivate = ref(true)
const draftForm = ref({
  title: '',
  content: '',
})
const loadingDraft = ref(false)

const roleLabelMap = {
  user: '普通用户',
  admin: '管理员',
  super_admin: '超级管理员',
} as const

const roleTagTypeMap: Record<string, 'info' | 'success' | 'danger'> = {
  user: 'info',
  admin: 'success',
  super_admin: 'danger',
}

const displayName = computed(() => auth.user?.nickname?.trim() || auth.user?.username || '你')
const avatarText = computed(() => displayName.value.slice(0, 1).toUpperCase())
const roleLabel = computed(() => roleLabelMap[auth.user?.role || 'user'] || '普通用户')
const roleTagType = computed(() => roleTagTypeMap[auth.user?.role || 'user'] || 'info')
const joinedDate = computed(() => {
  if (!auth.user?.created_at) return '未知'
  return new Date(auth.user.created_at).toLocaleDateString('zh-CN')
})

const shortcutCards = computed<ShortcutCard[]>(() => {
  const reviewItems: ShortcutCard[] = []

  if (auth.isAdmin) {
    reviewItems.push({
      key: 'comments',
      title: '评论审核',
      description: '集中处理站点评论和互动内容。',
      path: '/dashboard/comments',
      icon: ChatLineRound,
      badge: '管理员',
    })
  }

  if (auth.isSuperAdmin) {
    reviewItems.push({
      key: 'links',
      title: '友链管理',
      description: '维护友链资料和展示顺序。',
      path: '/dashboard/links',
      icon: Link,
      badge: '超管',
    })
  }

  const items: ShortcutCard[] = [
    ...reviewItems,
    {
      key: 'profile',
      title: '编辑资料',
      description: '维护头像、昵称、邮箱和个人简介。',
      path: '/dashboard/profile',
      icon: EditPen,
    },
    {
      key: 'todos',
      title: '待办事项',
      description: '继续处理计划、清单和执行节奏。',
      path: '/dashboard/todos',
      icon: Checked,
    },
    {
      key: 'articles',
      title: '文章管理',
      description: '整理草稿、发布内容和维护文章状态。',
      path: '/dashboard/articles',
      icon: Document,
    },
    {
      key: 'bills',
      title: '账单管理',
      description: '录入收支记录，保持日常记账连续性。',
      path: '/dashboard/bills',
      icon: CreditCard,
    },
    {
      key: 'files',
      title: '文件管理',
      description: '查看和整理已经上传的文件资源。',
      path: '/dashboard/files',
      icon: Folder,
    },
    {
      key: 'stats',
      title: '数据统计',
      description: '单独查看内容、互动、浏览和账单趋势。',
      path: '/dashboard/stats',
      icon: DataAnalysis,
    },
  ]

  if (auth.isSuperAdmin) {
    items.push({
      key: 'system',
      title: '系统状态',
      description: '检查服务、数据库和对象存储状态。',
      path: '/dashboard/system',
      icon: Monitor,
      badge: '超管',
    })
    items.push({
      key: 'settings',
      title: '系统设置',
      description: '调整评论、注册等全局配置。',
      path: '/dashboard/settings',
      icon: Setting,
      badge: '超管',
    })
    items.push({
      key: 'announcements',
      title: '公告管理',
      description: '发布或维护站点公告内容。',
      path: '/dashboard/announcements',
      icon: Bell,
      badge: '超管',
    })
  }

  return items
})

const leftFilters = computed(() => [
  { key: 'home', label: '主页总览', count: '现在', icon: House, active: true, path: '/dashboard' },
  { key: 'profile', label: '资料维护', count: '个人', icon: User, active: false, path: '/dashboard/profile' },
  { key: 'work', label: '任务执行', count: '待办', icon: Checked, active: false, path: '/dashboard/todos' },
  { key: 'content', label: '内容发布', count: '文章', icon: Document, active: false, path: '/dashboard/articles' },
  { key: 'assets', label: '资源整理', count: '文件', icon: Folder, active: false, path: '/dashboard/files' },
])

const rightHighlights = computed(() => [
  { label: '当前身份', value: roleLabel.value, emphasize: true },
  { label: '账户状态', value: auth.user?.is_active === false ? '账户停用' : '账户正常' },
])

const quickStats = computed(() => [
  { label: '可用入口', value: `${shortcutCards.value.length}` },
  { label: '主控状态', value: auth.user?.is_active === false ? '暂停' : '在线' },
  { label: '资料完整度', value: auth.user?.bio?.trim() && auth.user?.email ? '较高' : '待补充' },
])
const contentLength = computed(() => draftForm.value.content.length)
const isOverLimit = computed(() => contentLength.value > 1000)

const visibleFeedItems = computed(() => feedItems.value.filter((item) => {
  if (selectedFeedFilter.value === 'article' && item.type !== 'article') return false
  if (hidePrivate.value && item.type === 'article' && item.article?.status === 'private') return false
  return true
}))

function goTo(path: string) {
  router.push(path)
}

function 生成动态摘要(content: string) {
  return content.length > 220 ? `${content.slice(0, 220)}...` : content
}

function 格式化动态时间(date: string | null) {
  if (!date) return '刚刚'
  return new Date(date).toLocaleString('zh-CN')
}

async function loadDraft() {
  loadingDraft.value = true
  try {
    const draft = await momentStore.fetchDraft()
    draftForm.value.title = draft?.title || ''
    draftForm.value.content = draft?.content || ''
  } finally {
    loadingDraft.value = false
  }
}

let saveTimeout: ReturnType<typeof window.setTimeout> | null = null

function autoSave() {
  if (saveTimeout) window.clearTimeout(saveTimeout)
  saveTimeout = window.setTimeout(async () => {
    if (draftForm.value.content.trim() || draftForm.value.title.trim()) {
      await momentStore.saveDraft({
        title: draftForm.value.title,
        content: draftForm.value.content,
      })
    }
  }, 1000)
}

async function handleSaveDraft() {
  if (!draftForm.value.content.trim()) {
    ElMessage.warning('内容不能为空')
    return
  }
  await momentStore.saveDraft({
    title: draftForm.value.title,
    content: draftForm.value.content,
  })
  ElMessage.success('草稿已保存')
}

async function handlePublish() {
  if (!draftForm.value.content.trim()) {
    ElMessage.warning('内容不能为空')
    return
  }
  if (isOverLimit.value) {
    ElMessage.warning('内容超过1000字限制')
    return
  }

  await momentStore.publish({
    title: draftForm.value.title,
    content: draftForm.value.content,
  })
  ElMessage.success('发布成功')
  draftForm.value = { title: '', content: '' }
  await loadFeed(1)
}

async function handleClearDraft() {
  draftForm.value = { title: '', content: '' }
  await momentStore.saveDraft({ title: '', content: '' })
  ElMessage.success('草稿已清空')
}

function goArticle(slug: string) {
  void router.push(`/blog/${slug}`)
}

async function loadFeed(page = 1) {
  feedLoading.value = true

  try {
    const data = await fetchFeedList(page, { include_own_private: true })
    feedItems.value = data.items
    currentPage.value = data.page
    totalPages.value = data.pages
  } catch {
    feedItems.value = []
    currentPage.value = page
    totalPages.value = 0
  } finally {
    feedLoading.value = false
  }
}

onMounted(async () => {
  try {
    await auth.restoreUserIfNeeded()
    await loadDraft()
    await loadFeed(1)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page-container">
    <ElSkeleton :loading="loading" animated>
      <section class="topbar">
        <div class="topbar-main">
          <div class="topbar-profile">
            <ElAvatar v-if="auth.user?.avatar_url" :src="auth.user.avatar_url" :size="64" class="profile-avatar" />
            <ElAvatar v-else :size="64" class="profile-avatar profile-avatar--fallback">
              {{ avatarText }}
            </ElAvatar>
            <div class="topbar-profile-copy">
              <strong class="profile-name">{{ displayName }}</strong>
              <span class="profile-handle">@{{ auth.user?.username || 'unknown' }}</span>
              <div class="profile-tags">
                <ElTag :type="roleTagType" effect="dark">{{ roleLabel }}</ElTag>
                <ElTag :type="auth.user?.is_active === false ? 'danger' : 'success'" effect="plain">
                  {{ auth.user?.is_active === false ? '账户停用' : '账户正常' }}
                </ElTag>
              </div>
            </div>
          </div>
          <div class="topbar-actions">
            <ElButton type="primary" @click="goTo('/dashboard/profile')">编辑资料</ElButton>
            <ElButton @click="goTo('/dashboard/stats')">查看统计</ElButton>
          </div>
        </div>
      </section>

      <section class="dashboard-grid">
        <aside class="left-rail">
          <ElCard class="rail-card" shadow="never">
            <div class="rail-title">左侧筛选</div>
            <div class="filter-list">
              <button
                v-for="item in leftFilters"
                :key="item.key"
                type="button"
                class="filter-item"
                :class="{ 'is-active': item.active }"
                @click="goTo(item.path)"
              >
                <span class="filter-icon">
                  <ElIcon><component :is="item.icon" /></ElIcon>
                </span>
                <span class="filter-copy">
                  <strong>{{ item.label }}</strong>
                  <small>{{ item.count }}</small>
                </span>
              </button>
            </div>
          </ElCard>
        </aside>

        <main class="feed-column">
          <ElCard class="compose-entry" shadow="never">
            <ElSkeleton :loading="loadingDraft" animated>
              <div class="compose-entry-header">
                <div class="compose-entry-title">
                  <ElIcon><DocumentChecked /></ElIcon>
                  <span>编写动态</span>
                </div>
                <ElSpace>
                  <ElTooltip content="自动获取上次未发布的内容">
                    <ElButton text :icon="RefreshLeft" :loading="loadingDraft" @click="loadDraft">
                      刷新草稿
                    </ElButton>
                  </ElTooltip>
                </ElSpace>
              </div>

              <div class="compose-entry-main">
                <div class="compose-entry-avatar">
                  <ElAvatar v-if="auth.user?.avatar_url" :src="auth.user.avatar_url" :size="40" />
                  <ElAvatar v-else :size="40" class="profile-avatar--fallback compose-entry-avatar-fallback">
                    {{ avatarText }}
                  </ElAvatar>
                </div>
                <div class="compose-entry-form">
                  <ElInput
                    v-model="draftForm.title"
                    class="compose-title-input"
                    placeholder="标题（可选）"
                    maxlength="100"
                    @input="autoSave"
                  />
                  <ElInput
                    v-model="draftForm.content"
                    type="textarea"
                    :rows="4"
                    resize="none"
                    placeholder="分享一下你现在在想什么？"
                    maxlength="1000"
                    show-word-limit
                    @input="autoSave"
                  />
                  <div class="compose-entry-footer">
                    <ElTag :type="isOverLimit ? 'danger' : 'info'" size="small">
                      {{ contentLength }} / 1000 字
                    </ElTag>
                    <div class="compose-entry-actions">
                      <ElButton :loading="momentStore.saving" @click="handleSaveDraft">保存草稿</ElButton>
                      <ElPopconfirm
                        title="确定要清空草稿吗？"
                        confirm-button-text="确定"
                        cancel-button-text="取消"
                        @confirm="handleClearDraft"
                      >
                        <template #reference>
                          <ElButton>清空</ElButton>
                        </template>
                      </ElPopconfirm>
                      <ElButton type="primary" :icon="Plus" :disabled="isOverLimit || !draftForm.content.trim()" @click="handlePublish">
                        发布
                      </ElButton>
                    </div>
                  </div>
                </div>
              </div>
            </ElSkeleton>
          </ElCard>

          <div class="feed-toolbar">
            <div class="feed-toolbar-tabs">
              <button
                type="button"
                class="feed-toolbar-tab"
                :class="{ 'is-active': selectedFeedFilter === 'all' }"
                @click="selectedFeedFilter = 'all'"
              >
                全部
              </button>
              <button
                type="button"
                class="feed-toolbar-tab"
                :class="{ 'is-active': selectedFeedFilter === 'article' }"
                @click="selectedFeedFilter = 'article'"
              >
                文章
              </button>
            </div>
            <label class="feed-toolbar-switch">
              <span>不显示私有</span>
              <ElSwitch v-model="hidePrivate" />
            </label>
          </div>

          <ElSkeleton :loading="feedLoading" animated>
            <div v-if="visibleFeedItems.length === 0 && !feedLoading" class="empty-state">
              <ElEmpty description="暂无内容" />
            </div>

            <div class="feed-list">
              <ElCard
                v-for="item in visibleFeedItems"
                :key="`${item.type}-${item.source_id}`"
                shadow="hover"
                class="feed-card"
                :class="item.type === 'article' ? 'article-card' : 'moment-card'"
                @click="item.type === 'article' && item.article ? goArticle(item.article.slug) : undefined"
              >
                <template v-if="item.type === 'article' && item.article">
                  <div v-if="item.article.cover_url" class="article-cover">
                    <img :src="item.article.cover_url" :alt="item.article.title">
                  </div>
                  <div class="article-body">
                    <h2 class="article-title">{{ item.article.title }}</h2>
                    <p class="article-excerpt">{{ item.article.excerpt || '暂无摘要' }}</p>
                    <div class="article-meta">
                      <ElSpace size="small">
                        <ElTag v-if="item.article.category" size="small" type="info">{{ item.article.category.name }}</ElTag>
                        <ElTag v-for="tag in item.article.tags" :key="tag.id" size="small">{{ tag.name }}</ElTag>
                      </ElSpace>
                      <ElText type="info" class="feed-meta-text">
                        {{ item.article.author.nickname || item.article.author.username }} · {{ new Date(item.article.published_at || item.article.created_at).toLocaleDateString('zh-CN') }}
                        ·
                        <ElIcon><View /></ElIcon>
                        {{ item.article.view_count }}
                      </ElText>
                    </div>
                  </div>
                </template>

                <template v-else-if="item.type === 'moment' && item.moment">
                  <div class="moment-header">
                    <div class="moment-author">
                      <div class="moment-avatar">
                        <img v-if="item.moment.user?.avatar_url" :src="item.moment.user.avatar_url" :alt="item.moment.user.nickname || item.moment.user.username">
                        <span v-else>{{ (item.moment.user?.nickname || item.moment.user?.username || '我').slice(0, 1) }}</span>
                      </div>
                      <div class="moment-author-meta">
                        <strong>{{ item.moment.user?.nickname || item.moment.user?.username || '未知用户' }}</strong>
                        <ElText type="info">{{ 格式化动态时间(item.moment.published_at) }}</ElText>
                      </div>
                    </div>
                    <ElTag size="small" type="success" effect="plain">动态</ElTag>
                  </div>
                  <h2 v-if="item.moment.title" class="article-title moment-title">{{ item.moment.title }}</h2>
                  <p class="moment-excerpt">{{ 生成动态摘要(item.moment.content) }}</p>
                </template>
              </ElCard>
            </div>
          </ElSkeleton>

          <div v-if="totalPages > 1" class="pagination">
            <ElPagination
              :current-page="currentPage"
              :page-count="totalPages"
              layout="prev, pager, next"
              @update:current-page="loadFeed"
            />
          </div>
        </main>

        <aside class="right-rail">
          <ElCard class="right-card" shadow="never">
            <div class="rail-title">资料摘要</div>
            <div class="highlight-list">
              <div v-for="item in rightHighlights" :key="item.label" class="highlight-item">
                <span>{{ item.label }}</span>
                <strong :class="{ 'is-emphasize': item.emphasize }">{{ item.value }}</strong>
              </div>
            </div>
            <div class="right-card-section">
              <div class="mini-meta">
                <div class="mini-meta-item">
                  <span>邮箱</span>
                  <strong>{{ auth.user?.email || '未设置' }}</strong>
                </div>
                <div class="mini-meta-item">
                  <span>加入时间</span>
                  <strong>{{ joinedDate }}</strong>
                </div>
              </div>
            </div>
          </ElCard>

          <ElCard class="right-card" shadow="never">
            <div class="rail-title">状态概览</div>
            <div class="stats-list">
              <div v-for="item in quickStats" :key="item.label" class="stats-item">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
          </ElCard>
        </aside>
      </section>
    </ElSkeleton>
  </div>
</template>

<style scoped>
.page-container {
  height: 100%;
  overflow-y: auto;
  padding: 18px;
  box-sizing: border-box;
  background:
    radial-gradient(circle at top left, rgba(24, 160, 88, 0.1), transparent 28%),
    linear-gradient(180deg, #f6fbf8 0%, #f3f7f5 100%);
}

:deep(.el-card) {
  border-radius: 18px;
  border-color: rgba(24, 160, 88, 0.1);
}

.topbar {
  margin-bottom: 18px;
}

.topbar-main {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) auto;
  align-items: center;
  gap: 20px;
  min-height: 136px;
  padding: 20px 24px;
  border: 1px solid rgba(24, 160, 88, 0.14);
  border-radius: 22px;
  background:
    linear-gradient(135deg, rgba(24, 160, 88, 0.12), rgba(24, 160, 88, 0.03)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.99));
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.topbar-profile {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.topbar-profile-copy {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.topbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(220px, 280px) minmax(0, 1fr) minmax(240px, 300px);
  gap: 18px;
  align-items: start;
  width: 100%;
}

.left-rail,
.right-rail,
.feed-column {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.left-rail,
.right-rail {
  position: sticky;
  top: 0;
}

.rail-card,
.right-card,
.compose-entry,
.feed-card {
  border: 1px solid rgba(24, 160, 88, 0.1);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
  backdrop-filter: blur(10px);
}

.rail-card :deep(.el-card__body),
.right-card :deep(.el-card__body) {
  padding: 18px;
}

.rail-title {
  margin-bottom: 14px;
  font-size: 16px;
  font-weight: 700;
  color: #102418;
}

.right-card::after {
  content: '';
  position: absolute;
  inset: auto -40px -60px auto;
  width: 120px;
  height: 120px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(24, 160, 88, 0.12), transparent 70%);
  pointer-events: none;
}

.profile-avatar {
  flex-shrink: 0;
  border: 3px solid rgba(255, 255, 255, 0.82);
}

.profile-avatar--fallback {
  background: linear-gradient(135deg, #18a058, #4cb080);
  color: #fff;
  font-size: 24px;
  font-weight: 700;
}

.profile-name {
  font-size: 18px;
}

.profile-handle {
  color: var(--el-text-color-secondary);
  word-break: break-word;
}

.profile-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.filter-list {
  display: grid;
  gap: 10px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 14px;
  border: 1px solid rgba(24, 160, 88, 0.08);
  border-radius: 14px;
  background: rgba(248, 252, 249, 0.9);
  cursor: pointer;
  text-align: left;
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    background-color 0.18s ease;
}

.filter-item:hover,
.filter-item.is-active {
  transform: translateY(-1px);
  border-color: rgba(24, 160, 88, 0.22);
  background: rgba(24, 160, 88, 0.08);
}

.filter-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(24, 160, 88, 0.16), rgba(24, 160, 88, 0.08));
  color: #137046;
  font-size: 18px;
}

.filter-copy {
  display: grid;
  gap: 4px;
}

.filter-copy strong {
  font-size: 14px;
}

.filter-copy small {
  color: var(--el-text-color-secondary);
}

.mini-meta {
  display: grid;
  gap: 12px;
}

.mini-meta-item,
.highlight-item,
.stats-item {
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(247, 250, 248, 0.92);
}

.mini-meta-item span,
.highlight-item span,
.stats-item span {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.mini-meta-item strong,
.highlight-item strong,
.stats-item strong {
  line-height: 1.5;
  word-break: break-word;
}

.compose-entry :deep(.el-card__body) {
  padding: 16px 18px;
}

.compose-entry-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.compose-entry-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  color: #102418;
}

.compose-entry-main {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.compose-entry-avatar {
  flex: 0 0 auto;
}

.compose-entry-avatar-fallback {
  font-size: 16px;
  font-weight: 700;
}

.compose-entry-form {
  flex: 1;
  min-width: 0;
}

.compose-title-input {
  margin-bottom: 12px;
}

.compose-entry-form :deep(.el-input__wrapper),
.compose-entry-form :deep(.el-textarea__inner) {
  border: 1px solid rgba(24, 160, 88, 0.08);
  box-shadow: none;
  background: rgba(246, 250, 247, 0.95);
  transition:
    border-color 0.18s ease,
    background-color 0.18s ease;
}

.compose-entry-form :deep(.el-input__wrapper) {
  min-height: 42px;
  border-radius: 999px;
}

.compose-entry-form :deep(.el-textarea__inner) {
  min-height: 104px !important;
  border-radius: 20px;
  padding: 14px 16px;
  line-height: 1.7;
}

.compose-entry-form :deep(.el-input__wrapper:hover),
.compose-entry-form :deep(.el-input__wrapper.is-focus),
.compose-entry-form :deep(.el-textarea__inner:hover),
.compose-entry-form :deep(.el-textarea__inner:focus) {
  border-color: rgba(24, 160, 88, 0.18);
  background: rgba(24, 160, 88, 0.07);
}

.compose-entry-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
}

.compose-entry-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.feed-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 52px;
  padding: 10px 16px;
  border: 1px solid rgba(24, 160, 88, 0.1);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
}

.feed-toolbar-tabs {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.feed-toolbar-tab {
  min-width: 68px;
  padding: 8px 14px;
  border: 1px solid transparent;
  border-radius: 999px;
  background: transparent;
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition:
    background-color 0.18s ease,
    color 0.18s ease,
    border-color 0.18s ease;
}

.feed-toolbar-tab.is-active {
  border-color: rgba(24, 160, 88, 0.16);
  background: rgba(24, 160, 88, 0.1);
  color: #137046;
  font-weight: 600;
}

.feed-toolbar-switch {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  white-space: nowrap;
}

.empty-state {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.feed-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feed-card {
  transition: transform 0.2s, box-shadow 0.2s;
  overflow: hidden;
}

.feed-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.08);
}

.feed-card :deep(.el-card__body) {
  padding: 18px 20px;
}

.article-card {
  cursor: pointer;
}

.article-cover img {
  width: 100%;
  height: 220px;
  object-fit: cover;
  border-radius: 10px;
  margin-bottom: 14px;
}

.article-title {
  margin: 0 0 8px;
  font-size: 20px;
  line-height: 1.4;
}

.article-excerpt {
  color: #666;
  font-size: 14px;
  margin: 0 0 12px;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.7;
}

.article-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.feed-meta-text {
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.moment-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 248, 251, 0.96)),
    linear-gradient(120deg, rgba(24, 160, 88, 0.08), transparent 48%);
  border-color: rgba(24, 160, 88, 0.08);
}

.moment-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.moment-author {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.moment-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  overflow: hidden;
  border-radius: 50%;
  background: linear-gradient(135deg, #18a058, #34d399);
  color: #fff;
  font-weight: 700;
}

.moment-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.moment-author-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.moment-author-meta strong {
  color: #111827;
  font-size: 14px;
}

.moment-title {
  margin-bottom: 10px;
}

.moment-excerpt {
  margin: 0;
  color: #4b5563;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.pagination {
  display: flex;
  justify-content: center;
  padding: 12px 0 24px;
}

.highlight-list,
.stats-list {
  display: grid;
  gap: 12px;
}

.right-card-section {
  margin-top: 18px;
}

.highlight-item strong.is-emphasize {
  color: #137046;
}

.right-card {
  position: relative;
  overflow: hidden;
}

.dark .page-container {
  background:
    radial-gradient(circle at top left, rgba(120, 214, 163, 0.12), transparent 28%),
    linear-gradient(180deg, #111916 0%, #0f1513 100%);
}

.dark .topbar-main,
.dark .rail-card,
.dark .right-card,
.dark .compose-entry,
.dark .feed-card {
  border-color: rgba(120, 214, 163, 0.14);
  background:
    linear-gradient(135deg, rgba(24, 160, 88, 0.14), rgba(24, 160, 88, 0.05)),
    rgba(18, 25, 22, 0.9);
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.24);
}

.dark .filter-icon,
.dark .highlight-item strong.is-emphasize {
  color: #8fdeb7;
}

.dark .filter-item,
.dark .mini-meta-item,
.dark .highlight-item,
.dark .stats-item,
.dark .feed-toolbar {
  background: rgba(18, 25, 22, 0.72);
  border-color: rgba(120, 214, 163, 0.1);
}

.dark .filter-item:hover,
.dark .filter-item.is-active {
  background: rgba(120, 214, 163, 0.12);
}

.dark .rail-title {
  color: #eef8f1;
}

.dark .profile-avatar--fallback {
  background: linear-gradient(135deg, #1d9c64, #62c491);
}

.dark .compose-entry-copy strong {
  color: #eef8f1;
}

.dark .compose-entry-title {
  color: #eef8f1;
}

.dark .compose-entry-form :deep(.el-input__wrapper),
.dark .compose-entry-form :deep(.el-textarea__inner) {
  border-color: rgba(120, 214, 163, 0.1);
  background: rgba(18, 25, 22, 0.78);
  color: var(--text-secondary);
}

.dark .compose-entry-form :deep(.el-input__wrapper:hover),
.dark .compose-entry-form :deep(.el-input__wrapper.is-focus),
.dark .compose-entry-form :deep(.el-textarea__inner:hover),
.dark .compose-entry-form :deep(.el-textarea__inner:focus) {
  border-color: rgba(120, 214, 163, 0.18);
  background: rgba(120, 214, 163, 0.1);
}

.dark .feed-toolbar-tab.is-active {
  border-color: rgba(120, 214, 163, 0.2);
  background: rgba(120, 214, 163, 0.14);
  color: #8fdeb7;
}

.dark .article-title,
.dark .moment-author-meta strong {
  color: var(--text-primary);
}

.dark .article-excerpt,
.dark .moment-excerpt {
  color: var(--text-secondary);
}

.dark .moment-card {
  background:
    linear-gradient(180deg, rgba(20, 24, 30, 0.96), rgba(28, 34, 42, 0.96)),
    linear-gradient(120deg, rgba(74, 222, 128, 0.12), transparent 48%);
  border-color: rgba(74, 222, 128, 0.14);
}

@media (max-width: 1500px) {
  .dashboard-grid {
    grid-template-columns: 240px minmax(0, 1fr);
  }

  .right-rail {
    grid-column: 1 / -1;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    position: static;
  }
}

@media (max-width: 1180px) {
  .left-rail {
    position: static;
  }

  .topbar-main {
    grid-template-columns: 1fr;
    align-items: start;
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .right-rail {
    grid-column: auto;
    grid-template-columns: 1fr;
  }

  .left-rail,
  .right-rail {
    position: static;
  }
}

@media (max-width: 767px) {
  .page-container {
    padding: 14px;
  }

  .topbar-main {
    min-height: auto;
    padding: 18px;
  }

  .topbar-title {
    font-size: 24px;
  }

  .topbar-actions,
  .article-meta {
    flex-direction: column;
    align-items: stretch;
  }

  .topbar-actions :deep(.el-button),
  .article-meta :deep(.el-space) {
    width: 100%;
  }

  .compose-entry-main,
  .feed-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .compose-entry-header,
  .compose-entry-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .compose-entry-avatar {
    align-self: flex-start;
  }

  .feed-toolbar-tabs {
    width: 100%;
  }

  .feed-toolbar-tab {
    flex: 1;
  }

  .feed-card {
    padding: 18px;
  }

  .feed-card :deep(.el-card__body) {
    padding: 14px;
  }

  .moment-header {
    flex-direction: column;
  }
}
</style>
