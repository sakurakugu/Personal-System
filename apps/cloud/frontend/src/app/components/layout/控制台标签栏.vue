<script setup lang="ts">
import { Close, Plus } from '@element-plus/icons-vue'
import { ElIcon } from 'element-plus'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 开始控制台标签操作, 结束控制台标签操作 } from '../../router/dashboard-tab-operation'
import { 清除控制台标签切换标记, 设置控制台标签切换标记 } from '../../router/dashboard-tab-switch'
import { 使用控制台标签存储, type 控制台标签项 } from '../../stores/dashboard-tabs'

const route = useRoute()
const router = useRouter()
const tabsStore = 使用控制台标签存储()

const tabs = computed(() => tabsStore.tabs)
const activeTabId = computed(() => tabsStore.activeTabId)

const 标签滚动容器 = ref<globalThis.HTMLDivElement | null>(null)
const 右键菜单元素 = ref<globalThis.HTMLDivElement | null>(null)
const 右键菜单可见 = ref(false)
const 右键目标标签ID = ref('')
const 右键菜单X = ref(0)
const 右键菜单Y = ref(0)

const 可关闭其他标签 = computed(() => tabs.value.length > 1)
const 可关闭右侧标签 = computed(() => (
  tabs.value.findIndex((标签) => 标签.id === 右键目标标签ID.value) < tabs.value.length - 1
))

/**
 * 以「切换标签」的方式导航：写入一次性标记，
 * 让被 KeepAlive 保留的页面（如文章编辑页）不把这次跳转当成真正离开。
 */
async function 以标签切换方式导航(目标完整路径: string): Promise<boolean> {
  if (目标完整路径 === route.fullPath) {
    return true
  }
  设置控制台标签切换标记()
  try {
    const 导航失败 = await router.push(目标完整路径)
    return !导航失败
  } finally {
    清除控制台标签切换标记()
  }
}

async function 处理激活标签(标签: 控制台标签项) {
  关闭右键菜单()
  if (标签.path === route.path) {
    tabsStore.setActiveTab(标签.id)
    return
  }
  const 成功 = await 以标签切换方式导航(标签.fullPath)
  if (成功) {
    tabsStore.setActiveTab(标签.id)
  }
}

async function 处理新增标签() {
  关闭右键菜单()
  const 标签 = tabsStore.addTab()
  if (!标签) {
    return
  }
  if (标签.path === route.path) {
    tabsStore.setActiveTab(标签.id)
    return
  }
  const 成功 = await 以标签切换方式导航(标签.fullPath)
  if (成功) {
    tabsStore.setActiveTab(标签.id)
  }
}

/**
 * 关闭标签：激活标签需要先导航到目标页面，导航被守卫取消时标签保持不动。
 * 关闭激活标签属于真正离开当前页面，不写标签切换标记，仍会触发未保存确认。
 */
async function 处理关闭标签(标签ID: string, 事件?: globalThis.MouseEvent) {
  事件?.stopPropagation()
  关闭右键菜单()
  const 关闭结果 = tabsStore.planCloseTab(标签ID)
  if (!关闭结果) {
    return
  }

  if (关闭结果.是激活标签 && 关闭结果.目标完整路径 && 关闭结果.目标完整路径 !== route.fullPath) {
    开始控制台标签操作()
    try {
      const 导航失败 = await router.push(关闭结果.目标完整路径)
      if (导航失败) {
        return
      }
      tabsStore.applyCloseTab(标签ID)
    } finally {
      结束控制台标签操作()
    }
    tabsStore.syncRoute(route)
    return
  }

  tabsStore.applyCloseTab(标签ID)
}

function 处理中键关闭(事件: globalThis.MouseEvent, 标签: 控制台标签项) {
  if (事件.button !== 1) {
    return
  }
  事件.preventDefault()
  void 处理关闭标签(标签.id)
}

async function 处理刷新标签(标签ID: string) {
  关闭右键菜单()
  const 标签 = tabsStore.refreshTab(标签ID)
  if (!标签) {
    return
  }
  if (标签.path !== route.path) {
    const 成功 = await 以标签切换方式导航(标签.fullPath)
    if (成功) {
      tabsStore.setActiveTab(标签.id)
    }
  }
}

async function 处理关闭其他标签(标签ID: string) {
  关闭右键菜单()
  const 保留标签 = tabsStore.getTabById(标签ID)
  if (!保留标签) {
    return
  }

  if (保留标签.path !== route.path) {
    开始控制台标签操作()
    try {
      const 导航失败 = await router.push(保留标签.fullPath)
      if (导航失败) {
        return
      }
      tabsStore.keepOnlyTab(标签ID)
    } finally {
      结束控制台标签操作()
    }
    tabsStore.syncRoute(route)
    return
  }

  tabsStore.keepOnlyTab(标签ID)
}

async function 处理关闭右侧标签(标签ID: string) {
  关闭右键菜单()
  const 目标标签 = tabsStore.getTabById(标签ID)
  if (!目标标签) {
    return
  }

  if (tabsStore.closeRightTouchesActive(标签ID) && 目标标签.path !== route.path) {
    开始控制台标签操作()
    try {
      const 导航失败 = await router.push(目标标签.fullPath)
      if (导航失败) {
        return
      }
      tabsStore.closeTabsToRight(标签ID)
    } finally {
      结束控制台标签操作()
    }
    tabsStore.syncRoute(route)
    return
  }

  tabsStore.closeTabsToRight(标签ID)
}

function 打开右键菜单(事件: globalThis.MouseEvent, 标签ID: string) {
  事件.preventDefault()
  const 标签 = tabsStore.getTabById(标签ID)
  if (!标签) {
    return
  }
  右键目标标签ID.value = 标签ID
  右键菜单X.value = 事件.clientX
  右键菜单Y.value = 事件.clientY
  右键菜单可见.value = true
  window.requestAnimationFrame(() => 修正右键菜单位置())
}

function 关闭右键菜单() {
  右键菜单可见.value = false
}

/** 避免右键菜单位置超出视口。 */
function 修正右键菜单位置() {
  const 菜单 = 右键菜单元素.value
  if (!菜单) {
    return
  }
  const 边距 = 8
  右键菜单X.value = Math.min(右键菜单X.value, window.innerWidth - 菜单.offsetWidth - 边距)
  右键菜单Y.value = Math.min(右键菜单Y.value, window.innerHeight - 菜单.offsetHeight - 边距)
  右键菜单X.value = Math.max(边距, 右键菜单X.value)
  右键菜单Y.value = Math.max(边距, 右键菜单Y.value)
}

function 处理文档指针按下(事件: globalThis.PointerEvent) {
  const 目标节点 = 事件.target
  if (目标节点 instanceof globalThis.Node && 右键菜单元素.value?.contains(目标节点)) {
    return
  }
  关闭右键菜单()
}

function 处理文档按键(事件: globalThis.KeyboardEvent) {
  if (事件.key === 'Escape') {
    关闭右键菜单()
  }
}

watch(右键菜单可见, (可见) => {
  if (!可见) {
    document.removeEventListener('pointerdown', 处理文档指针按下)
    document.removeEventListener('keydown', 处理文档按键)
    window.removeEventListener('blur', 关闭右键菜单)
    window.removeEventListener('resize', 关闭右键菜单)
    return
  }
  document.addEventListener('pointerdown', 处理文档指针按下)
  document.addEventListener('keydown', 处理文档按键)
  window.addEventListener('blur', 关闭右键菜单)
  window.addEventListener('resize', 关闭右键菜单)
})

/** 激活标签变化后，把对应标签滚动到可视区域内。 */
watch(activeTabId, async () => {
  await nextTick()
  const 滚动容器 = 标签滚动容器.value
  if (!滚动容器) {
    return
  }
  const 激活标签元素 = 滚动容器.querySelector<globalThis.HTMLElement>('.dashboard-tabbar__tab.is-active')
  激活标签元素?.scrollIntoView({ block: 'nearest', inline: 'nearest' })
})

onBeforeUnmount(() => {
  关闭右键菜单()
  document.removeEventListener('pointerdown', 处理文档指针按下)
  document.removeEventListener('keydown', 处理文档按键)
  window.removeEventListener('blur', 关闭右键菜单)
  window.removeEventListener('resize', 关闭右键菜单)
})
</script>

<template>
  <div class="dashboard-tabbar" role="tablist" aria-label="后台页面标签">
    <div ref="标签滚动容器" class="dashboard-tabbar__scroller">
      <button
        v-for="标签 in tabs"
        :key="标签.id"
        type="button"
        role="tab"
        class="dashboard-tabbar__tab"
        :class="{ 'is-active': 标签.id === activeTabId }"
        :aria-selected="标签.id === activeTabId"
        :title="标签.title"
        @click="处理激活标签(标签)"
        @auxclick="处理中键关闭($event, 标签)"
        @contextmenu="打开右键菜单($event, 标签.id)"
      >
        <span class="dashboard-tabbar__label">{{ 标签.title }}</span>
        <span
          class="dashboard-tabbar__close"
          role="button"
          :aria-label="`关闭${标签.title}标签`"
          title="关闭标签"
          @click.stop="处理关闭标签(标签.id, $event)"
        >
          <ElIcon><Close /></ElIcon>
        </span>
      </button>
    </div>

    <button
      type="button"
      class="dashboard-tabbar__add"
      aria-label="新建标签页"
      title="新建标签页"
      @click="处理新增标签"
    >
      <ElIcon><Plus /></ElIcon>
    </button>

    <Teleport to="body">
      <Transition name="dashboard-tabbar-menu">
        <div
          v-if="右键菜单可见"
          ref="右键菜单元素"
          class="dashboard-tabbar__context-menu"
          :style="{ left: `${右键菜单X}px`, top: `${右键菜单Y}px` }"
          @contextmenu.prevent
        >
          <button
            type="button"
            class="dashboard-tabbar__context-item"
            @click="处理刷新标签(右键目标标签ID)"
          >
            刷新当前标签
          </button>
          <button
            type="button"
            class="dashboard-tabbar__context-item"
            @click="处理关闭标签(右键目标标签ID)"
          >
            关闭当前标签
          </button>
          <button
            type="button"
            class="dashboard-tabbar__context-item"
            :disabled="!可关闭其他标签"
            @click="处理关闭其他标签(右键目标标签ID)"
          >
            关闭其他标签
          </button>
          <button
            type="button"
            class="dashboard-tabbar__context-item"
            :disabled="!可关闭右侧标签"
            @click="处理关闭右侧标签(右键目标标签ID)"
          >
            关闭右侧标签
          </button>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
/* 参考 VS Code：标签条贴边、无外层内边距，标签为直角且彼此紧挨 */
.dashboard-tabbar {
  display: flex;
  align-items: stretch;
  gap: 0;
  flex: 0 0 auto;
  height: 38px;
  padding: 0;
  box-sizing: border-box;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--bg-secondary);
}

.dashboard-tabbar__scroller {
  display: flex;
  align-items: stretch;
  gap: 0;
  flex: 1;
  min-width: 0;
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.dashboard-tabbar__scroller::-webkit-scrollbar {
  display: none;
}

.dashboard-tabbar__tab {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
  max-width: 220px;
  height: 100%;
  padding: 0 6px 0 14px;
  border: none;
  border-right: 1px solid var(--el-border-color-lighter);
  border-radius: 0;
  background: transparent;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  outline: none;
  transition:
    color 0.18s ease,
    background-color 0.18s ease,
    border-color 0.18s ease;
}

/* 激活标签顶部高亮：整条贴边，与 VS Code 的选中标识一致 */
.dashboard-tabbar__tab::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: transparent;
  transition: background-color 0.18s ease;
}

.dashboard-tabbar__tab:hover {
  color: var(--el-text-color-primary);
  background: color-mix(in srgb, var(--el-bg-color) 82%, transparent);
}

.dashboard-tabbar__tab.is-active {
  color: var(--el-color-primary);
  background: var(--el-bg-color);
  box-shadow: none;
}

.dashboard-tabbar__tab.is-active::before {
  background: var(--el-color-primary);
}

.dashboard-tabbar__tab:focus-visible {
  background: var(--el-fill-color-light);
}

.dashboard-tabbar__label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dashboard-tabbar__close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  width: 16px;
  height: 16px;
  border-radius: 4px;
  color: var(--el-text-color-secondary);
  opacity: 0;
  transition:
    opacity 0.18s ease,
    color 0.18s ease,
    background-color 0.18s ease;
}

.dashboard-tabbar__close :deep(svg) {
  width: 10px;
  height: 10px;
}

.dashboard-tabbar__tab:hover .dashboard-tabbar__close,
.dashboard-tabbar__tab.is-active .dashboard-tabbar__close {
  opacity: 1;
}

.dashboard-tabbar__close:hover {
  color: var(--el-text-color-primary);
  background: var(--el-fill-color-darker);
}

.dashboard-tabbar__add {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  align-self: center;
  width: 28px;
  height: 28px;
  margin: 0 8px;
  padding: 0;
  border: none;
  border-radius: 0;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  outline: none;
  transition:
    color 0.18s ease,
    background-color 0.18s ease;
}

.dashboard-tabbar__add:hover {
  color: var(--el-color-primary);
  background: var(--el-fill-color-light);
}

.dashboard-tabbar__add :deep(svg) {
  width: 14px;
  height: 14px;
}

.dashboard-tabbar__context-menu {
  position: fixed;
  z-index: 4200;
  width: max-content;
  max-width: calc(100vw - 16px);
  padding: 6px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  background: var(--el-bg-color-overlay);
  box-shadow:
    0 18px 40px rgba(15, 23, 42, 0.16),
    0 4px 12px rgba(15, 23, 42, 0.1);
  backdrop-filter: blur(18px) saturate(160%);
}

.dashboard-tabbar__context-item {
  display: block;
  width: 100%;
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--el-text-color-primary);
  text-align: left;
  font-size: 13px;
  white-space: nowrap;
  cursor: pointer;
  transition:
    color 0.18s ease,
    background-color 0.18s ease;
}

.dashboard-tabbar__context-item:hover {
  color: var(--el-color-primary);
  background: var(--el-fill-color-light);
}

.dashboard-tabbar__context-item:disabled {
  color: var(--el-text-color-disabled);
  background: transparent;
  cursor: not-allowed;
}

.dashboard-tabbar-menu-enter-active,
.dashboard-tabbar-menu-leave-active {
  transition:
    opacity 0.16s ease,
    transform 0.16s ease;
}

.dashboard-tabbar-menu-enter-from,
.dashboard-tabbar-menu-leave-to {
  opacity: 0;
  transform: translateY(4px) scale(0.98);
}

@media (max-width: 768px) {
  .dashboard-tabbar__tab {
    max-width: 150px;
    padding: 0 4px 0 10px;
  }

  .dashboard-tabbar__add {
    margin: 0 4px;
  }
}
</style>
