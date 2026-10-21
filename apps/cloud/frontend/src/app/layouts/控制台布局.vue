<script setup lang="ts">
import { computed, watch } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import AppConsoleLayout from '../components/layout/应用控制台布局.vue'
import ConsoleTabBar from '../components/layout/控制台标签栏.vue'
import type { 控制台菜单项 } from '../components/layout/ConsoleLayout'
import { 过滤仪表盘菜单项 } from '../navigation/dashboard-navigation'
import { 是否控制台标签操作进行中 } from '../router/dashboard-tab-operation'
import { 控制台标签缓存上限, 使用控制台标签存储 } from '../stores/dashboard-tabs'

const route = useRoute()
const router = useRouter()
const tabsStore = 使用控制台标签存储()

const menuOptions = computed<控制台菜单项[]>(() => 过滤仪表盘菜单项())

tabsStore.init(router, route)

watch(
  () => route.fullPath,
  () => {
    // 关闭标签会先导航、导航成功后再落标签状态，这段路由变化不参与标签同步
    if (是否控制台标签操作进行中()) {
      return
    }
    tabsStore.syncRoute(route)
  },
  { immediate: true },
)

/**
 * 标签页 KeepAlive 缓存键：标签 + 页面标识 + 实例版本。
 * 切换标签能命中缓存保留页面状态；刷新标签或同一标签换页面时键变化，页面会重新创建。
 */
const 标签缓存键 = computed(() => {
  const 标签 = tabsStore.getTabByPath(route.path) ?? tabsStore.activeTab
  const 页面标识 = route.matched[route.matched.length - 1]?.path ?? route.path
  return `${标签?.id ?? '未归属标签'}::${页面标识}::${标签?.实例版本 ?? 0}`
})
</script>

<template>
  <AppConsoleLayout
    title="控制台"
    storage-key="dashboard_sider_mode"
    :menu-items="menuOptions"
  >
    <div class="dashboard-workspace">
      <ConsoleTabBar />
      <div class="dashboard-workspace__body">
        <RouterView v-slot="{ Component }">
          <KeepAlive :max="控制台标签缓存上限">
            <component :is="Component" :key="标签缓存键" />
          </KeepAlive>
        </RouterView>
      </div>
    </div>
  </AppConsoleLayout>
</template>

<style scoped>
.dashboard-workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.dashboard-workspace__body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.dashboard-workspace__body :deep(> *) {
  height: 100%;
}
</style>
