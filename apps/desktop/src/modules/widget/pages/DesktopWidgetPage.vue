<script setup lang="ts">
import { useThemeStore } from '@/shared/stores/theme'
import { fetchPublicWidgetSummary } from '@/shared/widget-summary'
import {
  closeDesktopWidgetWindow,
  getDesktopWidgetWindowState,
  onDesktopWidgetWindowStateChange,
  openDesktopMainWindow,
  setDesktopWidgetWindowContentHeight,
  setDesktopWidgetWindowState,
} from '@/shared/window-manager'
import { Close, Refresh, RefreshLeft } from '@element-plus/icons-vue'
import { Icon } from '@iconify/vue'
import { getConfiguredActiveBaseUrl } from '@personal-system/api'
import { useAuthStore } from '@personal-system/domain/auth'
import { useTodoStore } from '@personal-system/domain/todos'
import { GlassRangeSlider, ThemeHuePanel } from '@personal-system/ui'
import { ElButton, ElEmpty, ElIcon, ElInput, ElMessage, ElSwitch, ElTag } from 'element-plus'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const todoStore = useTodoStore()
const auth = useAuthStore()
const theme = useThemeStore()

const loading = ref(false)
const widgetAlwaysOnTop = ref(true)
const widgetMovable = ref(false)
const pinLongPressing = ref(false)
const settingWidgetState = ref(false)
const creatingTodo = ref(false)
const todoDraft = ref('')
const todoListExpanded = ref(true)
const activeUtilityPanel = ref<'none' | 'settings' | 'add'>('none')
const widgetContentElement = ref<globalThis.HTMLElement | null>(null)
const widgetSurfaceOpacity = ref(100)
const widgetShowCloseButton = ref(true)
const pinLongPressDuration = 450
const defaultWidgetSurfaceOpacity = 100
let pinLongPressTimer: number | null = null
let widgetHeightObserver: globalThis.ResizeObserver | null = null
let widgetHeightSyncFrame: number | null = null
let lastSyncedWidgetHeight = 0
let removeWidgetStateListener = () => {}
let widgetSurfaceOpacitySyncTimer: number | null = null

const activeTodos = computed(() => todoStore.todos.filter((todo) => !todo.is_deleted))
const pinButtonIcon = computed(() => 'mdi:pin')
const pinButtonIconClass = computed(() => ({
  'pin-button__icon--movable': widgetMovable.value,
}))
const pinButtonIconShellClass = computed(() => ({
  'pin-button__icon-shell--unpinned': !widgetAlwaysOnTop.value,
}))
const pinButtonTitle = computed(() => {
  const movableText = widgetMovable.value ? '当前允许移动，长按后锁定位置' : '当前禁止移动，长按后允许移动'
  const alwaysOnTopText = widgetAlwaysOnTop.value ? '点击后取消置顶' : '点击后置顶'
  return `${movableText}；${alwaysOnTopText}`
})
const todoListButtonTitle = computed(() => (todoListExpanded.value ? '收起待办列表' : '展开待办列表'))
const widgetSettingsButtonTitle = computed(() => (activeUtilityPanel.value === 'settings' ? '收起卡片设置' : '打开卡片设置'))
const widgetSurfaceOpaque = computed(() => widgetSurfaceOpacity.value >= 100)
const widgetSurfaceBackground = computed(() => {
  if (widgetSurfaceOpaque.value) {
    return theme.isDark ? 'rgb(15, 23, 42)' : 'rgb(255, 255, 255)'
  }
  return `color-mix(in srgb, var(--desktop-panel) ${widgetSurfaceOpacity.value}%, transparent)`
})
const orderedTodos = computed(() => [...activeTodos.value]
  .filter((todo) => todo.status === 'todo')
  .sort((left, right) => {
    if (left.is_pinned !== right.is_pinned) return left.is_pinned ? -1 : 1
    const leftDate = left.end_date ?? left.created_at
    const rightDate = right.end_date ?? right.created_at
    return String(leftDate).localeCompare(String(rightDate))
  }))

function normalizeOpacity(value: number) {
  if (!Number.isFinite(value)) {
    return 100
  }
  return Math.max(50, Math.min(100, Math.round(value)))
}

function formatEndDate(value: string | null) {
  if (!value) {
    return '无截止日期'
  }
  return value.slice(0, 10)
}

function isOverdue(value: string | null) {
  return Boolean(value && value < new Date().toISOString().slice(0, 10))
}

async function loadTodos() {
  loading.value = true
  try {
    if (auth.isAuthenticated) {
      await todoStore.fetchTodos()
      return
    }
    const summary = await fetchPublicWidgetSummary({
      apiBaseUrl: getConfiguredActiveBaseUrl(),
    })
    todoStore.todos = summary.items.map((item) => ({
      id: String(item.id),
      title: item.title,
      description: null,
      status: 'todo',
      importance: item.importance,
      urgency: item.urgency,
      start_date: null,
      end_date: item.end_date,
      is_pinned: item.is_pinned,
      is_deleted: false,
      deleted_at: null,
      tags: null,
      recurrence_type: 'none',
      recurrence_interval: 1,
      recurrence_count: 0,
      times_per_interval: 1,
      interval_progress: 0,
      progress_reset_at: null,
      created_at: item.end_date ?? new Date().toISOString(),
      updated_at: item.end_date ?? new Date().toISOString(),
    }))
  } catch (error) {
    console.error('加载待办失败', error)
    ElMessage.error('加载待办失败')
  } finally {
    loading.value = false
  }
}

async function createTodo() {
  const title = todoDraft.value.trim()
  if (!title) {
    ElMessage.warning('请输入待办内容')
    return
  }
  if (!auth.isAuthenticated) {
    ElMessage.warning('公开小工具模式下暂不支持新增待办')
    return
  }

  creatingTodo.value = true
  try {
    await todoStore.addTodo({
      title,
      importance: 0,
      urgency: 0,
      recurrence_type: 'none',
      recurrence_interval: 1,
      recurrence_count: 0,
      times_per_interval: 1,
    })
    todoDraft.value = ''
    activeUtilityPanel.value = 'none'
    todoListExpanded.value = true
    ElMessage.success('已添加待办')
  } catch (error) {
    console.error('新增待办失败', error)
    ElMessage.error('新增待办失败')
  } finally {
    creatingTodo.value = false
  }
}

async function handleToggleComplete(id: string) {
  if (!auth.isAuthenticated) {
    ElMessage.warning('公开小工具模式下暂不支持修改待办')
    return
  }

  try {
    await todoStore.toggleComplete(id)
  } catch (error) {
    console.error('更新待办状态失败', error)
    ElMessage.error('更新待办状态失败')
  }
}

async function handleTogglePin(id: string) {
  if (!auth.isAuthenticated) {
    ElMessage.warning('公开小工具模式下暂不支持修改待办')
    return
  }

  try {
    await todoStore.togglePin(id)
  } catch (error) {
    console.error('更新置顶状态失败', error)
    ElMessage.error('更新置顶状态失败')
  }
}

function toggleSection(section: 'list' | 'settings' | 'add') {
  if (section === 'list') {
    todoListExpanded.value = !todoListExpanded.value
    return
  }
  if (activeUtilityPanel.value === section) {
    activeUtilityPanel.value = 'none'
    return
  }
  activeUtilityPanel.value = section
}

async function syncWidgetState() {
  try {
    const state = await getDesktopWidgetWindowState()
    widgetAlwaysOnTop.value = state.alwaysOnTop
    widgetMovable.value = state.movable
    widgetSurfaceOpacity.value = normalizeOpacity(state.surfaceOpacity)
    widgetShowCloseButton.value = state.showCloseButton
  } catch (error) {
    console.error('读取小工具窗口状态失败', error)
  }
}

async function updateWidgetState(payload: {
  alwaysOnTop?: boolean
  movable?: boolean
  surfaceOpacity?: number
  showCloseButton?: boolean
}) {
  if (settingWidgetState.value) {
    return
  }

  settingWidgetState.value = true
  try {
    const state = await setDesktopWidgetWindowState(payload)
    widgetAlwaysOnTop.value = state.alwaysOnTop
    widgetMovable.value = state.movable
    widgetSurfaceOpacity.value = normalizeOpacity(state.surfaceOpacity)
    widgetShowCloseButton.value = state.showCloseButton
  } catch (error) {
    console.error('更新小工具窗口状态失败', error)
    ElMessage.error('更新小工具窗口状态失败')
  } finally {
    settingWidgetState.value = false
  }
}

function clearPinLongPressTimer() {
  if (!pinLongPressTimer) {
    return
  }

  window.clearTimeout(pinLongPressTimer)
  pinLongPressTimer = null
}

function beginPinLongPress() {
  pinLongPressing.value = false
  clearPinLongPressTimer()
  pinLongPressTimer = window.setTimeout(() => {
    pinLongPressing.value = true
    void updateWidgetState({
      movable: !widgetMovable.value,
    })
  }, pinLongPressDuration)
}

function cancelPinLongPress() {
  clearPinLongPressTimer()
}

async function handlePinButtonClick() {
  if (pinLongPressing.value) {
    pinLongPressing.value = false
    return
  }

  await updateWidgetState({
    alwaysOnTop: !widgetAlwaysOnTop.value,
  })
}

async function handleOpenMainWindow() {
  try {
    await openDesktopMainWindow()
  } catch (error) {
    console.error('显示主窗口失败', error)
    ElMessage.error('显示主窗口失败')
  }
}

async function handleCloseWindow() {
  try {
    await closeDesktopWidgetWindow()
  } catch (error) {
    console.error('关闭小工具失败', error)
    ElMessage.error('关闭小工具失败')
  }
}

async function handleRefresh() {
  await loadTodos()
}

function handleToggleSettingsPanel() {
  toggleSection('settings')
}

function scheduleSurfaceOpacitySync() {
  if (widgetSurfaceOpacitySyncTimer !== null) {
    window.clearTimeout(widgetSurfaceOpacitySyncTimer)
  }

  widgetSurfaceOpacitySyncTimer = window.setTimeout(() => {
    widgetSurfaceOpacitySyncTimer = null
    void updateWidgetState({
      surfaceOpacity: widgetSurfaceOpacity.value,
    })
  }, 120)
}

function resetWidgetSurfaceOpacity() {
  widgetSurfaceOpacity.value = defaultWidgetSurfaceOpacity
}

async function syncWidgetWindowHeight() {
  await nextTick()
  const element = widgetContentElement.value
  if (!element) {
    return
  }

  const rectHeight = Math.ceil(element.getBoundingClientRect().height)
  const scrollHeight = Math.ceil(element.scrollHeight)
  const offsetHeight = Math.ceil(element.offsetHeight)
  const nextHeight = Math.max(rectHeight, scrollHeight, offsetHeight)
  if (nextHeight <= 0 || nextHeight === lastSyncedWidgetHeight) {
    return
  }

  lastSyncedWidgetHeight = nextHeight
  await setDesktopWidgetWindowContentHeight(nextHeight)
}

function scheduleWidgetWindowHeightSync() {
  if (widgetHeightSyncFrame !== null) {
    window.cancelAnimationFrame(widgetHeightSyncFrame)
  }

  widgetHeightSyncFrame = window.requestAnimationFrame(() => {
    widgetHeightSyncFrame = null
    void syncWidgetWindowHeight()
  })
}

onMounted(() => {
  removeWidgetStateListener = onDesktopWidgetWindowStateChange((payload) => {
    widgetAlwaysOnTop.value = payload.alwaysOnTop
    widgetMovable.value = payload.movable
    widgetSurfaceOpacity.value = normalizeOpacity(payload.surfaceOpacity)
    widgetShowCloseButton.value = payload.showCloseButton
  })
  widgetHeightObserver = new window.ResizeObserver(() => {
    scheduleWidgetWindowHeightSync()
  })
  if (widgetContentElement.value) {
    widgetHeightObserver.observe(widgetContentElement.value)
  }
  void syncWidgetState()
  void loadTodos()
  scheduleWidgetWindowHeightSync()
})

onBeforeUnmount(() => {
  clearPinLongPressTimer()
  if (widgetSurfaceOpacitySyncTimer !== null) {
    window.clearTimeout(widgetSurfaceOpacitySyncTimer)
    widgetSurfaceOpacitySyncTimer = null
  }
  widgetHeightObserver?.disconnect()
  widgetHeightObserver = null
  if (widgetHeightSyncFrame !== null) {
    window.cancelAnimationFrame(widgetHeightSyncFrame)
    widgetHeightSyncFrame = null
  }
  removeWidgetStateListener()
})

watch(
  [
    loading,
    todoListExpanded,
    activeUtilityPanel,
    creatingTodo,
    todoDraft,
    orderedTodos,
  ],
  () => {
    scheduleWidgetWindowHeightSync()
  },
  { deep: true },
)

watch(widgetSurfaceOpacity, (value) => {
  const normalized = normalizeOpacity(value)
  if (normalized !== value) {
    widgetSurfaceOpacity.value = normalized
    return
  }
  scheduleSurfaceOpacitySync()
})

watch(widgetShowCloseButton, (value) => {
  void updateWidgetState({
    showCloseButton: value,
  })
})
</script>

<template>
  <div class="widget-page">
    <div
      ref="widgetContentElement"
      class="widget-shell"
      :class="{
        'widget-shell--movable': widgetMovable,
        'widget-shell--dark': theme.isDark,
        'widget-shell--opaque': widgetSurfaceOpaque,
      }"
      :style="{
        '--widget-surface-background': widgetSurfaceBackground,
      }"
    >
      <header class="widget-header">
        <div class="widget-header-card" :class="{ 'widget-header-card--drag': widgetMovable }">
          <div class="widget-header-card__inner">
            <div class="widget-header-brand widget-no-drag">
              <button
                class="widget-header-brand__icon-button"
                type="button"
                :title="widgetSettingsButtonTitle"
                :class="{ 'widget-header-brand__icon-button--active': activeUtilityPanel === 'settings' }"
                @click="handleToggleSettingsPanel"
              >
                <span class="widget-header-brand__icon-shell">
                  <Icon icon="mdi:checkbox-marked-circle-auto-outline" class="widget-header-brand__icon" />
                </span>
              </button>
              <button
                class="widget-header-brand__text-button"
                type="button"
                :title="todoListButtonTitle"
                @click="toggleSection('list')"
              >
                <span class="widget-header-brand__text" :class="{ 'widget-header-brand__text--active': todoListExpanded }">待办事项</span>
              </button>
            </div>
            <div class="widget-actions widget-no-drag">
              <ElButton
                class="widget-icon-button pin-button"
                plain
                :title="pinButtonTitle"
                :disabled="settingWidgetState"
                @mousedown="beginPinLongPress"
                @mouseup="cancelPinLongPress"
                @mouseleave="cancelPinLongPress"
                @touchstart.passive="beginPinLongPress"
                @touchend="cancelPinLongPress"
                @touchcancel="cancelPinLongPress"
                @click="handlePinButtonClick"
              >
                <span class="pin-button__icon-shell" :class="pinButtonIconShellClass">
                  <Icon :icon="pinButtonIcon" class="pin-button__icon" :class="pinButtonIconClass" />
                </span>
              </ElButton>
              <ElButton class="widget-icon-button widget-action-button" plain title="打开主窗口" @click="handleOpenMainWindow">
                <Icon icon="mdi:application-outline" />
              </ElButton>
              <ElButton v-if="widgetShowCloseButton" class="widget-icon-button" :icon="Close" plain @click="handleCloseWindow" />
            </div>
          </div>
        </div>
      </header>

      <section v-show="activeUtilityPanel === 'settings'" class="widget-panel widget-no-drag">
        <div class="panel-header panel-header--static">
          <div class="panel-header__left">
            <h3 class="panel-header__title">卡片设置</h3>
          </div>
        </div>

        <div class="panel-body panel-body--settings">
          <div class="setting-section">
            <div class="setting-item setting-item--switch">
              <div class="setting-item__header">
                <strong>显示顶部关闭按钮</strong>
                <span>{{ widgetShowCloseButton ? '开启' : '关闭' }}</span>
              </div>
              <ElSwitch v-model="widgetShowCloseButton" />
            </div>
          </div>

          <div class="settings-divider" role="separator" />

          <div class="setting-section setting-section--plain">
            <div class="setting-item__header setting-item__header--rich">
              <div class="setting-item__title">
                <span>背景透明度</span>
                <button
                  class="setting-reset"
                  :class="{ 'setting-reset--hidden': widgetSurfaceOpacity === defaultWidgetSurfaceOpacity }"
                  type="button"
                  @click="resetWidgetSurfaceOpacity"
                >
                  <ElIcon :size="12"><RefreshLeft /></ElIcon>
                </button>
              </div>
              <div class="setting-item__meta">
                <span class="setting-item__value">{{ widgetSurfaceOpacity }}%</span>
              </div>
            </div>
            <GlassRangeSlider
              :model-value="widgetSurfaceOpacity"
              :min="50"
              :max="100"
              :step="1"
              aria-label="卡片背景透明度"
              @update:model-value="(value) => widgetSurfaceOpacity = value"
            />
          </div>

          <div class="settings-divider" role="separator" />

          <div class="setting-section">
            <ThemeHuePanel
              :model-value="theme.hue"
              :default-value="theme.defaultHue"
              @update:model-value="theme.setHue"
            />
          </div>
        </div>
      </section>

      <section v-show="todoListExpanded" class="widget-panel widget-no-drag widget-panel--list">
        <div class="panel-header panel-header--static">
          <div class="panel-header__left">
            <h3 class="panel-header__title">全部待办</h3>
            <ElTag class="widget-count-tag" effect="plain">{{ orderedTodos.length }}</ElTag>
          </div>
          <div class="panel-header__right">
            <ElButton class="widget-icon-button" :icon="Refresh" plain @click="handleRefresh" />
            <ElButton
              class="widget-icon-button widget-action-button"
              plain
              title="新建待办"
              :class="{ 'widget-action-button--active': activeUtilityPanel === 'add' }"
              @click="toggleSection('add')"
            >
              <Icon icon="mdi:playlist-plus" />
            </ElButton>
          </div>
        </div>

        <div class="panel-body">
          <ElEmpty v-if="!loading && orderedTodos.length === 0" description="暂无待办" />

          <div v-else class="todo-list">
            <article v-for="todo in orderedTodos" :key="todo.id" class="todo-item">
              <button class="todo-check" type="button" :title="todo.status === 'done' ? '标记为未完成' : '标记为完成'" @click="handleToggleComplete(todo.id)">
                <Icon :icon="todo.status === 'done' ? 'mdi:checkbox-marked-circle' : 'mdi:checkbox-blank-circle-outline'" />
              </button>

              <div class="todo-item__main">
                <strong>{{ todo.title }}</strong>
                <p :class="{ 'todo-item__meta--warn': isOverdue(todo.end_date) }">
                  {{ formatEndDate(todo.end_date) }}
                </p>
              </div>

              <button class="todo-pin" type="button" :title="todo.is_pinned ? '取消置顶' : '置顶'" @click="handleTogglePin(todo.id)">
                <Icon :icon="todo.is_pinned ? 'mdi:star' : 'mdi:star-outline'" />
              </button>
            </article>
          </div>
        </div>
      </section>

      <section v-show="activeUtilityPanel === 'add'" class="widget-panel widget-no-drag">
        <div class="panel-header panel-header--static">
          <div class="panel-header__left">
            <h3 class="panel-header__title">添加新待办</h3>
          </div>
        </div>

        <div class="panel-body">
          <div class="composer">
            <p class="composer__label">请输入待办内容</p>
            <ElInput
              v-model="todoDraft"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 5 }"
              resize="none"
              placeholder="例如：整理本周账单、补充一篇文章草稿"
            />
            <div class="composer__actions">
              <ElButton plain @click="todoDraft = ''">清空</ElButton>
              <ElButton type="primary" :loading="creatingTodo" @click="createTodo">确认添加</ElButton>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.widget-page {
  --widget-window-radius: 8px;
  --widget-surface-background: color-mix(in srgb, var(--desktop-panel) 100%, transparent);
  padding: 0;
  background: transparent;
  overflow: hidden;
  scrollbar-width: none;
  overscroll-behavior: none;
}

.widget-page::-webkit-scrollbar {
  display: none;
}

.widget-shell {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0;
  border-radius: 0;
  overflow: visible;
  background: transparent;
  border: none;
  box-shadow: none;
}

.widget-shell--dark {
  background: transparent;
}

.widget-header,
.widget-panel {
  position: relative;
  z-index: 1;
}

.widget-header {
  display: flex;
  justify-content: stretch;
  align-items: center;
  gap: 16px;
  padding: 0;
}

.widget-header-card {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  width: 100%;
  min-height: 46px;
  padding: 0 12px;
  border-radius: var(--widget-window-radius);
  border: none;
  background: var(--widget-surface-background);
  backdrop-filter: blur(10px);
}

.widget-shell--opaque .widget-header-card {
  backdrop-filter: none;
}

.widget-header-card--drag {
  -webkit-app-region: drag;
}

.widget-header-card__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0px;
  width: 100%;
  min-height: 0px;
}

.widget-header-brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  height: 34px;
  padding: 0;
  color: var(--desktop-text);
}

.widget-header-brand__icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
}

.widget-header-brand__icon-shell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--desktop-accent) 16%, transparent);
  color: var(--desktop-accent);
  flex-shrink: 0;
  transition: background-color 0.18s ease, transform 0.18s ease;
}

.widget-header-brand__icon-button--active .widget-header-brand__icon-shell {
  background: color-mix(in srgb, var(--desktop-accent) 28%, transparent);
  transform: scale(1.03);
}

.widget-header-brand__icon {
  font-size: 18px;
}

.widget-header-brand__text-button {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  height: 100%;
  padding: 0;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.widget-header-brand__text {
  display: inline-flex;
  align-items: center;
  height: 100%;
  padding: 0 10px;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.04em;
  white-space: nowrap;
  transition: background-color 0.18s ease;
}

.widget-header-brand__text--active {
  background: color-mix(in srgb, var(--desktop-accent) 10%, transparent);
}

.widget-no-drag {
  -webkit-app-region: no-drag;
}

.panel-header p,
.composer__label,
.setting-row p,
.todo-item__main p {
  margin: 0;
  color: var(--desktop-text-muted);
}

.widget-actions {
  display: flex;
  gap: 0;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.widget-icon-button {
  width: 34px;
  height: 34px;
  padding: 0;
}

.widget-actions :deep(.el-button) {
  border-color: color-mix(in srgb, var(--desktop-accent) 18%, var(--desktop-border));
  background: color-mix(in srgb, var(--desktop-accent) 8%, transparent);
  color: var(--desktop-text);
  border-radius: 8px;
}

.widget-actions :deep(.el-button + .el-button) {
  margin-left: 5px;
}

.widget-actions :deep(.el-button:hover) {
  border-color: color-mix(in srgb, var(--desktop-accent) 34%, var(--desktop-border));
  background: color-mix(in srgb, var(--desktop-accent) 14%, transparent);
}

.widget-action-button {
  font-size: 18px;
}

.widget-action-button--active {
  border-color: color-mix(in srgb, var(--desktop-accent) 34%, var(--desktop-border));
  background: color-mix(in srgb, var(--desktop-accent) 18%, transparent);
}

.pin-button {
  overflow: hidden;
}

.pin-button__icon-shell {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
}

.pin-button__icon {
  font-size: 18px;
  transition: transform 0.18s ease;
}

.pin-button__icon--movable {
  transform: rotate(35deg);
}

.pin-button__icon-shell::after {
  content: '';
  position: absolute;
  top: -1px;
  left: 8px;
  width: 1.5px;
  height: 20px;
  border-radius: 999px;
  background: currentcolor;
  opacity: 0;
  transform: rotate(-45deg);
  transform-origin: center;
  transition: opacity 0.18s ease;
  pointer-events: none;
}

.pin-button__icon-shell--unpinned::after {
  opacity: 0.92;
}

.widget-panel {
  border-radius: var(--widget-window-radius);
  border: none;
  background: var(--widget-surface-background);
  backdrop-filter: blur(10px);
}

.widget-shell--opaque .widget-panel {
  backdrop-filter: none;
}

.widget-panel--list {
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 16px 18px 8px 18px;
  border: none;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.panel-header--static {
  cursor: default;
}

.panel-header__left,
.panel-header__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.panel-header__right {
  gap: 0px;
}

.widget-count-tag {
  border-radius: 6px;
}

.panel-header__title {
  position: relative;
  margin: 0 0 0 16px;
  color: var(--desktop-text);
  font-size: 1.125rem;
  font-weight: 700;
  line-height: 1.4;
}

.panel-header__title::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -16px;
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--desktop-accent);
  transform: translateY(-50%);
}

.panel-header__arrow {
  font-size: 22px;
  color: var(--desktop-text-muted);
  transition: transform 0.18s ease;
}

.panel-header__arrow--expanded {
  transform: rotate(180deg);
}

.panel-body {
  padding: 0 16px 16px;
}

.panel-body--settings {
  display: grid;
  gap: 16px;
}

.settings-divider {
  height: 1px;
  background: color-mix(in srgb, var(--desktop-border) 84%, transparent);
}

.setting-section {
  display: grid;
  gap: 14px;
}

.setting-section--plain {
  gap: 14px;
  padding: 2px 2px 0;
}

.setting-item {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: var(--widget-window-radius);
  background: color-mix(in srgb, var(--desktop-accent) 18%, transparent);
}

.setting-item--slider {
  gap: 12px;
}

.setting-item--switch {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
}

.setting-item__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--desktop-text);
}

.setting-item__header--rich {
  align-items: flex-start;
}

.setting-item__title {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 12px;
  font-size: 18px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.9);
}

.setting-item__title::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -12px;
  width: 4px;
  height: 16px;
  border-radius: 4px;
  background: var(--desktop-accent);
  transform: translateY(-50%);
}

.setting-reset {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  border-radius: 6px;
  color: var(--desktop-accent);
  background: color-mix(in srgb, var(--desktop-accent) 12%, transparent);
  cursor: pointer;
  transition: opacity 0.2s, background-color 0.15s ease, transform 0.15s ease;
}

.setting-reset:hover {
  background: color-mix(in srgb, var(--desktop-accent) 18%, transparent);
}

.setting-reset:active {
  transform: scale(0.92);
}

.setting-reset--hidden {
  opacity: 0;
  pointer-events: none;
}

.setting-item__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.setting-item__value {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  height: 30px;
  padding: 0 10px;
  border-radius: 6px;
  color: var(--desktop-accent);
  font-size: 15px;
  font-weight: 700;
  background: color-mix(in srgb, var(--desktop-accent) 16%, white);
}

.setting-item__header strong {
  font-size: 16px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.88);
}

.setting-item__header > span {
  color: rgba(0, 0, 0, 0.7);
  font-size: 14px;
}

.widget-shell--dark .setting-item__title {
  color: rgba(255, 255, 255, 0.92);
}

.widget-shell--dark .setting-item__header strong {
  color: rgba(255, 255, 255, 0.9);
}

.widget-shell--dark .setting-item__header > span {
  color: rgba(255, 255, 255, 0.72);
}

.widget-shell--dark .setting-item__value {
  background: color-mix(in srgb, var(--desktop-accent) 18%, #0f172a);
}

.setting-item--slider :deep(.glass-range-slider) {
  width: 100%;
}

.todo-list {
  display: grid;
  gap: 10px;
}

.todo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: var(--widget-window-radius);
  background: color-mix(in srgb, var(--desktop-accent) 20%, transparent);
}

.todo-check,
.todo-pin {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: color-mix(in srgb, var(--desktop-accent) 14%, transparent);
  color: var(--desktop-accent);
  cursor: pointer;
}

.todo-item__main {
  min-width: 0;
  flex: 1;
}

.todo-item__main strong,
.todo-item__main p {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.todo-item__main strong {
  color: var(--desktop-text);
}

.todo-item__meta--warn {
  color: var(--el-color-danger);
}

.composer {
  display: grid;
  gap: 12px;
}

.composer__actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 480px) {
  .widget-page {
    padding: 0;
  }

  .widget-shell {
    padding: 0;
    border-radius: 0;
  }
}
</style>
