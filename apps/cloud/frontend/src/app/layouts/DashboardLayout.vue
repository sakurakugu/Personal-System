<script setup lang="ts">
import { Bell, ChatDotRound, Checked, Collection, CreditCard, DataAnalysis, Document, Folder, House, Link, Monitor, Setting, User } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { RouterView } from 'vue-router'
import AppConsoleLayout from '../components/layout/AppConsoleLayout.vue'
import type { 控制台菜单项 } from '../components/layout/console-layout'
import { useAuthStore } from '../../modules/auth/store'

const auth = useAuthStore()

const menuOptions = computed<控制台菜单项[]>(() => {
  const items: 控制台菜单项[] = [
    { label: '个人主页', key: '/dashboard', icon: House },
    { label: '个人资料', key: '/dashboard/profile', icon: User },
    { label: '用户设置', key: '/dashboard/user-settings', icon: Setting },
    { label: '待办事项', key: '/dashboard/todos', icon: Checked },
    { label: '账单管理', key: '/dashboard/bills', icon: CreditCard },
    { label: '动态', key: '/dashboard/moments', icon: ChatDotRound },
    { label: '收藏收纳库', key: '/dashboard/collections', icon: Collection },
    { label: '文章管理', key: '/dashboard/articles', icon: Document },
    { label: '文件管理', key: '/dashboard/files', icon: Folder },
    { label: '数据统计', key: '/dashboard/stats', icon: DataAnalysis },
  ]

  if (auth.isAdmin) {
    items.push({ label: '用户管理', key: '/dashboard/users', icon: User, dividerBefore: true })
  }
  if (auth.isSuperAdmin) {
    items.push({ label: '友链管理', key: '/dashboard/friend-links', icon: Link, dividerBefore: true })
    items.push({ label: '评论管理', key: '/dashboard/twikoo', icon: ChatDotRound })
    items.push({ label: '系统状态', key: '/dashboard/system', icon: Monitor })
    items.push({ label: '公告管理', key: '/dashboard/announcements', icon: Bell })
    items.push({ label: '系统设置', key: '/dashboard/settings', icon: Setting })
  }
  return items
})
</script>

<template>
  <AppConsoleLayout
    title="控制台"
    storage-key="dashboard_sider_mode"
    :menu-items="menuOptions"
  >
    <RouterView />
  </AppConsoleLayout>
</template>
