<script setup lang="ts">
/* global Event, TouchEvent, MouseEvent, HTMLElement */
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import {
  ElButton,
  ElCheckbox,
  ElDatePicker,
  ElEmpty,
  ElIcon,
  ElTag,
} from 'element-plus'
import { ArrowLeft, ArrowRight, Star, Select } from '@element-plus/icons-vue'
import { fetchTodoCompletionHistory } from '../../api'
import type { Todo } from '../../store'
import { useLongPressSelection } from '../../../../composables/useLongPressSelection'
import {
  getPriorityAccentColor,
  isOverdue,
  getRecurrenceText,
  shouldKeepTodoAccentColor,
} from '../../helpers/todo-item'
import { getHolidayCalendarYears } from '../../../../utils/holidayCalendar'

const props = defineProps<{
  todos: Todo[]
  showRecycleBin?: boolean
  multiSelectMode?: boolean
  selectedIds?: string[]
}>()

const emit = defineEmits<{
  (e: 'edit', todo: Todo): void
  (e: 'togglePin', todo: Todo): void
  (e: 'delete', id: string, mode: 'soft' | 'permanent'): void
  (e: 'restore', id: string): void
  (e: 'changeStatus', todo: Todo): void
  (e: 'adjustOccurrence', todo: Todo, occurredOn: string, action: 'complete' | 'reset'): void
  (e: 'longPress', todo: Todo): void
  (e: 'toggleSelect', todo: Todo): void
}>()
const { startLongPress, cancelLongPress, consumeLongPress } = useLongPressSelection<Todo>({
  getId: todo => todo.id,
  onLongPress: todo => emit('longPress', todo),
})

// 当前显示的月份（默认为本月）
const currentMonth = ref(new Date())
const editingMonth = ref(false)
const pickerMonth = ref(formatMonthValue(currentMonth.value))

// 侧边栏宽度（可调整）
const sideWidth = ref(280)
const resizing = ref(false)
const resizeStartX = ref(0)
const resizeStartWidth = ref(280)

// 同步滚动状态
const syncing = ref(false)
const syncingHorizontal = ref(false)
const sideRef = ref<HTMLElement | null>(null)
const rowsRef = ref<HTMLElement | null>(null)
const timelineHeaderRef = ref<HTMLElement | null>(null)

const completionMap = ref(new Map<string, Map<string, number>>())
const holidayDates = ref(new Set<string>())
const workdayDates = ref(new Set<string>())
const COMPLETED_COLOR = '#67c23a'
const PARTIAL_COLOR = '#e6a23c'

// 格式化月份选择器的值
function formatMonthValue(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  return `${year}-${month}`
}

// 格式化日期为本地日期字符串 (YYYY-MM-DD)
function formatDateLocal(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 月份标签显示
const monthLabel = computed(() => {
  const year = currentMonth.value.getFullYear()
  const month = String(currentMonth.value.getMonth() + 1).padStart(2, '0')
  return `${year}年${month}月`
})

// 获取当前月份的所有日期
const days = computed(() => {
  const year = currentMonth.value.getFullYear()
  const month = currentMonth.value.getMonth()
  const lastDay = new Date(year, month + 1, 0)
  const result: { date: Date; day: number; iso: string }[] = []

  for (let d = 1; d <= lastDay.getDate(); d++) {
    const date = new Date(year, month, d)
    // 使用本地日期格式，避免 UTC 偏移问题
    const iso = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    result.push({
      date,
      day: d,
      iso,
    })
  }
  return result
})
const visibleYears = computed(() => Array.from(new Set(days.value.map(day => day.date.getFullYear()))).sort((a, b) => a - b))
const visibleYearsKey = computed(() => visibleYears.value.join(','))

// 显示有时间的待办（包括循环任务）
const displayTodos = computed(() => {
  return props.todos.filter(t => {
    // 显示有开始时间或截止时间的任务
    if (t.start_date || t.end_date) return true
    // 显示循环任务（recurrence_type 存在且不为 'none'）
    if (t.recurrence_type && t.recurrence_type !== 'none') return true
    return false
  })
})

// 上个月
function prevMonth() {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() - 1, 1)
  pickerMonth.value = formatMonthValue(currentMonth.value)
  editingMonth.value = false
}

// 下个月
function nextMonth() {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() + 1, 1)
  pickerMonth.value = formatMonthValue(currentMonth.value)
  editingMonth.value = false
}

// 开始编辑月份
function startEditMonth() {
  pickerMonth.value = formatMonthValue(currentMonth.value)
  editingMonth.value = true
}

// 应用月份选择
function applyMonthPicker(val: string) {
  if (val) {
    const [year, month] = val.split('-').map(Number)
    currentMonth.value = new Date(year, month - 1, 1)
  }
  editingMonth.value = false
}

// 开始调整侧边栏宽度
function startResize(e: MouseEvent) {
  resizing.value = true
  resizeStartX.value = e.clientX
  resizeStartWidth.value = sideWidth.value
  window.addEventListener('mousemove', onResizeMove)
  window.addEventListener('mouseup', stopResize)
}

function onResizeMove(e: MouseEvent) {
  if (!resizing.value) return
  const delta = e.clientX - resizeStartX.value
  const newWidth = Math.min(Math.max(200, resizeStartWidth.value + delta), 500)
  sideWidth.value = newWidth
}

function stopResize() {
  resizing.value = false
  window.removeEventListener('mousemove', onResizeMove)
  window.removeEventListener('mouseup', stopResize)
}

// 滚动同步：右侧滚动时同步左侧
function onRowsScroll() {
  if (syncing.value || !rowsRef.value || !sideRef.value) return
  syncing.value = true
  sideRef.value.scrollTop = rowsRef.value.scrollTop
  syncing.value = false
}

// 横向滚动同步
function syncHorizontalScroll(e: Event) {
  if (syncingHorizontal.value) return
  syncingHorizontal.value = true
  const target = e.target as HTMLElement
  const scrollLeft = target.scrollLeft
  if (timelineHeaderRef.value && target !== timelineHeaderRef.value) {
    timelineHeaderRef.value.scrollLeft = scrollLeft
  }
  if (rowsRef.value && target !== rowsRef.value) {
    rowsRef.value.scrollLeft = scrollLeft
  }
  syncingHorizontal.value = false
}

onMounted(() => {
  rowsRef.value?.addEventListener('scroll', onRowsScroll)
})

onUnmounted(() => {
  rowsRef.value?.removeEventListener('scroll', onRowsScroll)
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

async function loadCompletionHistory() {
  if (days.value.length === 0) {
    completionMap.value = new Map()
    return
  }

  try {
    const data = await fetchTodoCompletionHistory(
      days.value[0].iso,
      days.value[days.value.length - 1].iso,
    )

    const nextMap = new Map<string, Map<string, number>>()
    data.days.forEach(day => {
      day.items.forEach(item => {
        if (!nextMap.has(item.todo_id)) {
          nextMap.set(item.todo_id, new Map<string, number>())
        }
        nextMap.get(item.todo_id)!.set(day.date, item.completed_count)
      })
    })
    completionMap.value = nextMap
  } catch {
    completionMap.value = new Map()
  }
}

watch([days, () => props.todos], () => {
  void loadCompletionHistory()
}, { deep: true, immediate: true })

// 生成部分完成时的分段背景
function getProgressBackground(done: number, total: number): string | null {
  const safeTotal = Math.max(1, total)
  const safeDone = Math.min(Math.max(done, 0), safeTotal)

  if (safeDone <= 0) return null
  if (safeDone >= safeTotal) return COMPLETED_COLOR

  const percent = Math.floor((safeDone / safeTotal) * 100)
  return `linear-gradient(to right, ${COMPLETED_COLOR} ${percent}%, ${PARTIAL_COLOR} ${percent}%)`
}

function getCompletedCount(todoId: string, iso: string): number {
  return completionMap.value.get(todoId)?.get(iso) ?? 0
}

// 获取任务条的基础颜色
// 计算任务条的位置和宽度
function getBarStyle(todo: Todo) {
  const totalDays = days.value.length
  if (totalDays === 0) return { display: 'none' }

  const year = currentMonth.value.getFullYear()
  const month = currentMonth.value.getMonth()
  const monthStart = new Date(year, month, 1)
  const monthEnd = new Date(year, month + 1, 0, 23, 59, 59)

  // 解析任务时间
  const taskStart = todo.start_date ? new Date(todo.start_date) : null
  const taskEnd = todo.end_date ? new Date(todo.end_date) : null

  // 如果没有时间信息，不显示（循环任务用特殊方式显示）
  if (!taskStart && !taskEnd) {
    return { display: 'none' }
  }

  // 确定实际显示范围
  const displayStart = taskStart || taskEnd
  const displayEnd = taskEnd || taskStart

  if (!displayStart || !displayEnd) return { display: 'none' }

  // 计算在当月的位置
  const effectiveStart = displayStart < monthStart ? monthStart : displayStart
  const effectiveEnd = displayEnd > monthEnd ? monthEnd : displayEnd

  // 如果任务不在当前月份显示范围内
  if (effectiveStart > monthEnd || effectiveEnd < monthStart) {
    return { display: 'none' }
  }

  // 计算起始位置和宽度
  const startDay = effectiveStart.getDate() - 1
  const endDay = effectiveEnd.getDate() - 1
  const spanDays = endDay - startDay + 1

  const leftPct = (startDay / totalDays) * 100
  const widthPct = (spanDays / totalDays) * 100

  // 进度条样式 - 支持多次完成的渐变显示
  const style: Record<string, string> = {
    left: `${leftPct}%`,
    width: `${widthPct}%`,
  }

  // 如果有多次完成设置，显示分段进度
  const hasMulti = (todo.times_per_interval || 1) > 1
  if (hasMulti) {
    const progressBackground = getProgressBackground(
      todo.interval_progress || 0,
      todo.times_per_interval || 1,
    )
    if (progressBackground) {
      style.background = progressBackground
    }
  }

  return style
}

// 获取循环任务的日块
function getRecurrenceSegments(todo: Todo) {
  if (!todo.recurrence_type || todo.recurrence_type === 'none') return []

  const totalDays = days.value.length
  const segments: { day: number; style: Record<string, string>; iso: string }[] = []
  const requiredCount = Math.max(1, todo.times_per_interval || 1)
  const hasMulti = requiredCount > 1

  for (let i = 0; i < totalDays; i++) {
    const date = days.value[i].date
    const iso = days.value[i].iso
    if (occursOnDay(todo, date)) {
      const leftPct = (i / totalDays) * 100
      const widthPct = (1 / totalDays) * 100

      const style: Record<string, string> = {
        left: `${leftPct}%`,
        width: `${widthPct}%`,
      }

      // 如果存在部分完成记录，按当天已完成次数显示分段进度
      if (hasMulti) {
        const progressBackground = getProgressBackground(
          getCompletedCount(todo.id, iso),
          requiredCount,
        )
        if (progressBackground) {
          style.background = progressBackground
        }
      }

      segments.push({
        day: i,
        iso,
        style,
      })
    }
  }

  return segments
}

// 判断任务是否在某天发生
function occursOnDay(todo: Todo, date: Date): boolean {
  const type = todo.recurrence_type
  if (!type || type === 'none') return false

  // 检查是否在开始日期之后
  if (todo.start_date) {
    const start = new Date(todo.start_date)
    start.setHours(0, 0, 0, 0)
    const checkDate = new Date(date)
    checkDate.setHours(0, 0, 0, 0)
    if (checkDate < start) return false
  }

  // 检查是否在截止日期之前
  if (todo.end_date) {
    const end = new Date(todo.end_date)
    end.setHours(23, 59, 59, 999)
    const checkDate = new Date(date)
    checkDate.setHours(23, 59, 59, 999)
    if (checkDate > end) return false
  }

  const day = date.getDay()
  const dateNum = date.getDate()
  const month = date.getMonth()
  const iso = formatDateLocal(date)

  switch (type) {
    case 'daily':
      return true
    case 'weekly': {
      if (!todo.start_date) return false
      const start = new Date(todo.start_date)
      return day === start.getDay()
    }
    case 'workday':
      if (workdayDates.value.has(iso)) return true
      if (holidayDates.value.has(iso)) return false
      return day >= 1 && day <= 5
    case 'weekend':
      return day === 0 || day === 6
    case 'holiday':
      return holidayDates.value.has(iso)
    case 'monthly': {
      if (!todo.start_date) return false
      const start = new Date(todo.start_date)
      return dateNum === start.getDate()
    }
    case 'yearly': {
      if (!todo.start_date) return false
      const start = new Date(todo.start_date)
      return month === start.getMonth() && dateNum === start.getDate()
    }
    case 'custom': {
      if (!todo.start_date) return false
      const start = new Date(todo.start_date)
      start.setHours(0, 0, 0, 0)
      const checkDate = new Date(date)
      checkDate.setHours(0, 0, 0, 0)
      const diffDays = Math.floor((checkDate.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
      const interval = Math.max(1, todo.recurrence_interval || 1)
      return diffDays % interval === 0
    }
    default:
      return false
  }
}

// 获取任务条样式类
function getBarClass(todo: Todo): string {
  const isDone = todo.status === 'done'
  const isOverdueTask = todo.end_date && isOverdue(todo.end_date) && !isDone

  if (isDone) return 'status-completed'
  if (isOverdueTask) return 'status-overdue'
  return 'status-pending'
}

// 获取循环任务日块样式类
function getSegmentClass(todo: Todo, iso: string): string {
  const completedCount = getCompletedCount(todo.id, iso)
  const requiredCount = Math.max(1, todo.times_per_interval || 1)
  const todayIso = formatDateLocal(new Date())

  if (completedCount >= requiredCount) return 'status-completed'
  if (completedCount > 0) return 'status-partial'
  if (iso < todayIso) return 'is-past'
  return 'status-pending'
}

function getImportanceStyle(importance: number) {
  return {
    '--todo-importance-color': getPriorityAccentColor(importance),
  }
}

// 处理任务完成点击
function handleCompleteClick(todo: Todo) {
  if (props.multiSelectMode) {
    emit('toggleSelect', todo)
    return
  }
  emit('changeStatus', todo)
}

function handleTogglePin(todo: Todo) {
  if (props.multiSelectMode) {
    emit('toggleSelect', todo)
    return
  }
  emit('togglePin', todo)
}

// 处理循环任务日块点击（按日期补记或重置完成记录）
function handleSegmentClick(todo: Todo, iso: string) {
  if (consumeLongPress(todo)) return
  if (props.multiSelectMode) {
    emit('toggleSelect', todo)
    return
  }
  const todayIso = formatDateLocal(new Date())
  if (iso > todayIso) return

  const completedCount = getCompletedCount(todo.id, iso)
  const requiredCount = Math.max(1, todo.times_per_interval || 1)
  if (completedCount >= requiredCount) {
    emit('adjustOccurrence', todo, iso, 'reset')
    return
  }
  emit('adjustOccurrence', todo, iso, 'complete')
}

// 处理编辑
function handleEdit(todo: Todo) {
  if (consumeLongPress(todo)) return
  if (props.multiSelectMode) {
    emit('toggleSelect', todo)
    return
  }
  if (!props.showRecycleBin && todo.status !== 'done') {
    emit('edit', todo)
  }
}

function isSelected(id: string): boolean {
  return props.selectedIds?.includes(id) ?? false
}
</script>

<template>
  <div class="todo-gantt">
    <!-- 甘特图主体 -->
    <div class="gantt-body">
      <!-- 左侧任务列表 -->
      <div
        ref="sideRef"
        class="gantt-side"
        :style="{ width: sideWidth + 'px' }"
      >
        <div class="gantt-resizer" @mousedown="startResize" />
        <!-- 图例（与右侧工具栏对齐） -->
        <div class="side-legend-row">
          <div class="legend-item">
            <div class="legend-box pending" />
            <span>待完成</span>
          </div>
          <div class="legend-item">
            <div class="legend-box completed" />
            <span>已完成</span>
          </div>
          <div class="legend-item">
            <div class="legend-box partial" />
            <span>部分完成</span>
          </div>
          <div class="legend-item">
            <div class="legend-box overdue" />
            <span>已过期</span>
          </div>
        </div>
        <!-- 侧边栏头部（移到第二行，与右侧日期头部对齐） -->
        <div class="side-header">
          <span class="header-title">任务列表</span>
          <ElTag type="info" size="small">共 {{ displayTodos.length }} 项</ElTag>
        </div>
        <div v-if="displayTodos.length === 0" class="side-empty">
          <div class="side-empty-content">
            <ElEmpty description="暂无有时间安排的任务" />
            <p class="side-empty-desc">添加带有开始时间或截止日期的待办事项以查看甘特图</p>
          </div>
        </div>
        <template v-else>
          <!-- 任务列表 -->
          <div
            v-for="todo in displayTodos"
            :key="todo.id"
            class="gantt-task-row"
            :class="{ 'is-done': todo.status === 'done', 'keeps-accent': shouldKeepTodoAccentColor(todo), 'is-selected': isSelected(todo.id) }"
            :style="getImportanceStyle(todo.importance)"
            @touchstart.passive="startLongPress(todo, $event)"
            @touchmove="cancelLongPress(todo)"
            @touchend="cancelLongPress(todo)"
            @touchcancel="cancelLongPress(todo)"
            @mousedown="startLongPress(todo, $event)"
            @mousemove="cancelLongPress(todo)"
            @mouseup="cancelLongPress(todo)"
            @mouseleave="cancelLongPress(todo)"
            @click="handleEdit(todo)"
          >
            <div v-if="multiSelectMode" class="task-select-indicator" :class="{ 'is-selected': isSelected(todo.id) }">
              <ElIcon><Select /></ElIcon>
            </div>
            <ElCheckbox
              :model-value="todo.status === 'done'"
              class="task-checkbox"
              @change="handleCompleteClick(todo)"
              @click.stop
            />
            <div class="task-info">
              <div class="task-title-wrapper">
                <ElIcon v-if="todo.is_pinned" class="pin-icon" :size="12"><Star /></ElIcon>
                <span class="task-title" :title="todo.title">{{ todo.title }}</span>
              </div>
              <div class="task-meta">
                <span v-if="todo.recurrence_type !== 'none'" class="recurrence-badge">
                  {{ getRecurrenceText(todo.recurrence_type, todo.recurrence_interval) }}
                </span>
                <ElButton
                  size="small"
                  :type="todo.is_pinned ? 'warning' : ''"
                  @click.stop="handleTogglePin(todo)"
                >
                  <ElIcon><Star /></ElIcon>
                </ElButton>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 右侧时间轴 -->
      <div class="gantt-timeline">
        <div class="timeline-toolbar">
          <div class="toolbar-center">
            <ElButton text @click="prevMonth">
              <ElIcon><ArrowLeft /></ElIcon>
              上个月
            </ElButton>
            <template v-if="!editingMonth">
              <ElButton text class="month-label" @click="startEditMonth">
                {{ monthLabel }}
              </ElButton>
            </template>
            <template v-else>
              <ElDatePicker
                v-model="pickerMonth"
                type="month"
                format="YYYY年MM月"
                value-format="YYYY-MM"
                :teleported="false"
                :editable="false"
                :clearable="false"
                size="small"
                popper-class="gantt-month-popper"
                style="width: 140px"
                @change="applyMonthPicker"
              />
            </template>
            <ElButton text @click="nextMonth">
              下个月
              <ElIcon><ArrowRight /></ElIcon>
            </ElButton>
          </div>
        </div>

        <!-- 日期头部（可横向滚动） -->
        <div ref="timelineHeaderRef" class="timeline-header" :style="{ '--days-count': days.length }" @scroll="syncHorizontalScroll">
          <div class="timeline-header-inner">
            <!-- 日期头部 -->
            <div class="days-header" :style="{ '--days-count': days.length }">
              <div
                v-for="d in days"
                :key="d.iso"
                class="day-cell"
                :class="{
                  'is-today': d.iso === formatDateLocal(new Date()),
                  'is-weekend': d.date.getDay() === 0 || d.date.getDay() === 6,
                }"
              >
                <span class="day-number">{{ d.day }}</span>
                <span class="day-week">{{ ['日', '一', '二', '三', '四', '五', '六'][d.date.getDay()] }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 时间轴行（可横向滚动） -->
        <div ref="rowsRef" class="timeline-rows" :style="{ '--days-count': days.length }" @scroll="syncHorizontalScroll">
          <div class="timeline-rows-inner">
            <div
              v-for="todo in displayTodos"
              :key="todo.id"
              class="timeline-row"
              :class="{ 'is-done': todo.status === 'done' }"
            >
              <div class="bar-track">
                <!-- 网格线 -->
                <div
                  v-for="(_, i) in days"
                  :key="i"
                  class="grid-line"
                  :style="{ left: `${(i / days.length) * 100}%`, width: `${100 / days.length}%` }"
                />
                <!-- 任务条（非循环任务） -->
                <div
                  v-if="!todo.recurrence_type || todo.recurrence_type === 'none'"
                  :title="todo.title"
                  class="task-bar"
                  :class="[getBarClass(todo), { 'is-pinned': todo.is_pinned, 'is-selected': isSelected(todo.id) }]"
                  :style="getBarStyle(todo)"
                  @touchstart.passive="startLongPress(todo, $event)"
                  @touchmove="cancelLongPress(todo)"
                  @touchend="cancelLongPress(todo)"
                  @touchcancel="cancelLongPress(todo)"
                  @mousedown="startLongPress(todo, $event)"
                  @mousemove="cancelLongPress(todo)"
                  @mouseup="cancelLongPress(todo)"
                  @mouseleave="cancelLongPress(todo)"
                  @click="handleEdit(todo)"
                >
                  <span v-if="todo.start_date && todo.end_date" class="bar-text">{{ todo.title }}</span>
                </div>
                <!-- 循环任务块 -->
                <template v-else>
                  <div
                    v-for="(seg, idx) in getRecurrenceSegments(todo)"
                    :key="idx"
                    :title="`${todo.title}\n${seg.iso}\n已记录 ${getCompletedCount(todo.id, seg.iso)} / ${Math.max(1, todo.times_per_interval || 1)} 次`"
                    class="recurrence-segment"
                    :class="[getSegmentClass(todo, seg.iso), { 'is-pinned': todo.is_pinned, 'is-selected': isSelected(todo.id) }]"
                    :style="seg.style"
                    @touchstart.passive="startLongPress(todo, $event)"
                    @touchmove="cancelLongPress(todo)"
                    @touchend="cancelLongPress(todo)"
                    @touchcancel="cancelLongPress(todo)"
                    @mousedown="startLongPress(todo, $event)"
                    @mousemove="cancelLongPress(todo)"
                    @mouseup="cancelLongPress(todo)"
                    @mouseleave="cancelLongPress(todo)"
                    @click="handleSegmentClick(todo, seg.iso)"
                  />
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import '../../../styles/media.css';

.todo-gantt {
  --gantt-day-width: 32px;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  border-radius: 8px;
  overflow: hidden;
}

.gantt-body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* 左侧任务列表 */
.gantt-side {
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--el-border-color-lighter);
  overflow: hidden;
  position: relative;
  flex-shrink: 0;
  background: #ffffff;
}

.dark .gantt-side {
  background: var(--bg-hover);
}

.gantt-side-content {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.gantt-resizer {
  position: absolute;
  top: 0;
  right: -3px;
  width: 6px;
  height: 100%;
  cursor: col-resize;
  z-index: 10;
}

.gantt-resizer:hover {
  background: var(--el-color-primary);
  opacity: 0.3;
}



.side-legend-row {
  height: 48px; /* 与右侧工具栏对齐 */
  border-bottom: 1px solid var(--el-border-color-lighter);
  position: sticky;
  top: 0;
  z-index: 5;
  flex-shrink: 0;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  padding: 0 12px;
  background: #ffffff;
}

.dark .side-legend-row {
  background: var(--bg-hover);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.legend-box {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-box.pending {
  background-color: #409eff;
}

.legend-box.completed {
  background-color: #67c23a;
}

.legend-box.partial {
  background: linear-gradient(to right, #67c23a 50%, #e6a23c 50%);
}

.legend-box.overdue {
  background-color: #c0c4cc;
}

.side-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 50px; /* 与右侧日期头部高度对齐 */
  border-bottom: 1px solid var(--el-border-color-lighter);
  position: sticky;
  top: 48px; /* 在空行下方 */
  z-index: 4;
  flex-shrink: 0;
  box-sizing: border-box;
  background: #ffffff;
}

.dark .side-header {
  background: var(--bg-hover);
}

.header-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.gantt-task-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: background-color 0.2s;
  height: 48px;
  box-sizing: border-box;
  flex-shrink: 0;
  overflow: hidden;
  min-width: 0;
  position: relative;
}

.gantt-task-row::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--todo-importance-color, var(--el-color-primary));
}

.gantt-task-row.is-selected {
  background: color-mix(in srgb, var(--el-color-primary-light-9) 78%, white);
}

.gantt-task-row.is-selected::before {
  background: var(--el-color-primary);
}

.side-empty {
  display: flex;
  flex: 1;
  min-height: 0;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
}

.side-empty-content {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.side-empty-desc {
  margin: -32px 0 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: center;
}

.gantt-task-row:hover {
  background: var(--el-fill-color-light);
}

.gantt-task-row.is-done {
  background: #f2f3f5;
  opacity: 0.6;
}

.gantt-task-row.is-done::before {
  background: #909399;
}

.gantt-task-row.is-done.keeps-accent::before {
  background: var(--todo-importance-color, var(--el-color-primary));
}

.gantt-task-row.is-selected.keeps-accent::before {
  background: var(--el-color-primary);
}

.gantt-task-row.is-done:hover {
  background: #f2f3f5;
}

.gantt-task-row.is-done .task-title {
  text-decoration: line-through;
}

.task-checkbox {
  flex-shrink: 0;
}

.task-select-indicator {
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

.task-select-indicator.is-selected {
  background: var(--el-color-primary);
  color: #fff;
}

.task-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}

.task-title-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pin-icon {
  color: #f56c6c;
  flex-shrink: 0;
}

.task-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
  overflow: hidden;
  min-width: 0;
}

.task-meta .el-button {
  height: 18px;
  padding: 0 4px;
  margin-left: auto;
}

.recurrence-badge {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color);
  padding: 1px 6px;
  border-radius: 4px;
}

/* 右侧时间轴 */
.gantt-timeline {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  background: #ffffff;
}

.dark .gantt-timeline {
  background: var(--bg-hover);
}

.timeline-header {
  flex-shrink: 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  overflow-x: auto;
  overflow-y: hidden;
  overscroll-behavior-x: contain;
}

.timeline-header::-webkit-scrollbar {
  display: none;
}

.timeline-header-inner {
  min-width: calc(var(--days-count) * var(--gantt-day-width));
  width: max-content;
}

.toolbar-center {
  display: flex;
  align-items: center;
  gap: 8px;
}

.timeline-toolbar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 8px;
  height: 48px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: #ffffff;
  box-sizing: border-box;
  flex-shrink: 0;
}

.dark .timeline-toolbar {
  background: var(--bg-hover);
}

.month-label {
  font-weight: 600;
  font-size: 14px;
}

.days-header {
  display: grid;
  grid-template-columns: repeat(var(--days-count), var(--gantt-day-width));
  min-width: max-content;
}

.day-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2px;
  height: 49px;
  font-size: 12px;
  min-width: 0;
  box-sizing: border-box;
  background: #ffffff;
  border-right: 1px solid var(--el-border-color-lighter);
}

.dark .day-cell {
  background: var(--bg-hover);
}

.day-cell.is-today {
  background: var(--el-color-primary-light-9);
}

.day-cell.is-today .day-number {
  color: var(--el-color-primary-dark-2);
  font-weight: 600;
}

.day-cell.is-today .day-week {
  color: var(--el-color-primary-dark-2);
}

.day-cell.is-weekend {
  background: #f5f7fa;
}

.dark .day-cell.is-weekend {
  background: var(--bg-primary);
}

.day-number {
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.day-week {
  font-size: 10px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

/* 时间轴行 */
.timeline-rows {
  flex: 1;
  overflow: auto;
  display: flex;
  flex-direction: column;
  overscroll-behavior-x: contain;
}

.timeline-rows-inner {
  min-width: calc(var(--days-count) * var(--gantt-day-width));
  width: max-content;
}

.timeline-row {
  height: 48px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  position: relative;
  flex-shrink: 0;
  min-width: calc(var(--days-count) * var(--gantt-day-width));
}

.timeline-row.is-done,
.timeline-row.is-done .bar-track {
  background: #f2f3f5;
}

.bar-track {
  position: relative;
  width: 100%;
  min-width: calc(var(--days-count) * var(--gantt-day-width));
  height: 100%;
}

.grid-line {
  position: absolute;
  top: 0;
  bottom: 0;
  border-right: 1px dashed var(--el-border-color-lighter);
  pointer-events: none;
}

.task-bar {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  height: 28px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  padding: 0 8px;
  color: white;
  font-size: 12px;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.2s;
  overflow: hidden;
  z-index: 2;
}

.task-bar:hover {
  opacity: 0.9;
  transform: translateY(-50%) scaleY(1.05);
}

.task-bar.is-selected,
.recurrence-segment.is-selected {
  box-shadow: 0 0 0 2px rgb(var(--el-color-primary-rgb) / 0.45);
}

.task-bar.status-pending { background-color: #409eff; }
.task-bar.status-completed { background-color: #67c23a; }
.task-bar.status-overdue { background-color: #c0c4cc; }



.bar-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recurrence-segment {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  height: 24px;
  border-radius: 3px;
  cursor: pointer;
  transition: opacity 0.2s;
  z-index: 2;
}

.recurrence-segment:hover {
  opacity: 0.8;
  transform: translateY(-50%) scaleY(1.1);
}

.recurrence-segment.status-pending { background-color: #409eff; }
.recurrence-segment.status-completed { background-color: #67c23a; }
.recurrence-segment.status-partial { background-color: #e6a23c; }
.recurrence-segment.is-past { background-color: #c0c4cc; }



/* 深色模式下日期头部背景 */
.dark .days-header {
  background: var(--el-border-color);
}

/* 深色模式下今天和周末样式正确 */
.dark .day-cell.is-today {
  background: var(--el-color-primary-light-9);
}

.dark .day-cell.is-weekend {
  background: var(--bg-primary);
}

/* 深色模式下时间轴背景 */
.dark .timeline-header {
  background: var(--bg-primary);
}

/* 深色模式下时间轴行区域背景 */
.dark .timeline-rows {
  background: var(--bg-hover);
}

/* 深色模式下任务条轨道背景 */
.dark .bar-track {
  background: var(--bg-hover);
}

/* 深色模式下任务行悬停效果 */
.dark .gantt-task-row:hover {
  background: var(--bg-hover);
}

.dark .gantt-task-row.is-done {
  background: #2b3138;
}

.dark .gantt-task-row.is-done::before {
  background: #909399;
}

.dark .gantt-task-row.is-done.keeps-accent::before {
  background: var(--todo-importance-color, var(--el-color-primary));
}

.dark .gantt-task-row.is-selected.keeps-accent::before {
  background: var(--el-color-primary);
}

.dark .gantt-task-row.is-done:hover {
  background: #2b3138;
}

.dark .gantt-task-row.is-selected {
  background: rgb(var(--el-color-primary-rgb) / 0.16);
}

.dark .timeline-row.is-done,
.dark .timeline-row.is-done .bar-track {
  background: #2b3138;
}

/* 深色模式下文字颜色 - 统一为白色 */
.dark .day-number,
.dark .day-week,
.dark .header-title,
.dark .task-title,
.dark .legend-item,
.dark .legend-item span,
.dark .recurrence-badge,
.dark .month-label {
  color: #e5e7eb !important;
}

/* 深色模式下循环任务标签背景 */
.dark .recurrence-badge {
  background: var(--bg-primary);
}

/* 深色模式下今天日期数字和周用深色 */
.dark .day-cell.is-today .day-number,
.dark .day-cell.is-today .day-week {
  color: var(--el-color-primary-dark-2) !important;
}

/* 深色模式下任务条文字 */
.dark .task-bar .bar-text {
  color: #e5e7eb;
}

.dark .side-empty-desc {
  color: var(--el-text-color-secondary);
}

/* 深色模式下置顶按钮边框更明显 */
.dark .task-meta .el-button--warning {
  border: 1px solid #e6a23c;
}

/* 月份选择器弹窗样式 */
:global(.gantt-month-popper) {
  width: 260px !important;
}

/* 响应式 */
@media (--mobile-viewport) {
  .todo-gantt {
    --gantt-day-width: 24px;
  }

  .gantt-side {
    width: 180px !important;
  }

  .day-cell {
    padding: 4px 1px;
  }

  .day-week {
    font-size: 9px;
  }

  .task-bar .bar-text {
    display: none;
  }
}
</style>
