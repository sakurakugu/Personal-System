<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NLayout, NLayoutSider, NLayoutContent, NMenu } from 'naive-ui'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const menuOptions = computed(() => {
  const items = [
    { label: '概览', key: '/dashboard' },
    { label: '待办事项', key: '/dashboard/todos' },
    { label: '文章管理', key: '/dashboard/articles' },
    { label: '文件管理', key: '/dashboard/files' },
    { label: '数据统计', key: '/dashboard/stats' },
  ]
  if (auth.isAdmin) {
    items.push({ label: '系统状态', key: '/dashboard/system' })
  }
  return items
})

function handleMenuUpdate(key: string) {
  router.push(key)
}
</script>

<template>
  <NLayout has-sider style="min-height: calc(100vh - 80px)">
    <NLayoutSider
      bordered
      :width="200"
      collapse-mode="width"
      :collapsed-width="0"
      show-trigger="bar"
      content-style="padding: 16px 0;"
    >
      <div style="padding: 8px 16px 16px; font-weight: 600; font-size: 16px">📋 控制台</div>
      <NMenu
        :options="menuOptions"
        :value="route.path"
        @update:value="handleMenuUpdate"
      />
    </NLayoutSider>
    <NLayoutContent content-style="padding: 24px;">
      <RouterView />
    </NLayoutContent>
  </NLayout>
</template>
