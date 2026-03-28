<script setup lang="ts">
/* global HTMLElement */
import { computed, onMounted, ref, watch } from 'vue'
import { ElEmpty, ElTag } from 'element-plus'
import { fetchTodoCompletionHistory } from '../../../features/todos/api'
import type { CompletionHistoryDay, CompletionHistoryItem, CompletionHistoryResponse } from '../../../features/todos/types'
import type { Todo } from '../../../stores/todo'
import BaseDialog from '../../../components/BaseDialog.vue'
import { getApiErrorMessage } from '../../../utils/api'

const props = defineProps<{
  todos: Todo[]
  multiSelectMode?: boolean
  selectedIds?: string[]
}>()

const emit = defineEmits<{
  (e: 'toggleComplete', todo: Todo): void
  (e: 'edit', todo: Todo): void
  (e: 'longPress', todo: Todo): void
  (e: 'toggleSelect', todo: Todo): void
}>()

interface DayStats {
  date: Date
  dateStr: string
  completedCount: number
  items: CompletionHistoryItem[]
  isToday: boolean
  isFuture: boolean
}

const today = new Date()
const currentYear = today.getFullYear()
const currentMonth = today.getMonth()
const startDate = computed(() => new Date(currentYear - 1, currentMonth, 1))
const endDate = computed(() => new Date(currentYear + 1, currentMonth + 1, 0))

const loading = ref(false)
const loadError = ref('')
const history = ref<CompletionHistoryResponse | null>(null)
const showDayDetail = ref(false)
const selectedDay = ref<DayStats | null>(null)
const heatmapContainerRef = ref<HTMLElement | null>(null)

function formatDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

async function loadHistory() {
  loading.value = true
  loadError.value = ''
  try {
    history.value = await fetchTodoCompletionHistory(
      formatDate(startDate.value),
      formatDate(endDate.value),
    )
  } catch (error) {
    loadError.value = getApiErrorMessage(error, '完成历史加载失败')
  } finally {
    loading.value = false
  }
}

watch(() => props.todos, loadHistory, { deep: true, immediate: true })

const historyMap = computed(() => {
  const mapped = new Map<string, CompletionHistoryDay>()
  history.value?.days.forEach(day => {
    mapped.set(day.date, day)
  })
  return mapped
})

const totalCompletedCount = computed(() => history.value?.total_completed_count ?? 0)
const maxCompletedCount = computed(() => Math.max(1, history.value?.max_completed_count ?? 0))

const days = computed(() => {
  const result: DayStats[] = []
  const start = new Date(startDate.value)
  const end = new Date(endDate.value)

  const startDay = start.getDay()
  const offset = startDay === 0 ? 6 : startDay - 1
  start.setDate(start.getDate() - offset)

  const current = new Date(start)
  const todayDate = new Date()
  todayDate.setHours(0, 0, 0, 0)

  while (current <= end) {
    const dateStr = formatDate(current)
    const historyDay = historyMap.value.get(dateStr)

    result.push({
      date: new Date(current),
      dateStr,
      completedCount: historyDay?.completed_count ?? 0,
      items: historyDay?.items ?? [],
      isToday: current.getTime() === todayDate.getTime(),
      isFuture: current > todayDate,
    })

    current.setDate(current.getDate() + 1)
  }

  return result
})

const weeksCount = computed(() => Math.ceil(days.value.length / 7))

const todayColumnIndex = computed(() => {
  const todayDate = new Date()
  todayDate.setHours(0, 0, 0, 0)

  for (let i = 0; i < days.value.length; i++) {
    if (days.value[i].date.getTime() === todayDate.getTime()) {
      return Math.floor(i / 7)
    }
  }
  return Math.floor(days.value.length / 14)
})

onMounted(() => {
  setTimeout(() => {
    if (!heatmapContainerRef.value) return
    const container = heatmapContainerRef.value
    const colWidth = 17
    const targetScrollLeft = todayColumnIndex.value * colWidth - container.clientWidth / 2 + colWidth / 2
    container.scrollTo({
      left: Math.max(0, targetScrollLeft),
      behavior: 'auto',
    })
  }, 100)
})

const yearLabels = computed(() => {
  const labels: Array<{ year: number; start: number; span: number }> = []
  let currentYearValue = -1
  let startCol = 1

  days.value.forEach((day, index) => {
    const year = day.date.getFullYear()
    const colIndex = Math.floor(index / 7) + 1

    if (year !== currentYearValue) {
      if (currentYearValue !== -1) {
        labels.push({
          year: currentYearValue,
          start: startCol,
          span: colIndex - startCol,
        })
      }
      currentYearValue = year
      startCol = colIndex
    }
  })

  if (currentYearValue !== -1) {
    labels.push({
      year: currentYearValue,
      start: startCol,
      span: weeksCount.value - startCol + 1,
    })
  }

  return labels
})

const monthLabels = computed(() => {
  const labels: Array<{ key: string; label: string; start: number; span: number; isEven: boolean }> = []
  let currentMonthValue = -1
  let currentYearValue = -1
  let startCol = 1
  const rawStart = new Date(currentYear - 1, currentMonth, 1)

  days.value.forEach((day, index) => {
    if (day.date.getTime() < rawStart.getTime()) {
      return
    }

    const month = day.date.getMonth()
    const year = day.date.getFullYear()
    const colIndex = Math.floor(index / 7) + 1
    if (month !== currentMonthValue || year !== currentYearValue) {
      if (currentMonthValue !== -1) {
        labels.push({
          key: `${currentYearValue}-${currentMonthValue}`,
          label: `${currentMonthValue + 1}月`,
          start: startCol,
          span: colIndex - startCol,
          isEven: (currentMonthValue + 1) % 2 === 0,
        })
      }
      currentMonthValue = month
      currentYearValue = year
      startCol = colIndex
    }
  })

  if (currentMonthValue !== -1) {
    labels.push({
      key: `${currentYearValue}-${currentMonthValue}`,
      label: `${currentMonthValue + 1}月`,
      start: startCol,
      span: weeksCount.value - startCol + 1,
      isEven: (currentMonthValue + 1) % 2 === 0,
    })
  }

  return labels
})

const currentTodoMap = computed(() => new Map(props.todos.map(todo => [todo.id, todo])))

function getCellClass(day: DayStats): Record<string, boolean> {
  const month = day.date.getMonth() + 1
  return {
    'is-today': day.isToday,
    'is-future': day.isFuture,
    'has-history': day.completedCount > 0,
    'is-even-month': month % 2 === 0 && day.completedCount === 0,
  }
}

function getCellColor(day: DayStats): string {
  const month = day.date.getMonth() + 1
  if (day.isFuture) {
    return month % 2 === 0 ? 'var(--heatmap-future-even)' : 'var(--heatmap-future-odd)'
  }
  if (day.completedCount <= 0) {
    return month % 2 === 0 ? 'var(--heatmap-empty-even)' : 'var(--heatmap-empty-odd)'
  }

  const ratio = day.completedCount / maxCompletedCount.value
  if (ratio >= 0.85) return 'var(--heatmap-level-4)'
  if (ratio >= 0.6) return 'var(--heatmap-level-3)'
  if (ratio >= 0.35) return 'var(--heatmap-level-2)'
  return 'var(--heatmap-level-1)'
}

function getTooltip(day: DayStats): string {
  if (day.completedCount <= 0) {
    return `${day.dateStr}\n无完成记录`
  }
  return `${day.dateStr}\n完成次数: ${day.completedCount}\n完成待办: ${day.items.length}`
}

function handleDayClick(day: DayStats) {
  if (day.completedCount <= 0) return
  selectedDay.value = day
  showDayDetail.value = true
}

function getCurrentTodo(item: CompletionHistoryItem): Todo | undefined {
  return currentTodoMap.value.get(item.todo_id)
}

function handleHistoryItemClick(item: CompletionHistoryItem) {
  const todo = getCurrentTodo(item)
  if (!todo) return
  if (props.multiSelectMode) {
    emit('toggleSelect', todo)
    return
  }
  emit('edit', todo)
}

function isSelected(id: string): boolean {
  return props.selectedIds?.includes(id) ?? false
}
</script>

<template>
  <div class="todo-heatmap">
    <div class="heatmap-header">
      <div class="heatmap-title">
        <h3>完成热力图</h3>
        <span class="heatmap-subtitle">按完成历史着色，回收站与永久删除记录都会保留</span>
      </div>
      <div class="legend">
        <div class="legend-item">
          <div class="legend-box none" />
          <span>无记录</span>
        </div>
        <div class="legend-item">
          <div class="legend-box level-1" />
          <span>较少</span>
        </div>
        <div class="legend-item">
          <div class="legend-box level-2" />
          <span>中等</span>
        </div>
        <div class="legend-item">
          <div class="legend-box level-3" />
          <span>较多</span>
        </div>
        <div class="legend-item">
          <div class="legend-box future" />
          <span>未来</span>
        </div>
      </div>
    </div>

    <div v-if="loadError" class="empty-state">
      <ElEmpty :description="loadError" />
    </div>

    <div v-else-if="!loading && totalCompletedCount === 0 && props.todos.length === 0" class="empty-state">
      <ElEmpty description="暂无待办或完成历史" />
    </div>

    <div v-else class="heatmap-wrapper">
      <div class="week-labels-fixed">
        <div class="week-label">一</div>
        <div class="week-label">二</div>
        <div class="week-label">三</div>
        <div class="week-label">四</div>
        <div class="week-label">五</div>
        <div class="week-label">六</div>
        <div class="week-label">日</div>
      </div>

      <div ref="heatmapContainerRef" class="heatmap-container">
        <div class="year-labels" :style="{ gridTemplateColumns: `repeat(${weeksCount}, 14px)` }">
          <div
            v-for="yearLabel in yearLabels"
            :key="yearLabel.year"
            class="year-label"
            :style="{ gridColumn: `${yearLabel.start} / span ${yearLabel.span}` }"
          >
            {{ yearLabel.year }}年
          </div>
        </div>

        <div class="month-labels" :style="{ gridTemplateColumns: `repeat(${weeksCount}, 14px)` }">
          <div
            v-for="month in monthLabels"
            :key="month.key"
            class="month-label"
            :class="{ 'is-even': month.isEven }"
            :style="{ gridColumn: `${month.start} / span ${month.span}` }"
          >
            {{ month.label }}
          </div>
        </div>

        <div class="days-grid" :style="{ gridTemplateColumns: `repeat(${weeksCount}, 14px)` }">
          <div
            v-for="day in days"
            :key="day.dateStr"
            class="day-cell"
            :class="getCellClass(day)"
            :style="{ backgroundColor: getCellColor(day) }"
            :title="getTooltip(day)"
            @click="handleDayClick(day)"
          />
        </div>
      </div>
    </div>

    <BaseDialog
      v-model="showDayDetail"
      :title="`${selectedDay?.dateStr} 完成记录`"
      width="560px"
    >
      <div v-if="selectedDay" class="day-detail">
        <div class="stats-summary">
          <ElTag type="success">完成次数: {{ selectedDay.completedCount }}</ElTag>
          <ElTag>完成待办: {{ selectedDay.items.length }}</ElTag>
        </div>

        <div class="history-list">
          <div
            v-for="item in selectedDay.items"
            :key="`${item.todo_id}-${item.title}`"
            class="history-item"
            :class="{ 'is-clickable': !!getCurrentTodo(item), 'is-selected': isSelected(item.todo_id) }"
            @click="handleHistoryItemClick(item)"
          >
            <div class="history-main">
              <div class="history-title">{{ item.title }}</div>
              <div class="history-meta">
                <ElTag size="small" type="success">完成 {{ item.completed_count }} 次</ElTag>
                <ElTag v-if="getCurrentTodo(item)" size="small">当前仍存在</ElTag>
                <ElTag v-else size="small" type="info">仅历史记录</ElTag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </BaseDialog>
  </div>
</template>

<style scoped>
.todo-heatmap {
  padding: 20px;
  border-radius: 8px;
  min-height: 200px;
  --heatmap-empty-odd: #ebedf0;
  --heatmap-empty-even: #f3f4f6;
  --heatmap-future-odd: #d1d5db;
  --heatmap-future-even: #e5e7eb;
  --heatmap-level-1: #9be9a8;
  --heatmap-level-2: #40c463;
  --heatmap-level-3: #30a14e;
  --heatmap-level-4: #216e39;
}

.dark .todo-heatmap {
  --heatmap-empty-odd: #2d333b;
  --heatmap-empty-even: #1f2937;
  --heatmap-future-odd: #4b5563;
  --heatmap-future-even: #374151;
  --heatmap-level-1: #1f6f4a;
  --heatmap-level-2: #238636;
  --heatmap-level-3: #2ea043;
  --heatmap-level-4: #3fb950;
}

.heatmap-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 12px;
  flex-wrap: wrap;
}

.heatmap-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.heatmap-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.heatmap-subtitle {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.legend {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.legend-box {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-box.none {
  background: linear-gradient(135deg, var(--heatmap-empty-odd) 0%, var(--heatmap-empty-even) 100%);
}

.legend-box.level-1 {
  background: var(--heatmap-level-1);
}

.legend-box.level-2 {
  background: var(--heatmap-level-2);
}

.legend-box.level-3 {
  background: linear-gradient(135deg, var(--heatmap-level-3) 0%, var(--heatmap-level-4) 100%);
}

.legend-box.future {
  background: linear-gradient(135deg, var(--heatmap-future-odd) 0%, var(--heatmap-future-even) 100%);
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 180px;
}

.heatmap-wrapper {
  display: flex;
  gap: 8px;
  min-height: 180px;
}

.week-labels-fixed {
  display: grid;
  grid-template-rows: repeat(7, 14px);
  gap: 3px;
  padding-top: 40px;
  flex-shrink: 0;
}

.week-label {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  line-height: 14px;
  height: 14px;
}

.heatmap-container {
  overflow-x: auto;
  overflow-y: hidden;
  flex: 1;
  min-width: 0;
}

.year-labels,
.month-labels {
  display: grid;
  gap: 3px;
  margin-bottom: 6px;
}

.year-label,
.month-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.month-label.is-even {
  opacity: 0.85;
}

.days-grid {
  display: grid;
  grid-template-rows: repeat(7, 14px);
  grid-auto-flow: column;
  gap: 3px;
}

.day-cell {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
  border: 1px solid transparent;
}

.day-cell.has-history:hover {
  transform: scale(1.15);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.08);
}

.day-cell.is-today {
  outline: 2px solid var(--el-color-primary);
  outline-offset: 1px;
}

.day-cell.is-future {
  cursor: default;
}

.dark .day-cell:not(.has-history) {
  border-color: rgba(255, 255, 255, 0.04);
}

.day-detail {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stats-summary {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 420px;
  overflow-y: auto;
}

.history-item {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  padding: 12px;
  background: var(--el-bg-color);
}

.history-item.is-clickable {
  cursor: pointer;
}

.history-item.is-clickable:hover {
  border-color: var(--el-color-primary-light-5);
  background: var(--el-fill-color-light);
}

.history-item.is-selected {
  border-color: var(--el-color-primary);
}

.history-main {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.history-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.dark .history-item {
  background: #1f2937;
}

@media (max-width: 768px) {
  .todo-heatmap {
    padding: 16px;
  }

  .legend {
    gap: 8px;
  }

  .week-labels-fixed {
    padding-top: 44px;
  }
}
</style>
