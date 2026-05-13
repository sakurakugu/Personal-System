<script setup lang="ts">
import { Close, Refresh, Open } from '@element-plus/icons-vue'
import { ElButton, ElCard, ElEmpty, ElMessage, ElTag } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { getConfiguredActiveBaseUrl } from '@personal-system/api'
import { useAuthStore } from '@personal-system/domain/auth'
import { useTodoStore } from '@personal-system/domain/todos'
import { closeDesktopWidgetWindow, openDesktopMainWindow } from '@/shared/window-manager'
import { fetchPublicWidgetSummary } from '@/shared/widget-summary'

const todoStore = useTodoStore()
const auth = useAuthStore()
const loading = ref(false)

const activeTodos = computed(() => todoStore.todos.filter((todo) => !todo.is_deleted))
const todoCount = computed(() => activeTodos.value.filter((todo) => todo.status === 'todo').length)
const doneCount = computed(() => activeTodos.value.filter((todo) => todo.status === 'done').length)
const pinnedCount = computed(() => activeTodos.value.filter((todo) => todo.is_pinned).length)
const overdueCount = computed(() => activeTodos.value.filter((todo) => todo.status === 'todo' && todo.end_date && todo.end_date < new Date().toISOString().slice(0, 10)).length)

const upcomingTodos = computed(() => [...activeTodos.value]
  .filter((todo) => todo.status === 'todo')
  .sort((left, right) => {
    if (left.is_pinned !== right.is_pinned) return left.is_pinned ? -1 : 1
    const leftDate = left.end_date ?? left.created_at
    const rightDate = right.end_date ?? right.created_at
    return String(leftDate).localeCompare(String(rightDate))
  })
  .slice(0, 5))

function formatEndDate(value: string | null) {
  if (!value) {
    return '无截止日期'
  }
  return value.slice(0, 10)
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

async function handleOpenMainWindow() {
  try {
    await openDesktopMainWindow()
  } catch (error) {
    console.error('打开主窗口失败', error)
    ElMessage.error('打开主窗口失败')
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

onMounted(() => {
  void loadTodos()
})
</script>

<template>
  <div class="widget-page">
    <ElCard class="widget-shell" shadow="never">
      <div class="widget-header">
        <div>
          <p class="widget-kicker">Personal System</p>
          <h1>桌面小工具</h1>
          <p class="widget-desc">固定在桌面上的轻量待办面板。</p>
        </div>
        <div class="widget-actions">
          <ElButton :icon="Refresh" circle plain @click="handleRefresh" />
          <ElButton type="primary" :icon="Open" @click="handleOpenMainWindow">打开主窗口</ElButton>
          <ElButton :icon="Close" circle plain @click="handleCloseWindow" />
        </div>
      </div>

      <div class="widget-stats">
        <div class="stat-card">
          <span>待办</span>
          <strong>{{ todoCount }}</strong>
        </div>
        <div class="stat-card">
          <span>完成</span>
          <strong>{{ doneCount }}</strong>
        </div>
        <div class="stat-card">
          <span>置顶</span>
          <strong>{{ pinnedCount }}</strong>
        </div>
        <div class="stat-card stat-card--warn">
          <span>逾期</span>
          <strong>{{ overdueCount }}</strong>
        </div>
      </div>

      <div class="widget-list">
        <div class="widget-list__header">
          <h2>最近待办</h2>
          <ElTag type="info" effect="plain">{{ upcomingTodos.length }} 条</ElTag>
        </div>

        <ElEmpty v-if="!loading && upcomingTodos.length === 0" description="暂无待办" />

        <div v-else class="todo-list">
          <article v-for="todo in upcomingTodos" :key="todo.id" class="todo-item">
            <div class="todo-item__main">
              <strong>{{ todo.title }}</strong>
              <p>{{ formatEndDate(todo.end_date) }}</p>
            </div>
            <ElTag v-if="todo.is_pinned" type="warning" effect="plain">置顶</ElTag>
          </article>
        </div>
      </div>
    </ElCard>
  </div>
</template>

<style scoped>
.widget-page {
  height: 100vh;
  padding: 14px;
  background:
    radial-gradient(circle at top, color-mix(in srgb, var(--desktop-accent) 18%, transparent), transparent 42%),
    linear-gradient(180deg, color-mix(in srgb, var(--desktop-bg) 92%, #ffffff 8%), var(--desktop-bg));
}

.widget-shell {
  height: 100%;
  border: none;
  border-radius: 22px;
  background: color-mix(in srgb, var(--desktop-panel) 96%, #ffffff 4%);
}

.widget-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.widget-kicker,
.widget-desc,
.todo-item__main p {
  margin: 0;
  color: var(--desktop-text-muted);
}

.widget-header h1 {
  margin: 4px 0 8px;
  font-size: 26px;
}

.widget-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.widget-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 18px;
}

.stat-card {
  padding: 14px;
  border-radius: 18px;
  background: color-mix(in srgb, var(--desktop-hover) 72%, transparent);
}

.stat-card span {
  display: block;
  font-size: 12px;
  color: var(--desktop-text-muted);
}

.stat-card strong {
  display: block;
  margin-top: 6px;
  font-size: 24px;
}

.stat-card--warn strong {
  color: var(--el-color-danger);
}

.widget-list {
  margin-top: 18px;
}

.widget-list__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.widget-list__header h2 {
  margin: 0;
  font-size: 16px;
}

.todo-list {
  display: grid;
  gap: 10px;
}

.todo-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--desktop-hover) 58%, transparent);
}

.todo-item__main {
  min-width: 0;
}

.todo-item__main strong,
.todo-item__main p {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 480px) {
  .widget-header {
    flex-direction: column;
  }

  .widget-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
