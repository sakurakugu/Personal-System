<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElAside, ElButton, ElContainer, ElIcon, ElMain, ElMenu, ElMenuItem } from 'element-plus'
import { House, Checked, CreditCard, Document, Folder, DataAnalysis, Monitor, Fold, Expand, Grid, User, Setting, Bell, Link, ChatDotRound, ChatLineRound } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const collapsed = ref(false)
const autoCollapsed = ref(false)
const siderWidth = 200
const siderCollapsedWidth = 64
const collapseRatio = 0.22
const expandRatio = 0.2

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
  collapsed.value = !collapsed.value
  autoCollapsed.value = false
  applyAutoCollapse()
}

function applyAutoCollapse() {
  const width = window.innerWidth
  if (!width) return
  const ratio = siderWidth / width
  if (!collapsed.value && ratio >= collapseRatio) {
    collapsed.value = true
    autoCollapsed.value = true
    return
  }
  if (collapsed.value && autoCollapsed.value && ratio <= expandRatio) {
    collapsed.value = false
    autoCollapsed.value = false
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
      :class="{ 'is-collapsed': collapsed }"
      :width="`${collapsed ? siderCollapsedWidth : siderWidth}px`"
    >
      <div class="sider-inner">
        <div class="sider-title">
          <ElIcon><Grid /></ElIcon>
          <span class="sider-title-text">控制台</span>
        </div>
        <ElMenu
          :collapse="collapsed"
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
              <component :is="collapsed ? Expand : Fold" />
            </ElIcon>
            <span class="sider-trigger-text">收起侧栏</span>
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

.dashboard-sider.is-collapsed .sider-title {
  padding-left: 24px;
}

.dashboard-sider.is-collapsed .sider-title-text,
.dashboard-sider.is-collapsed .sider-trigger-text {
  opacity: 0;
  transform: translateX(-8px);
  pointer-events: none;
}

.dashboard-sider.is-collapsed .sider-trigger :deep(.el-button) {
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

.dashboard-sider.is-collapsed .sider-inner :deep(.el-menu-item.menu-item--admin-start::before),
.dashboard-sider.is-collapsed .sider-inner :deep(.el-menu-item.menu-item--super-admin-start::before) {
  left: 12px;
  right: 12px;
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

.dark .dashboard-main {
  background-color: var(--bg-primary);
}
</style>
