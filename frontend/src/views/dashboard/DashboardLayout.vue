<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElAside, ElButton, ElContainer, ElIcon, ElMain, ElMenu, ElMenuItem } from 'element-plus'
import { House, Checked, CreditCard, Document, Folder, DataAnalysis, Monitor, Fold, Expand, Grid, User, Setting, Bell, Link, ChatDotRound, ChatLineRound } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
type SiderMode = 'expanded' | 'compact' | 'hidden'

const siderMode = ref<SiderMode>('expanded')
const autoCompact = ref(false)
const siderWidth = 200
const siderCompactWidth = 64
const siderHiddenWidth = 0
const collapseRatio = 0.22
const expandRatio = 0.2
const isCompact = computed(() => siderMode.value === 'compact')
const isHidden = computed(() => siderMode.value === 'hidden')
const currentSiderWidth = computed(() => {
  if (siderMode.value === 'hidden') return siderHiddenWidth
  if (siderMode.value === 'compact') return siderCompactWidth
  return siderWidth
})
const triggerIcon = computed(() => (isHidden.value ? Expand : Fold))
const triggerText = computed(() => {
  if (isHidden.value) return '展开侧栏'
  if (isCompact.value) return '继续收起'
  return '收起侧栏'
})

type MenuEntry =
  | { type: 'item'; label: string; key: string; icon: object; section?: 'admin' | 'super-admin' }

const menuOptions = computed<MenuEntry[]>(() => {
  const items: MenuEntry[] = [
    { type: 'item', label: '概览', key: '/dashboard', icon: House },
    { type: 'item', label: '个人资料', key: '/dashboard/profile', icon: User },
    { type: 'item', label: '待办事项', key: '/dashboard/todos', icon: Checked },
    { type: 'item', label: '账单管理', key: '/dashboard/bills', icon: CreditCard },
    { type: 'item', label: '动态', key: '/dashboard/moments', icon: ChatDotRound },
    { type: 'item', label: '文章管理', key: '/dashboard/articles', icon: Document },
    { type: 'item', label: '文件管理', key: '/dashboard/files', icon: Folder },
    { type: 'item', label: '数据统计', key: '/dashboard/stats', icon: DataAnalysis },
  ]
  if (auth.isAdmin) {
    items.push({ type: 'item', label: '友链管理', key: '/dashboard/links', icon: Link, section: 'admin' })
    items.push({ type: 'item', label: '评论审核', key: '/dashboard/comments', icon: ChatLineRound })
    items.push({ type: 'item', label: '系统状态', key: '/dashboard/system', icon: Monitor })
  }
  if (auth.isSuperAdmin) {
    items.push({ type: 'item', label: '用户管理', key: '/dashboard/users', icon: User, section: 'super-admin' })
    items.push({ type: 'item', label: '公告管理', key: '/dashboard/announcements', icon: Bell })
    items.push({ type: 'item', label: '系统设置', key: '/dashboard/settings', icon: Setting })
  }
  return items
})

function handleMenuUpdate(key: string) {
  router.push(key)
}

function toggleSider() {
  if (isHidden.value) {
    siderMode.value = window.innerWidth && siderWidth / window.innerWidth >= collapseRatio ? 'compact' : 'expanded'
    autoCompact.value = false
    return
  }
  if (isCompact.value) {
    siderMode.value = 'hidden'
    autoCompact.value = false
    return
  }
  siderMode.value = 'compact'
  autoCompact.value = false
}

function applyAutoCollapse() {
  const width = window.innerWidth
  if (!width) return
  const ratio = siderWidth / width
  if (ratio >= collapseRatio) {
    if (siderMode.value === 'expanded') {
      siderMode.value = 'compact'
      autoCompact.value = true
    }
    return
  }
  if (autoCompact.value && ratio <= expandRatio && siderMode.value === 'compact') {
    siderMode.value = 'expanded'
    autoCompact.value = false
  }
}

function handleResize() {
  applyAutoCollapse()
}

onMounted(() => {
  applyAutoCollapse()
  window.addEventListener('resize', handleResize)
  // 禁止 body 滚动，只允许控制台内部滚动
  document.body.style.overflow = 'hidden'
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  // 恢复 body 滚动
  document.body.style.overflow = ''
})
</script>

<template>
  <ElContainer class="dashboard-layout">
    <ElAside
      class="dashboard-sider"
      :class="{
        'is-compact': isCompact,
        'is-hidden': isHidden,
      }"
      :width="`${currentSiderWidth}px`"
    >
      <div class="sider-inner">
        <div class="sider-title">
          <ElIcon><Grid /></ElIcon>
          <span class="sider-title-text">控制台</span>
        </div>
        <ElMenu
          :collapse="isCompact"
          :collapse-transition="false"
          :default-active="route.path"
          @select="handleMenuUpdate"
        >
          <template v-for="item in menuOptions" :key="item.key">
            <ElMenuItem
              :index="item.key"
              :class="{
                'menu-item--admin-start': item.section === 'admin',
                'menu-item--super-admin-start': item.section === 'super-admin',
              }"
            >
              <ElIcon class="menu-icon"><component :is="item.icon" /></ElIcon>
              <template #title>{{ item.label }}</template>
            </ElMenuItem>
          </template>
        </ElMenu>
        <div class="sider-footer">
          <ElButton text class="sider-trigger" @click="toggleSider">
            <ElIcon class="trigger-icon">
              <component :is="triggerIcon" />
            </ElIcon>
            <span class="sider-trigger-text">{{ triggerText }}</span>
          </ElButton>
        </div>
      </div>
    </ElAside>
    <ElMain class="dashboard-main">
      <RouterView />
    </ElMain>
  </ElContainer>
</template>

<style scoped>
.dashboard-layout {
  height: calc(var(--app-viewport-height) - var(--app-header-height));
  display: flex;
  overflow: hidden;
}

.dashboard-sider {
  align-self: stretch;
  overflow: hidden;
  transition: width 0.24s cubic-bezier(0.22, 1, 0.36, 1);
  border-right: 1px solid var(--el-border-color);
  will-change: width;
  position: relative;
}

.sider-inner {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 8px 0;
  overflow: hidden;
}

.sider-inner :deep(.el-menu) {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
  border-right: none;
}

.sider-inner :deep(.el-menu::-webkit-scrollbar) {
  display: none;
}

.sider-title {
  padding: 8px 16px 16px 24px;
  font-weight: 600;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  overflow: hidden;
}

.sider-title-text,
.sider-trigger-text {
  opacity: 1;
  transform: translateX(0);
  transition:
    opacity 0.16s ease,
    transform 0.2s ease;
}

.sider-footer {
  margin-top: auto;
  padding: 12px 8px var(--app-safe-area-bottom);
  overflow: hidden;
}

.sider-trigger {
  width: 100%;
  justify-content: flex-start;
  overflow: hidden;
  white-space: nowrap;
}

.menu-icon {
  font-size: 18px;
  line-height: 1;
  position: relative;
  top: -1px;
}

.trigger-icon {
  font-size: 16px;
}

.dashboard-main {
  --dashboard-panel-radius: 12px;
  padding: 0 !important;
  overflow: hidden;
  height: 100%;
  box-sizing: border-box;
}

.dashboard-main :deep(> *) {
  height: 100%;
}

.dashboard-main :deep(.el-card) {
  border-radius: var(--dashboard-panel-radius);
  overflow: hidden;
}

.sider-trigger :deep(.el-button) {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
  overflow: visible;
  white-space: nowrap;
  padding-left: 20px;
}

.dashboard-sider.is-compact .sider-title {
  padding-left: 24px;
}

.dashboard-sider.is-compact .sider-title-text,
.dashboard-sider.is-compact .sider-trigger-text {
  opacity: 0;
  transform: translateX(-8px);
  pointer-events: none;
}

.dashboard-sider.is-compact .sider-trigger :deep(.el-button) {
  gap: 0;
  justify-content: center;
  padding-left: 0;
}

.sider-inner :deep(.el-menu-item.menu-item--admin-start),
.sider-inner :deep(.el-menu-item.menu-item--super-admin-start) {
  position: relative;
  margin-top: 14px;
}

.sider-inner :deep(.el-menu-item.menu-item--admin-start::before),
.sider-inner :deep(.el-menu-item.menu-item--super-admin-start::before) {
  content: '';
  position: absolute;
  left: 16px;
  right: 16px;
  top: -8px;
  height: 1px;
  background-color: var(--el-border-color);
  opacity: 0.9;
}

.dashboard-sider.is-compact .sider-inner :deep(.el-menu-item.menu-item--admin-start::before),
.dashboard-sider.is-compact .sider-inner :deep(.el-menu-item.menu-item--super-admin-start::before) {
  left: 12px;
  right: 12px;
}

.dashboard-sider.is-hidden {
  width: 0 !important;
  min-width: 0 !important;
  border-right: none;
  overflow: visible;
}

.dashboard-sider.is-hidden .sider-inner {
  padding: 0;
  overflow: visible;
}

.dashboard-sider.is-hidden .sider-title,
.dashboard-sider.is-hidden .sider-inner :deep(.el-menu) {
  opacity: 0;
  pointer-events: none;
}

.dashboard-sider.is-hidden .sider-footer {
  position: absolute;
  left: 0;
  right: -16px;
  bottom: calc(12px + var(--app-safe-area-bottom));
  padding: 0;
  overflow: visible;
  display: flex;
  justify-content: flex-start;
}

.dashboard-sider.is-hidden .sider-trigger {
  width: 60px;
  min-width: 60px;
  max-width: 60px;
  flex: 0 0 60px;
  height: 36px;
  border-radius: 0 16px 16px 0;
  background-color: var(--el-bg-color-overlay);
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.12);
  border: 1px solid var(--el-border-color-light);
  border-left: none;
  position: relative;
  z-index: 1;
}

.dashboard-sider.is-hidden .sider-trigger::before {
  content: '';
  position: absolute;
  left: 10px;
  top: 50%;
  width: 4px;
  height: 16px;
  border-radius: 999px;
  background-color: color-mix(in srgb, var(--el-text-color-secondary) 22%, transparent);
  transform: translateY(-50%);
}

.dashboard-sider.is-hidden :deep(.el-button.sider-trigger) {
  width: 43px;
  min-width: 43px;
  max-width: 43px;
  flex: 0 0 43px;
}

.dashboard-sider.is-hidden :deep(.el-button.sider-trigger .el-button__text) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.dashboard-sider.is-hidden .sider-trigger :deep(.el-button) {
  width: 100%;
  height: 100%;
  padding: 0 0 0 10px;
  gap: 0;
  justify-content: center;
}

.dashboard-sider.is-hidden .sider-trigger-text {
  display: none;
}

.dashboard-sider.is-hidden .trigger-icon {
  font-size: 18px;
}

/* 夜间模式 */
.dark .dashboard-sider {
  background-color: var(--sidebar-bg) !important;
  border-right-color: var(--border-color) !important;
}

.dark .sider-title {
  color: var(--text-primary);
}

.dark .sider-trigger:hover {
  background-color: var(--bg-hover) !important;
}

.dark .dashboard-sider.is-hidden .sider-trigger {
  background-color: color-mix(in srgb, var(--sidebar-bg) 88%, #ffffff 12%);
  border-color: var(--border-color);
  box-shadow: 0 10px 28px rgba(2, 6, 23, 0.32);
}

.dark .dashboard-main {
  background-color: var(--bg-primary);
}
</style>
