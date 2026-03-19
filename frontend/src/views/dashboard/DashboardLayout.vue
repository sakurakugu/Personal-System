<script setup lang="ts">
import { computed, h, onBeforeUnmount, onMounted, ref, type Component } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NLayout, NLayoutSider, NLayoutContent, NMenu, NButton } from 'naive-ui'
import { ElIcon } from 'element-plus'
import { House, Checked, Document, Folder, DataAnalysis, Monitor, Fold, Expand, Grid, User, Setting } from '@element-plus/icons-vue'
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

function renderIcon(icon: Component) {
  return () => h(
    ElIcon,
    {
      class: 'menu-icon',
      size: 18,
      style: {
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
      },
    },
    { default: () => h(icon, { style: { width: '1em', height: '1em' } }) },
  )
}

const menuOptions = computed(() => {
  const items = [
    { label: '概览', key: '/dashboard', icon: renderIcon(House) },
    { label: '个人资料', key: '/dashboard/profile', icon: renderIcon(User) },
    { label: '待办事项', key: '/dashboard/todos', icon: renderIcon(Checked) },
    { label: '文章管理', key: '/dashboard/articles', icon: renderIcon(Document) },
    { label: '文件管理', key: '/dashboard/files', icon: renderIcon(Folder) },
    { label: '数据统计', key: '/dashboard/stats', icon: renderIcon(DataAnalysis) },
  ]
  if (auth.isAdmin) {
    items.push({ label: '系统状态', key: '/dashboard/system', icon: renderIcon(Monitor) })
  }
  if (auth.isSuperAdmin) {
    items.push({ label: '用户管理', key: '/dashboard/users', icon: renderIcon(User) })
    items.push({ label: '系统设置', key: '/dashboard/settings', icon: renderIcon(Setting) })
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
  <NLayout has-sider class="dashboard-layout">
    <NLayoutSider
      class="dashboard-sider"
      bordered
      :width="siderWidth"
      collapse-mode="width"
      :collapsed-width="siderCollapsedWidth"
      :collapsed="collapsed"
      :show-trigger="false"
      content-style="overflow-x: hidden;"
    >
      <div class="sider-inner">
        <div v-if="!collapsed" class="sider-title">
          <ElIcon><Grid /></ElIcon>
          <span>控制台</span>
        </div>
        <NMenu
          :options="menuOptions"
          :value="route.path"
          :collapsed="collapsed"
          :collapsed-width="64"
          @update:value="handleMenuUpdate"
        />
        <div class="sider-footer">
          <NButton quaternary block class="sider-trigger" @click="toggleSider">
            <ElIcon class="trigger-icon">
              <component :is="collapsed ? Expand : Fold" />
            </ElIcon>
            <span v-if="!collapsed">收起侧栏</span>
          </NButton>
        </div>
      </div>
    </NLayoutSider>
    <NLayoutContent content-style="padding: 24px;">
      <RouterView />
    </NLayoutContent>
  </NLayout>
</template>

<style scoped>
.dashboard-layout {
  min-height: calc(100vh - 80px);
}

.dashboard-sider {
  height: calc(100vh - 80px);
  overflow: hidden;
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

.sider-trigger :deep(.n-button__content) {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
</style>
