<script setup lang="ts">
/* global HTMLElement, MouseEvent */
import { ref, computed, onMounted, watch } from 'vue'
import { ElEmpty, ElTag, ElCheckbox } from 'element-plus'
import { Select } from '@element-plus/icons-vue'
import type { Todo } from '../../../stores/todo'
import { recurrenceOptions } from '../../../composables/useTodoItem'
import { useLongPressSelection } from '../../../composables/useLongPressSelection'
import BaseDialog from '../../../components/BaseDialog.vue'
import { getHolidayCalendarYears } from '../../../utils/holidayCalendar'

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
const { startLongPress, cancelLongPress, consumeLongPress } = useLongPressSelection<Todo>({
  getId: todo => todo.id,
  onLongPress: todo => emit('longPress', todo),
})

// 日期范围：从这个月往前一年 到 往后一年
// 例如当前是2026年3月，则显示 2025年3月 ~ 2027年3月
const today = new Date()
const currentYear = today.getFullYear()
const currentMonth = today.getMonth()
const startDate = computed(() => new Date(currentYear - 1, currentMonth, 1))
const endDate = computed(() => new Date(currentYear + 1, currentMonth + 1, 0))

// 选中的日期详情
const showDayDetail = ref(false)
const selectedDay = ref<DayStats | null>(null)
const holidayDates = ref(new Set<string>())
const workdayDates = ref(new Set<string>())

interface DayStats {
  date: Date
  dateStr: string
  todos: Todo[]
  total: number
  completed: number
  todo: number
  done: number
  completionRate: number
  isToday: boolean
  isFuture: boolean
}

// 获取指定日期的待办事项
function getTodosForDate(date: Date): Todo[] {
  const dateStr = formatDate(date)

  return props.todos.filter(todo => {
    // 已删除的待办不显示
    if (todo.is_deleted) return false

    // 如果有截止日期，检查是否匹配
    if (todo.end_date) {
      const endDate = formatDate(new Date(todo.end_date))

      // 对于非循环任务，只在到期日显示
      if (todo.recurrence_type === 'none') {
        return dateStr === endDate
      }

      // 对于循环任务，如果指定了截止日期，在截止日期之后不显示
      if (dateStr > endDate) {
        return false
      }
    }

    // 检查开始日期
    if (todo.start_date) {
      const startDate = formatDate(new Date(todo.start_date))
      if (dateStr < startDate) return false
    }

    // 对于循环任务，检查是否在该日期有效
    if (todo.recurrence_type && todo.recurrence_type !== 'none' && todo.start_date) {
      return isRecurringTodoActiveOnDate(todo, date)
    }

    return false
  })
}

// 检查循环任务是否在指定日期有效
function isRecurringTodoActiveOnDate(todo: Todo, date: Date): boolean {
  if (!todo.start_date) return false

  const startDate = new Date(todo.start_date)
  startDate.setHours(0, 0, 0, 0)

  const checkDate = new Date(date)
  checkDate.setHours(0, 0, 0, 0)

  if (checkDate < startDate) return false

  const dayOfWeek = checkDate.getDay()
  const iso = formatDate(checkDate)

  switch (todo.recurrence_type) {
    case 'daily':
      return true
    case 'weekly': {
      const startDay = startDate.getDay()
      return dayOfWeek === startDay
    }
    case 'workday':
      if (workdayDates.value.has(iso)) return true
      if (holidayDates.value.has(iso)) return false
      return dayOfWeek >= 1 && dayOfWeek <= 5
    case 'weekend':
      return dayOfWeek === 0 || dayOfWeek === 6
    case 'holiday':
      return holidayDates.value.has(iso)
    case 'monthly': {
      return checkDate.getDate() === startDate.getDate()
    }
    case 'yearly': {
      return checkDate.getMonth() === startDate.getMonth() &&
        checkDate.getDate() === startDate.getDate()
    }
    case 'custom': {
      // 自定义循环：每 recurrence_interval 天
      const diffTime = checkDate.getTime() - startDate.getTime()
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
      return diffDays % todo.recurrence_interval === 0
    }
    default:
      return false
  }
}

// 格式化日期为 YYYY-MM-DD
function formatDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 计算单日统计
function calculateDayStats(todos: Todo[]): Omit<DayStats, 'date' | 'dateStr' | 'isToday' | 'isFuture'> {
  const total = todos.length
  const completed = todos.filter(t => t.status === 'done').length
  const todo = todos.filter(t => t.status === 'todo').length

  return {
    todos,
    total,
    completed,
    todo,
    done: completed,
    completionRate: total > 0 ? completed / total : 0,
  }
}

// 生成日期列表
const days = computed(() => {
  const result: DayStats[] = []
  const start = new Date(startDate.value)
  const end = new Date(endDate.value)

  // 调整到周一开始
  const startDay = start.getDay()
  const offset = startDay === 0 ? 6 : startDay - 1
  start.setDate(start.getDate() - offset)

  const current = new Date(start)
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  while (current <= end) {
    const dateStr = formatDate(current)
    const dayTodos = getTodosForDate(current)
    const stats = calculateDayStats(dayTodos)

    result.push({
      date: new Date(current),
      dateStr,
      ...stats,
      isToday: current.getTime() === today.getTime(),
      isFuture: current > today,
    })

    current.setDate(current.getDate() + 1)
  }

  return result
})

// 周数
const weeksCount = computed(() => Math.ceil(days.value.length / 7))
const visibleYears = computed(() => Array.from(new Set(days.value.map(day => day.date.getFullYear()))).sort((a, b) => a - b))
const visibleYearsKey = computed(() => visibleYears.value.join(','))

// 热力图容器ref，用于滚动到中间
const heatmapContainerRef = ref<HTMLElement | null>(null)

// 计算今天所在列索引（用于滚动到中间）
const todayColumnIndex = computed(() => {
  const todayDate = new Date()
  todayDate.setHours(0, 0, 0, 0)
  
  for (let i = 0; i < days.value.length; i++) {
    const day = days.value[i]
    if (day.date.getTime() === todayDate.getTime()) {
      return Math.floor(i / 7)
    }
  }
  // 如果没找到今天，返回中间位置
  return Math.floor(days.value.length / 2 / 7)
})

// 组件挂载后滚动到今天所在位置（居中显示）
onMounted(() => {
  // 使用 setTimeout 确保 DOM 完全渲染
  setTimeout(() => {
    if (heatmapContainerRef.value) {
      const container = heatmapContainerRef.value
      // 每个列宽度 = 格子14px + gap 3px = 17px
      const colWidth = 17
      const todayCol = todayColumnIndex.value
      // 目标滚动位置 = 今天所在列的位置 - 容器宽度的一半 + 一列宽度的一半（使该列居中）
      const targetScrollLeft = todayCol * colWidth - container.clientWidth / 2 + colWidth / 2
      
      container.scrollTo({
        left: Math.max(0, targetScrollLeft),
        behavior: 'auto' // 使用 'auto' 避免 smooth 可能带来的延迟问题
      })
    }
  }, 100)
})

async function loadHolidayCalendar() {
  try {
    const data = await getHolidayCalendarYears(visibleYears.value)
    holidayDates.value = new Set(data.flatMap(item => item.holiday_dates))
    workdayDates.value = new Set(data.flatMap(item => item.workday_dates))
  } catch {
    holidayDates.value = new Set()
    workdayDates.value = new Set()
  }
}

watch(visibleYearsKey, () => {
  void loadHolidayCalendar()
}, { immediate: true })

// 年份标签
const yearLabels = computed(() => {
  const labels: Array<{ year: number; start: number; span: number }> = []
  let currentYearVal = -1
  let startCol = 1

  days.value.forEach((day, index) => {
    const year = day.date.getFullYear()
    const colIndex = Math.floor(index / 7) + 1

    if (year !== currentYearVal) {
      if (currentYearVal !== -1) {
        labels.push({
          year: currentYearVal,
          start: startCol,
          span: colIndex - startCol,
        })
      }
      currentYearVal = year
      startCol = colIndex
    }
  })

  if (currentYearVal !== -1) {
    const weeksCountValue = Math.ceil(days.value.length / 7)
    labels.push({
      year: currentYearVal,
      start: startCol,
      span: weeksCountValue - startCol + 1,
    })
  }

  return labels
})

// 月份标签（不显示年份）
const monthLabels = computed(() => {
  const labels: Array<{ key: string; label: string; start: number; span: number; isEven: boolean }> = []
  let currentMonth = -1
  let startCol = 1
  let currentYear = -1

  // 原始开始日期（不调整到周一之前的）：前一年本月1日
  const now = new Date()
  const rawStart = new Date(now.getFullYear() - 1, now.getMonth(), 1)

  days.value.forEach((day, index) => {
    const month = day.date.getMonth()
    const year = day.date.getFullYear()
    const colIndex = Math.floor(index / 7) + 1

    // 跳过在原始开始日期之前的月份（避免显示调整到周一前的那些月份）
    if (day.date.getTime() < rawStart.getTime()) {
      return
    }

    if (month !== currentMonth || year !== currentYear) {
      if (currentMonth !== -1) {
        labels.push({
          key: `${currentYear}-${currentMonth}`,
          label: `${currentMonth + 1}月`,
          start: startCol,
          span: colIndex - startCol,
          isEven: (currentMonth + 1) % 2 === 0,
        })
      }
      currentMonth = month
      currentYear = year
      startCol = colIndex
    }
  })

  if (currentMonth !== -1) {
    const weeksCountValue = Math.ceil(days.value.length / 7)
    labels.push({
      key: `${currentYear}-${currentMonth}`,
      label: `${currentMonth + 1}月`,
      start: startCol,
      span: weeksCountValue - startCol + 1,
      isEven: (currentMonth + 1) % 2 === 0,
    })
  }

  return labels
})

// 获取单元格样式类
function getCellClass(day: DayStats): Record<string, boolean> {
  const month = day.date.getMonth() + 1
  return {
    'is-today': day.isToday,
    'is-future': day.isFuture,
    'has-todos': day.total > 0,
    'is-completed': day.total > 0 && day.completionRate === 1,
    'is-partial': day.total > 0 && day.completionRate > 0 && day.completionRate < 1,
    'is-pending': day.total > 0 && day.completionRate === 0,
    'is-even-month': month % 2 === 0 && day.total === 0,
  }
}

// 获取单元格背景色
function getCellColor(day: DayStats): string {
  const month = day.date.getMonth() + 1 // 1-12
  const isEvenMonth = month % 2 === 0

  // 双数月份无数据用浅灰色
  if (day.total === 0) {
    return isEvenMonth ? '#f3f4f6' : '#ebedf0'
  }

  if (day.isFuture) return '#d1d5db'

  // 全部完成 - 绿色梯度
  if (day.completionRate === 1) {
    const intensity = Math.min(day.total, 4)
    const colors = ['#9be9a8', '#40c463', '#30a14e', '#216e39']
    return colors[intensity - 1] || colors[3]
  }

  // 部分完成
  if (day.completionRate > 0) {
    return '#ffd54f'
  }

  // 全部未完成
  return '#f87171'
}

// 获取提示文本
function getTooltip(day: DayStats): string {
  if (day.total === 0) {
    return day.dateStr
  }

  let tooltip = `${day.dateStr}\n`
  tooltip += `总计: ${day.total}\n`
  tooltip += `已完成: ${day.completed}\n`
  tooltip += `待完成: ${day.todo}`

  return tooltip
}

// 处理单元格点击
function handleDayClick(day: DayStats): void {
  if (day.total === 0) return
  selectedDay.value = day
  showDayDetail.value = true
}

// 获取循环类型标签
function getRecurrenceLabel(type: string): string {
  return recurrenceOptions.find(o => o.value === type)?.label || type
}

// 判断待办是否超期
function isOverdue(todo: Todo): boolean {
  if (!todo.end_date || todo.status === 'done') return false
  return new Date(todo.end_date) < new Date()
}

function handleTodoClick(todo: Todo) {
  if (consumeLongPress(todo)) return
  if (props.multiSelectMode) {
    emit('toggleSelect', todo)
    return
  }
  emit('edit', todo)
}

function isSelected(id: string): boolean {
  return props.selectedIds?.includes(id) ?? false
}

function handleTodoCheckboxChange(todo: Todo) {
  if (props.multiSelectMode) {
    emit('toggleSelect', todo)
    return
  }
  emit('toggleComplete', todo)
}
</script>

<template>
  <div class="todo-heatmap">
    <div class="heatmap-header">
      <h3>待办热力图</h3>
      <div class="legend">
        <div class="legend-item">
          <div class="legend-box future" />
          <span>未到期</span>
        </div>
        <div class="legend-item">
          <div class="legend-box completed" />
          <span>全部完成</span>
        </div>
        <div class="legend-item">
          <div class="legend-box partial" />
          <span>部分完成</span>
        </div>
        <div class="legend-item">
          <div class="legend-box pending" />
          <span>未完成</span>
        </div>
      </div>
    </div>

    <div v-if="props.todos.length === 0" class="empty-state">
      <ElEmpty description="暂无待办事项数据" />
    </div>

    <div v-else class="heatmap-wrapper">
      <!-- 星期标签 - 固定在左侧 -->
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
        <!-- 年份标签行 -->
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

        <!-- 月份标签行 -->
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

        <div class="days-grid">
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

    <!-- 日期详情弹窗 -->
    <BaseDialog
      v-model="showDayDetail"
      :title="`${selectedDay?.dateStr} 待办详情`"
      width="560px"
    >
      <div v-if="selectedDay" class="day-detail">
        <div class="stats-summary">
          <ElTag>总数: {{ selectedDay.total }}</ElTag>
          <ElTag type="success">已完成: {{ selectedDay.completed }}</ElTag>
          <ElTag type="warning">待完成: {{ selectedDay.todo }}</ElTag>
        </div>

        <div class="todos-list">
          <div
            v-for="todo in selectedDay.todos"
            :key="todo.id"
            class="todo-item"
            :class="[`status-${todo.status}`, { 'is-selected': isSelected(todo.id) }]"
            @touchstart.passive="startLongPress(todo, $event)"
            @touchmove="cancelLongPress(todo)"
            @touchend="cancelLongPress(todo)"
            @touchcancel="cancelLongPress(todo)"
            @mousedown="startLongPress(todo, $event)"
            @mousemove="cancelLongPress(todo)"
            @mouseup="cancelLongPress(todo)"
            @mouseleave="cancelLongPress(todo)"
            @click="handleTodoClick(todo)"
          >
            <div v-if="multiSelectMode" class="select-indicator" :class="{ 'is-selected': isSelected(todo.id) }">
              <Select />
            </div>
            <ElCheckbox
              :model-value="todo.status === 'done'"
              @click.stop
              @change="handleTodoCheckboxChange(todo)"
            />
            <div class="todo-content">
              <div class="todo-title">{{ todo.title }}</div>
              <div class="todo-meta">
                <ElTag v-if="todo.recurrence_type !== 'none'" size="small">
                  {{ getRecurrenceLabel(todo.recurrence_type) }}
                </ElTag>
                <span v-if="todo.times_per_interval > 1">
                  {{ Math.min(todo.interval_progress || 0, todo.times_per_interval) }}/{{ todo.times_per_interval }}
                </span>
                <span v-if="isOverdue(todo)" class="overdue-tag">已超期</span>
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
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 180px;
}

.heatmap-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.heatmap-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.dark .heatmap-header h3 {
  color: #e5e7eb;
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

.dark .legend-item {
  color: #9ca3af;
}

.legend-box {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-box.future {
  background-color: #d1d5db;
}

.legend-box.completed {
  background: linear-gradient(to right, #9be9a8 0%, #216e39 100%);
}

.legend-box.partial {
  background-color: #ffd54f;
}

.legend-box.pending {
  background-color: #f87171;
}

.heatmap-wrapper {
  display: flex;
  gap: 8px;
  position: relative;
}

.heatmap-container {
  overflow-x: auto;
  padding-bottom: 8px;
  flex: 1;
}

.week-labels-fixed {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding-top: 42px; /* 年份标签(12px + 4px margin) + 月份标签(11px + 8px margin) = 35px，再加一些余量 */
  flex-shrink: 0;
}

/* 年份标签样式 */
.year-labels {
  display: grid;
  gap: 3px;
  margin-bottom: 4px;
}

.year-label {
  font-size: 12px;
  color: var(--el-text-color-primary);
  text-align: left;
  font-weight: 600;
}

.dark .year-label {
  color: #d1d5db;
}

/* 月份标签样式 */
.month-labels {
  display: grid;
  gap: 3px;
  margin-bottom: 8px;
}

.month-label {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  text-align: left;
  font-weight: 500;
}

.dark .month-label {
  color: #9ca3af;
}

.month-label.is-even {
  color: #d1d5db;
}

.dark .month-label.is-even {
  color: #6b7280;
}

.week-labels-fixed .week-label,
.week-label {
  width: 20px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.dark .week-label {
  color: #9ca3af;
}

.days-grid {
  display: grid;
  grid-template-rows: repeat(7, 14px);
  grid-auto-flow: column;
  grid-auto-columns: 14px;
  gap: 3px;
}

.day-cell {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  cursor: default;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.day-cell.has-todos {
  cursor: pointer;
}

.day-cell.has-todos:hover {
  transform: scale(1.3);
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  border-color: var(--el-color-primary);
}

.day-cell.is-today {
  outline: 2px solid var(--el-color-primary);
  outline-offset: 1px;
}

.day-detail {
  max-height: 500px;
}

.stats-summary {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.todos-list {
  max-height: 400px;
  overflow-y: auto;
}

.todo-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  margin-bottom: 8px;
  transition: all 0.2s;
  cursor: pointer;
}

.todo-item.is-selected {
  background: color-mix(in srgb, var(--el-color-primary-light-9) 78%, white);
  border-color: var(--el-color-primary);
}

.todo-item:hover {
  background-color: var(--el-fill-color-light);
  border-color: var(--el-border-color);
}

.todo-item.status-done {
  opacity: 0.6;
}

.todo-item.status-done .todo-title {
  text-decoration: line-through;
}

.todo-content {
  flex: 1;
}

.select-indicator {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color);
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.select-indicator.is-selected {
  background: var(--el-color-primary);
  color: #fff;
}

.todo-title {
  font-size: 14px;
  margin-bottom: 4px;
  color: var(--el-text-color-primary);
}

.todo-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.overdue-tag {
  color: var(--el-color-danger);
  font-weight: 500;
}

/* 深色模式适配 */
.dark .legend-box.future {
  background-color: #6b7280;
}

/* 未到期格子 - 深色模式 */
.dark .day-cell.is-future {
  background-color: #6b7280 !important;
}

.dark .day-cell {
  opacity: 0.9;
}

.dark .day-cell.has-todos:hover {
  opacity: 1;
}

/* 单双数月份格子颜色 - 单数月份 */
.day-cell:not(.is-even-month):not(.has-todos) {
  background-color: #ebedf0 !important;
}

.dark .day-cell:not(.is-even-month):not(.has-todos) {
  background-color: #2d333b !important;
}

/* 双数月份格子颜色 */
.day-cell.is-even-month {
  background-color: #f3f4f6 !important;
}

.dark .day-cell.is-even-month {
  background-color: #1f2937 !important;
}
</style>
