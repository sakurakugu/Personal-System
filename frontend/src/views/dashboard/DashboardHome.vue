<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { Component } from 'vue'
import { useRouter } from 'vue-router'
import { ElAvatar, ElButton, ElCard, ElCol, ElIcon, ElRow, ElSkeleton, ElTag } from 'element-plus'
import { User, EditPen, Checked, CreditCard, Document, Folder, DataAnalysis, Link, ChatLineRound, Monitor, Setting, Bell } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'

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
const loading = ref(true)

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
const greetingText = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 11) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})
const bioText = computed(() => {
  const value = auth.user?.bio?.trim()
  return value || '这里是你的个人主页，用来查看身份信息、常用入口和后台页面分工。'
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

function goTo(path: string) {
  router.push(path)
}

onMounted(async () => {
  try {
    await auth.restoreUserIfNeeded()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page-container">
    <ElSkeleton :loading="loading" animated>
      <section class="home-hero">
        <div class="hero-main">
          <ElAvatar v-if="auth.user?.avatar_url" :src="auth.user.avatar_url" :size="88" class="hero-avatar" />
          <ElAvatar v-else :size="88" class="hero-avatar hero-avatar--fallback">
            {{ avatarText }}
          </ElAvatar>
          <div class="hero-copy">
            <div class="hero-eyebrow">
              <ElIcon><User /></ElIcon>
              <span>个人主页</span>
            </div>
            <h2 class="hero-title">{{ greetingText }}，{{ displayName }}</h2>
            <p class="hero-description">{{ bioText }}</p>
            <div class="hero-actions">
              <ElButton type="primary" @click="goTo('/dashboard/profile')">编辑个人资料</ElButton>
              <ElButton @click="goTo('/dashboard/stats')">查看数据统计</ElButton>
            </div>
          </div>
        </div>

        <div class="hero-panel">
          <div class="hero-tags">
            <ElTag :type="roleTagType" effect="dark">{{ roleLabel }}</ElTag>
            <ElTag :type="auth.user?.is_active === false ? 'danger' : 'success'" effect="plain">
              {{ auth.user?.is_active === false ? '账户停用' : '账户正常' }}
            </ElTag>
          </div>
          <div class="hero-meta">
            <div class="meta-item">
              <span class="meta-label">用户名</span>
              <strong class="meta-value">{{ auth.user?.username || '未设置' }}</strong>
            </div>
            <div class="meta-item">
              <span class="meta-label">邮箱</span>
              <strong class="meta-value">{{ auth.user?.email || '未设置' }}</strong>
            </div>
            <div class="meta-item">
              <span class="meta-label">加入时间</span>
              <strong class="meta-value">{{ joinedDate }}</strong>
            </div>
          </div>
        </div>
      </section>

      <section class="section-block">
        <div class="section-heading">
          <h3 class="section-title">常用入口</h3>
          <p class="section-description">首页只保留个人信息和快捷操作，统计指标继续放在独立的数据统计页面。</p>
        </div>
        <ElRow :gutter="16" class="shortcut-grid">
          <ElCol v-for="item in shortcutCards" :key="item.key" :xs="24" :sm="12" :xl="8">
            <ElCard class="shortcut-card" shadow="hover">
              <div class="shortcut-header">
                <div class="shortcut-icon">
                  <ElIcon><component :is="item.icon" /></ElIcon>
                </div>
                <span v-if="item.badge" class="shortcut-badge">{{ item.badge }}</span>
              </div>
              <div class="shortcut-title">{{ item.title }}</div>
              <p class="shortcut-description">{{ item.description }}</p>
              <ElButton text type="primary" @click="goTo(item.path)">进入页面</ElButton>
            </ElCard>
          </ElCol>
        </ElRow>
      </section>

      <ElCard class="page-note">
        <div class="page-note-title">页面分工</div>
        <p class="page-note-text">
          个人主页用于展示身份信息和后台入口，数据统计页面则保留所有内容、互动、浏览和记账相关的数值与趋势图，二者职责分开。
        </p>
      </ElCard>
    </ElSkeleton>
  </div>
</template>

<style scoped>
.page-container {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

:deep(.el-card) {
  border-radius: 12px;
}

.home-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(280px, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.hero-main,
.hero-panel {
  border: 1px solid rgba(24, 160, 88, 0.14);
  border-radius: 20px;
  background:
    linear-gradient(135deg, rgba(24, 160, 88, 0.12), rgba(24, 160, 88, 0.03)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.99));
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.hero-main {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  padding: 28px;
}

.hero-avatar {
  flex-shrink: 0;
  border: 4px solid rgba(255, 255, 255, 0.72);
}

.hero-avatar--fallback {
  background: linear-gradient(135deg, #18a058, #4cb080);
  color: #fff;
  font-size: 30px;
  font-weight: 700;
}

.hero-copy {
  min-width: 0;
}

.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #137046;
  font-weight: 600;
}

.hero-title {
  margin: 12px 0 10px;
  font-size: 30px;
  line-height: 1.25;
}

.hero-description {
  margin: 0;
  max-width: 720px;
  color: var(--el-text-color-secondary);
  line-height: 1.8;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 20px;
}

.hero-panel {
  padding: 24px;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 18px;
}

.hero-meta {
  display: grid;
  gap: 12px;
}

.meta-item {
  padding: 14px 16px;
  border-radius: 14px;
  background-color: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(24, 160, 88, 0.08);
}

.meta-label {
  display: block;
  margin-bottom: 6px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.meta-value {
  display: block;
  line-height: 1.5;
  word-break: break-word;
}

.section-block {
  margin-bottom: 24px;
}

.section-heading {
  margin-bottom: 16px;
}

.section-title {
  margin: 0 0 6px;
  font-size: 20px;
}

.section-description {
  margin: 0;
  color: var(--el-text-color-secondary);
  line-height: 1.7;
}

.shortcut-grid {
  row-gap: 16px;
}

.shortcut-card {
  height: 100%;
}

.shortcut-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.shortcut-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.shortcut-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(24, 160, 88, 0.16), rgba(24, 160, 88, 0.08));
  color: #137046;
  font-size: 20px;
}

.shortcut-badge {
  padding: 4px 8px;
  border-radius: 999px;
  background-color: rgba(24, 160, 88, 0.1);
  color: #137046;
  font-size: 12px;
  font-weight: 600;
}

.shortcut-title {
  font-size: 18px;
  font-weight: 600;
}

.shortcut-description {
  flex: 1;
  margin: 10px 0 18px;
  color: var(--el-text-color-secondary);
  line-height: 1.75;
}

.page-note-title {
  margin-bottom: 8px;
  font-size: 16px;
  font-weight: 600;
}

.page-note-text {
  margin: 0;
  color: var(--el-text-color-secondary);
  line-height: 1.75;
}

.dark .hero-main,
.dark .hero-panel {
  border-color: rgba(120, 214, 163, 0.16);
  background:
    linear-gradient(135deg, rgba(24, 160, 88, 0.16), rgba(24, 160, 88, 0.06)),
    rgba(18, 25, 22, 0.92);
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.24);
}

.dark .hero-eyebrow,
.dark .shortcut-icon,
.dark .shortcut-badge {
  color: #8fdeb7;
}

.dark .meta-item {
  background-color: rgba(18, 25, 22, 0.72);
  border-color: rgba(120, 214, 163, 0.12);
}

.dark .shortcut-icon {
  background: linear-gradient(135deg, rgba(120, 214, 163, 0.18), rgba(120, 214, 163, 0.08));
}

.dark .shortcut-badge {
  background-color: rgba(120, 214, 163, 0.12);
}

@media (max-width: 1100px) {
  .home-hero {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .page-container {
    padding: 16px;
  }

  .hero-main,
  .hero-panel {
    padding: 20px;
  }

  .hero-main {
    flex-direction: column;
  }

  .hero-title {
    font-size: 26px;
  }

  .hero-actions {
    flex-direction: column;
  }

  .hero-actions :deep(.el-button) {
    width: 100%;
  }
}
</style>
