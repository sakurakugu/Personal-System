<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElAside, ElButton, ElContainer, ElIcon, ElMain, ElMenu, ElMenuItem } from 'element-plus'
import { House, Checked, Document, Folder, DataAnalysis, Monitor, Fold, Expand, Grid, User, Setting, Bell } from '@element-plus/icons-vue'
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

const menuOptions = computed(() => {
  const items = [
    { label: '概览', key: '/dashboard', icon: House },
    { label: '个人资料', key: '/dashboard/profile', icon: User },
    { label: '待办事项', key: '/dashboard/todos', icon: Checked },
    { label: '文章管理', key: '/dashboard/articles', icon: Document },
    { label: '文件管理', key: '/dashboard/files', icon: Folder },
    { label: '数据统计', key: '/dashboard/stats', icon: DataAnalysis },
  ]
  if (auth.isAdmin) {
    items.push({ label: '系统状态', key: '/dashboard/system', icon: Monitor })
  }
  if (auth.isSuperAdmin) {
    items.push({ label: '用户管理', key: '/dashboard/users', icon: User })
    items.push({ label: '公告管理', key: '/dashboard/announcements', icon: Bell })
    items.push({ label: '系统设置', key: '/dashboard/settings', icon: Setting })
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
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <ElContainer class="dashboard-layout">
    <ElAside
      class="dashboard-sider"
      :width="`${collapsed ? siderCollapsedWidth : siderWidth}px`"
    >
      <div class="sider-inner">
        <div v-if="!collapsed" class="sider-title">
          <ElIcon><Grid /></ElIcon>
          <span>控制台</span>
        </div>
        <ElMenu :collapse="collapsed" :default-active="route.path" @select="handleMenuUpdate">
          <ElMenuItem v-for="item in menuOptions" :key="item.key" :index="item.key">
            <ElIcon class="menu-icon"><component :is="item.icon" /></ElIcon>
            <template #title>{{ item.label }}</template>
          </ElMenuItem>
        </ElMenu>
        <div class="sider-footer">
          <ElButton text class="sider-trigger" @click="toggleSider">
            <ElIcon class="trigger-icon">
              <component :is="collapsed ? Expand : Fold" />
            </ElIcon>
            <span v-if="!collapsed">收起侧栏</span>
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
  min-height: calc(100vh - 80px);
}

.dashboard-sider {
  height: calc(100vh - 80px);
  overflow: hidden;
  transition: width 0.2s ease;
  border-right: 1px solid var(--el-border-color);
}

.sider-inner {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px 0;
  overflow: hidden;
}

.sider-title {
  padding: 8px 16px 16px;
  font-weight: 600;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.sider-footer {
  margin-top: auto;
  padding: 12px 8px 0;
  overflow: hidden;
}

.sider-trigger {
  width: 100%;
  justify-content: center;
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
  padding: 24px;
}

.sider-trigger :deep(.el-button) {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

/* 夜间模式 */
.dark .dashboard-sider {
  background-color: var(--sidebar-bg) !important;
  border-right-color: var(--border-color) !important;
}

.dark .sider-title {
  color: var(--text-primary);
}

.dark .dashboard-main {
  background-color: var(--bg-primary);
}
</style>
