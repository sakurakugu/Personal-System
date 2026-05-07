<script setup lang="ts">
/* global Event, TouchEvent, MouseEvent */
import { computed, reactive } from 'vue'
import { ElCard, ElEmpty, ElIcon, ElTag, ElTooltip } from 'element-plus'
import { Star, Calendar, ArrowUp, ArrowDown, Delete, RefreshRight, Select } from '@element-plus/icons-vue'
import type { Todo } from '../../store'
import { useLongPressSelection } from '../../shared/composables/useLongPressSelection'
import {
  formatPreciseDateTime,
  getTrashExpireAt,
  getTrashRemainingDeleteText,
} from '../../helpers/todo-item'

interface Props {
  todos: Todo[]
  showRecycleBin?: boolean
  multiSelectMode?: boolean
  selectedIds?: string[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  edit: [todo: Todo]
  delete: [id: string, mode: 'soft' | 'permanent']
  togglePin: [todo: Todo]
  changeStatus: [todo: Todo]
  restore: [id: string]
  longPress: [todo: Todo]
  toggleSelect: [todo: Todo]
}>()
const { startLongPress, cancelLongPress, consumeLongPress } = useLongPressSelection<Todo>({
  getId: todo => todo.id,
  onLongPress: todo => emit('longPress', todo),
})

// 判断是否为重要日（包含"重要日"标签）
function isImportantDay(todo: Todo): boolean {
  if (!todo.tags) return false
  return todo.tags.includes('重要日')
}

// 解析日期，返回 Date 对象（本地时间）
function parseDate(dateStr: string | null): Date | null {
  if (!dateStr) return null
  return new Date(dateStr)
}

// 计算两个日期之间的天数差（忽略时间部分）
function getDaysDiff(start: Date, end: Date): number {
  const s = new Date(start.getFullYear(), start.getMonth(), start.getDate())
  const e = new Date(end.getFullYear(), end.getMonth(), end.getDate())
  return Math.floor((e.getTime() - s.getTime()) / (1000 * 60 * 60 * 24))
}

// 获取当前日期（本地时间）
function getToday(): Date {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), now.getDate())
}

// 按自然年拆分两个日期之间的间隔
function getYearDaySpan(start: Date, end: Date): { years: number; days: number } {
  let years = end.getFullYear() - start.getFullYear()
  let anchor = new Date(start.getFullYear() + years, start.getMonth(), start.getDate())

  if (anchor > end) {
    years -= 1
    anchor = new Date(start.getFullYear() + years, start.getMonth(), start.getDate())
  }

  return {
    years: Math.max(0, years),
    days: Math.max(0, getDaysDiff(anchor, end)),
  }
}

// 计算下一个周年日的年份
function getNextAnniversaryYear(startDate: Date): number {
  const today = getToday()
  const currentYear = today.getFullYear()
  const anniversaryThisYear = new Date(currentYear, startDate.getMonth(), startDate.getDate())
  
  // 如果今年的纪念日已过，取明年
  if (anniversaryThisYear < today) {
    return currentYear + 1
  }
  return currentYear
}

// 重要日信息接口
interface ImportantDayInfo {
  todo: Todo
  type: 'countdown' | 'countup' // countdown: 倒计时, countup: 正计时
  days: number // 拆分后的余下天数
  totalDays: number // 总天数（正计时从起始日期累计）
  years: number // 年数（正计时）
  targetDate: Date // 目标日期（倒计时用）或起始日期（正计时用）
  nextAnniversary?: Date // 下一个周年日
}

// 计算重要日信息
const importantDays = computed<ImportantDayInfo[]>(() => {
  const list: ImportantDayInfo[] = []
  const today = getToday()

  for (const todo of props.todos) {
    if (!isImportantDay(todo)) continue

    const startDate = parseDate(todo.start_date)
    const endDate = parseDate(todo.end_date)

    // 情况1: 只有 start_date -> 正计时（从 start_date 开始计算已过天数）
    if (startDate && !endDate) {
      const totalDays = getDaysDiff(startDate, today)
      const { years, days } = getYearDaySpan(startDate, today)
      
      list.push({
        todo,
        type: 'countup',
        days,
        totalDays,
        years,
        targetDate: startDate,
        nextAnniversary: new Date(getNextAnniversaryYear(startDate), startDate.getMonth(), startDate.getDate())
      })
      continue
    }

    // 情况2: 只有 end_date -> 倒计时（到 end_date 还剩多少天）
    if (!startDate && endDate) {
      const totalDays = getDaysDiff(today, endDate)
      const span = getYearDaySpan(today, endDate)
      list.push({
        todo,
        type: 'countdown',
        days: span.days,
        totalDays: Math.abs(totalDays),
        years: span.years,
        targetDate: endDate
      })
      continue
    }

    // 情况3: 两者都有，根据日期判断
    if (startDate && endDate) {
      // 如果 end_date 在未来，显示倒计时
      if (endDate > today) {
        const totalDays = getDaysDiff(today, endDate)
        const span = getYearDaySpan(today, endDate)
        list.push({
          todo,
          type: 'countdown',
          days: span.days,
          totalDays: Math.abs(totalDays),
          years: span.years,
          targetDate: endDate
        })
      } else {
        // end_date 已过，转换为正计时（从 start_date 开始）
        const totalDays = getDaysDiff(startDate, today)
        const { years, days } = getYearDaySpan(startDate, today)
        
        list.push({
          todo,
          type: 'countup',
          days,
          totalDays,
          years,
          targetDate: startDate,
          nextAnniversary: new Date(getNextAnniversaryYear(startDate), startDate.getMonth(), startDate.getDate())
        })
      }
      continue
    }

    // 情况4: 都没有日期，仍然显示但不计算天数
    list.push({
      todo,
      type: 'countup',
      days: 0,
      totalDays: 0,
      years: 0,
      targetDate: today
    })
  }

  // 排序：置顶的在前，然后按天数排序（倒计时少的在前，正计时多的在前）
  return list.sort((a, b) => {
    // 置顶优先
    if (a.todo.is_pinned !== b.todo.is_pinned) {
      return a.todo.is_pinned ? -1 : 1
    }
    // 同类型内排序
    if (a.type === b.type) {
      if (a.type === 'countdown') {
        return a.totalDays - b.totalDays // 倒计时：天数少的在前
      } else {
        return b.years - a.years || b.days - a.days // 正计时：年数/天数多的在前
      }
    }
    // 倒计时优先于正计时
    return a.type === 'countdown' ? -1 : 1
  })
})

// 获取其他标签（排除"重要日"）
function getOtherTags(tags: string[] | null): string[] {
  if (!tags) return []
  return tags.filter(tag => tag && tag !== '重要日')
}

// 格式化日期显示
function formatDate(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function formatDeletedDate(dateStr: string | null): string {
  const date = parseDate(dateStr)
  return date ? formatDate(date) : ''
}

// 判断是否循环
function isYearlyRecurrence(todo: Todo): boolean {
  return todo.recurrence_type === 'yearly' || todo.recurrence_type === 'monthly'
}

function canToggleCountupDisplay(item: ImportantDayInfo): boolean {
  return item.type === 'countup' && item.years > 0
}

function canToggleYearDayDisplay(item: ImportantDayInfo): boolean {
  return item.years > 0
}

interface SwipeState {
  offsetX: number
  offsetY: number
  startX: number
  startY: number
  isDragging: boolean
  hasMoved: boolean
}

const swipeState = reactive<Record<string, SwipeState>>({})

const SWIPE_THRESHOLD = 88
const MAX_OFFSET_X = 116
const MAX_OFFSET_Y = 38
const MIN_TRIGGER_Y = 12

function initSwipeState(id: string) {
  if (!swipeState[id]) {
    swipeState[id] = {
      offsetX: 0,
      offsetY: 0,
      startX: 0,
      startY: 0,
      isDragging: false,
      hasMoved: false,
    }
  }
}

function onTouchStart(e: Event, id: string) {
  if (props.multiSelectMode) return
  initSwipeState(id)
  const state = swipeState[id]
  state.isDragging = true

  if (e instanceof TouchEvent) {
    state.startX = e.touches[0].clientX
    state.startY = e.touches[0].clientY
  } else if (e instanceof MouseEvent) {
    state.startX = e.clientX
    state.startY = e.clientY
  }
}

function onTouchMove(e: Event, id: string) {
  if (props.multiSelectMode) return
  const state = swipeState[id]
  if (!state?.isDragging) return

  let clientX = 0
  let clientY = 0
  if (e instanceof TouchEvent) {
    clientX = e.touches[0].clientX
    clientY = e.touches[0].clientY
  } else if (e instanceof MouseEvent) {
    clientX = e.clientX
    clientY = e.clientY
  }

  const deltaX = clientX - state.startX
  const deltaY = clientY - state.startY

  if (deltaY < -12 || Math.abs(deltaY) > Math.abs(deltaX) * 1.25) {
    return
  }

  if (Math.abs(deltaX) > 6 || Math.abs(deltaY) > 6) {
    state.hasMoved = true
  }

  if (e instanceof TouchEvent && Math.abs(deltaX) > 10) {
    e.preventDefault()
  }

  const visualDown = Math.max(0, deltaY) * 0.35 + Math.abs(deltaX) * 0.14
  state.offsetX = Math.max(-MAX_OFFSET_X, Math.min(MAX_OFFSET_X, deltaX))
  state.offsetY = Math.max(0, Math.min(MAX_OFFSET_Y, visualDown))
}

function resetSwipeState(id: string) {
  const state = swipeState[id]
  if (!state) return
  state.offsetX = 0
  state.offsetY = 0
}

function onTouchEnd(todo: Todo) {
  if (props.multiSelectMode) return
  const state = swipeState[todo.id]
  if (!state) return

  const hadMoved = state.hasMoved
  state.isDragging = false

  if (hadMoved) {
    setTimeout(() => {
      state.hasMoved = false
    }, 50)
  } else {
    state.hasMoved = false
  }

  const shouldTrigger = state.offsetY >= MIN_TRIGGER_Y
  if (props.showRecycleBin) {
    if (shouldTrigger && state.offsetX <= -SWIPE_THRESHOLD) {
      emit('delete', todo.id, 'permanent')
      resetSwipeState(todo.id)
      return
    }

    if (shouldTrigger && state.offsetX >= SWIPE_THRESHOLD) {
      emit('restore', todo.id)
      resetSwipeState(todo.id)
      return
    }

    resetSwipeState(todo.id)
    return
  }

  if (shouldTrigger && state.offsetX <= -SWIPE_THRESHOLD) {
    emit('togglePin', todo)
    resetSwipeState(todo.id)
    return
  }

  if (shouldTrigger && state.offsetX >= SWIPE_THRESHOLD) {
    emit('delete', todo.id, 'soft')
    resetSwipeState(todo.id)
    return
  }

  resetSwipeState(todo.id)
}

function handleCardClick(todo: Todo) {
  if (consumeLongPress(todo)) return
  const state = swipeState[todo.id]
  if (state?.hasMoved) return
  if (props.multiSelectMode) {
    emit('toggleSelect', todo)
    return
  }
  if (props.showRecycleBin) return
  emit('edit', todo)
}

function isSelected(id: string): boolean {
  return props.selectedIds?.includes(id) ?? false
}

function getCardStyle(id: string) {
  const state = swipeState[id]
  if (!state) return {}

  const rotate = state.offsetX / 18
  return {
    transform: `translate3d(${state.offsetX}px, ${state.offsetY}px, 0) rotate(${rotate}deg)`,
    transition: state.isDragging ? 'none' : 'transform 0.28s ease',
  }
}

function getLeftActionStyle(id: string) {
  const state = swipeState[id]
  if (!state) return { opacity: 0 }

  const progress = Math.min(1, Math.max(0, state.offsetX / SWIPE_THRESHOLD))
  return {
    opacity: progress,
    transform: `translateX(${(-18 + progress * 18).toFixed(2)}px) scale(${(0.88 + progress * 0.12).toFixed(3)})`,
  }
}

function getRightActionStyle(id: string) {
  const state = swipeState[id]
  if (!state) return { opacity: 0 }

  const progress = Math.min(1, Math.max(0, -state.offsetX / SWIPE_THRESHOLD))
  return {
    opacity: progress,
    transform: `translateX(${(18 - progress * 18).toFixed(2)}px) scale(${(0.88 + progress * 0.12).toFixed(3)})`,
  }
}
</script>

<template>
  <div class="important-days-container">
    <div v-if="importantDays.length === 0" class="empty-wrapper">
      <ElEmpty :description="showRecycleBin ? '回收站是空的' : '暂无重要日'">
        <template #description>
          <div style="text-align: center; color: var(--el-text-color-secondary)">
            <p>{{ showRecycleBin ? '回收站是空的' : '暂无重要日' }}</p>
            <p v-if="!showRecycleBin" style="font-size: 12px; margin-top: 8px">给待办添加 "重要日" 标签即可显示</p>
          </div>
        </template>
      </ElEmpty>
    </div>
    
    <div v-else class="important-days-grid">
      <div
        v-for="item in importantDays"
        :key="item.todo.id"
        class="important-day-swipe-item"
        @touchstart.passive="(event: Event) => { startLongPress(item.todo, event); onTouchStart(event, item.todo.id) }"
        @touchmove="(event: Event) => { cancelLongPress(item.todo); onTouchMove(event, item.todo.id) }"
        @touchend="() => { cancelLongPress(item.todo); onTouchEnd(item.todo) }"
        @touchcancel="cancelLongPress(item.todo)"
        @mousedown="(event: Event) => { startLongPress(item.todo, event); onTouchStart(event, item.todo.id) }"
        @mousemove="(event: Event) => { cancelLongPress(item.todo); onTouchMove(event, item.todo.id) }"
        @mouseup="() => { cancelLongPress(item.todo); onTouchEnd(item.todo) }"
        @mouseleave="() => { cancelLongPress(item.todo); onTouchEnd(item.todo) }"
      >
        <div class="swipe-action" :class="showRecycleBin ? 'restore-action' : 'left-action'" :style="getLeftActionStyle(item.todo.id)">
          <ElIcon :size="24">
            <RefreshRight v-if="showRecycleBin" />
            <Delete v-else />
          </ElIcon>
          <span class="action-text">{{ showRecycleBin ? '恢复' : '删除' }}</span>
        </div>

        <div class="swipe-action" :class="showRecycleBin ? 'permanent-delete-action' : 'right-action'" :style="getRightActionStyle(item.todo.id)">
          <ElIcon :size="24">
            <Delete v-if="showRecycleBin" />
            <Star v-else />
          </ElIcon>
          <span class="action-text">{{ showRecycleBin ? '永久删除' : (item.todo.is_pinned ? '取消收藏' : '收藏') }}</span>
        </div>

        <ElCard
          class="important-day-card"
          :class="{ 'is-pinned': item.todo.is_pinned, 'is-countdown': item.type === 'countdown', 'is-countup': item.type === 'countup', 'is-recycle-bin': showRecycleBin, 'is-selected': isSelected(item.todo.id) }"
          :style="getCardStyle(item.todo.id)"
          shadow="hover"
          @click="handleCardClick(item.todo)"
        >
          <div v-if="multiSelectMode" class="select-indicator" :class="{ 'is-selected': isSelected(item.todo.id) }">
            <ElIcon><Select /></ElIcon>
          </div>
          <!-- 置顶标记 -->
          <div v-if="item.todo.is_pinned" class="pin-badge">
            <ElIcon :size="18"><Star /></ElIcon>
          </div>

          <!-- 类型标记 -->
          <div class="type-badge" :class="item.type">
            <ElIcon>
              <ArrowDown v-if="item.type === 'countdown'" />
              <ArrowUp v-else />
            </ElIcon>
            <span>{{ item.type === 'countdown' ? '倒计时' : '正计时' }}</span>
          </div>

          <!-- 标题 -->
          <div class="title">{{ item.todo.title }}</div>

          <!-- 主要数字显示 -->
          <div class="days-display">
            <template v-if="item.todo.start_date || item.todo.end_date">
              <div class="days-label">
                {{ item.type === 'countdown' ? '还剩' : '已经' }}
              </div>
              <template v-if="item.type === 'countup' && item.years > 0">
                <div class="days-number-wrap countup-split" :class="{ 'is-hover-toggle': canToggleCountupDisplay(item) }">
                  <div class="days-number countup countup-main countup-default">
                    <span class="years">{{ item.years }}</span>
                    <span class="countup-side countup-default">
                      <span class="countup-unit">年</span>
                      <span v-if="item.days > 0" class="countup-extra">
                        <span class="countup-extra-value">+{{ item.days }}</span>
                        <span class="countup-extra-unit">天</span>
                      </span>
                    </span>
                  </div>
                  <div class="days-number countup countup-total-days countup-hover">
                    <span class="days">{{ item.totalDays }}</span>
                    <span class="unit">天</span>
                  </div>
                </div>
              </template>
              <template v-else-if="item.type === 'countdown' && canToggleYearDayDisplay(item)">
                <div class="days-number-wrap is-hover-toggle">
                  <div class="days-number countdown countup-default">
                    <span class="days">{{ item.totalDays }}</span>
                    <span class="unit">天</span>
                  </div>
                  <div class="countup-hover countdown-hover-detail">
                    <div class="days-number countdown countup-main">
                      <span class="years">{{ item.years }}</span>
                      <span class="countup-side">
                        <span class="countup-unit">年</span>
                        <span v-if="item.days > 0" class="countup-extra">
                          <span class="countup-extra-value">+{{ item.days }}</span>
                          <span class="countup-extra-unit">天</span>
                        </span>
                      </span>
                    </div>
                  </div>
                </div>
              </template>
              <div v-else class="days-number" :class="item.type">
                <span class="days">{{ item.type === 'countdown' ? item.totalDays : Math.abs(item.days) }}</span>
                <span class="unit">天</span>
              </div>
            </template>
            <template v-else>
              <div class="days-label">{{ showRecycleBin && item.todo.deleted_at ? '回收站保留' : '点击编辑设置' }}</div>
              <div class="days-number no-date">
                <span class="no-date-text">{{ showRecycleBin && item.todo.deleted_at ? getTrashRemainingDeleteText(item.todo.deleted_at) : '未设置日期' }}</span>
              </div>
            </template>
          </div>

          <!-- 描述 -->
          <div v-if="item.todo.description" class="description">
            {{ item.todo.description }}
          </div>

          <!-- 标签 -->
          <div v-if="getOtherTags(item.todo.tags).length > 0" class="tags">
            <ElTag
              v-for="tag in getOtherTags(item.todo.tags)"
              :key="tag"
              size="small"
              effect="plain"
            >
              {{ tag }}
            </ElTag>
          </div>

          <!-- 循环标记 -->
          <div v-if="isYearlyRecurrence(item.todo)" class="recurrence-badge">
            <ElIcon><RefreshRight /></ElIcon>
            <span>{{ item.todo.recurrence_type === 'yearly' ? '每年' : '每月' }}重复</span>
          </div>

          <!-- 日期信息 -->
          <ElTooltip
            v-if="showRecycleBin && item.todo.deleted_at"
            placement="top"
            :show-after="120"
            popper-class="trash-date-tooltip-popper"
          >
            <template #content>
              <div class="trash-date-tooltip">
                <div>删除于: {{ formatPreciseDateTime(item.todo.deleted_at) }}</div>
                <div class="trash-date-tooltip-sub">自动删除于: {{ formatPreciseDateTime(getTrashExpireAt(item.todo.deleted_at)) }}</div>
              </div>
            </template>
            <div class="date-info date-info-trash">
              <ElIcon><Calendar /></ElIcon>
              <span>
                删除于: {{ formatDeletedDate(item.todo.deleted_at) }}
                <br>
                <small class="trash-date-info-sub">{{ getTrashRemainingDeleteText(item.todo.deleted_at) }}</small>
              </span>
            </div>
          </ElTooltip>
          <div v-else-if="item.todo.start_date || item.todo.end_date" class="date-info">
            <ElIcon><Calendar /></ElIcon>
            <span v-if="item.type === 'countdown'">
              目标: {{ formatDate(item.targetDate) }}
              <template v-if="isYearlyRecurrence(item.todo)">
                <br>
                <small class="anniversary-placeholder" />
              </template>
            </span>
            <span v-else>
              始于: {{ formatDate(item.targetDate) }}
              <template v-if="isYearlyRecurrence(item.todo)">
                <br>
                <small v-if="item.nextAnniversary" style="color: var(--el-text-color-secondary)">
                  下次: {{ formatDate(item.nextAnniversary) }}
                </small>
                <small v-else class="anniversary-placeholder" />
              </template>
            </span>
          </div>
        </ElCard>
      </div>
    </div>
  </div>
</template>

<style scoped>
.important-days-container {
  padding: 16px;
}

.empty-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.important-days-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  align-items: start;
}

.important-day-swipe-item {
  position: relative;
  touch-action: pan-y;
  user-select: none;
}

.swipe-action {
  position: absolute;
  top: 10px;
  bottom: 10px;
  width: 96px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: #fff;
  border-radius: 14px;
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.left-action {
  left: 0;
  background: linear-gradient(135deg, #f56c6c 0%, #fb8b8b 100%);
}

.right-action {
  right: 0;
  background: linear-gradient(135deg, #e6a23c 0%, #f3c266 100%);
}

.restore-action {
  left: 0;
  background: linear-gradient(90deg, var(--el-color-success) 0%, var(--el-color-success-light-3) 100%);
}

.permanent-delete-action {
  right: 0;
  background: linear-gradient(270deg, #f56c6c 0%, #f89898 100%);
}

.action-text {
  font-size: 12px;
  font-weight: 600;
}

.important-day-card {
  position: relative;
  transition: all 0.3s ease;
  border-radius: 12px;
  z-index: 1;
  cursor: pointer;
  transform-origin: center center;
}

.important-day-card.is-selected {
  box-shadow: 0 0 0 2px rgb(var(--el-color-primary-rgb) / 0.35);
  background: color-mix(in srgb, var(--el-color-primary-light-9) 66%, white);
}

.important-day-card:hover {
  transform: translateY(-2px);
}

.important-day-card:active {
  cursor: grabbing;
}

.important-day-card.is-recycle-bin {
  cursor: default;
}

.important-day-card.is-pinned {
  border: 2px solid var(--el-color-warning);
}

.important-day-card.is-countdown {
  background: linear-gradient(135deg, var(--el-color-primary-light-9) 0%, var(--el-bg-color) 100%);
}

.important-day-card.is-countup {
  background: linear-gradient(135deg, var(--el-color-success-light-9) 0%, var(--el-bg-color) 100%);
}

.pin-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  color: var(--el-color-warning);
  font-size: 16px;
}

.type-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.type-badge.countdown {
  background: var(--el-color-primary-light-8);
  color: var(--el-color-primary);
}

.type-badge.countup {
  background: var(--el-color-success-light-8);
  color: var(--el-color-success);
}

.days-display {
  text-align: center;
  padding: 8px 0 16px;
  min-height: 80px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.days-number {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: baseline;
  justify-items: center;
  line-height: 1;
}

.days-number-wrap {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  min-height: 56px;
}

.countup-default,
.countup-hover {
  transition: opacity 0.18s ease;
}

.days-number-wrap.countup-split {
  align-items: center;
}

.countup-main {
  width: 100%;
}

.countup-hover {
  position: absolute;
  inset: 0;
  opacity: 0;
  pointer-events: none;
}

.days-number-wrap.is-hover-toggle:hover .countup-default {
  opacity: 0;
}

.days-number-wrap.is-hover-toggle:hover .countup-hover {
  opacity: 1;
}

.countdown-hover-detail {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.countdown-hover-detail .countup-main {
  position: static;
}

.countdown-hover-detail .countup-extra-value {
  color: var(--el-color-primary);
}

.days-number .years,
.days-number .days {
  grid-column: 2;
}

.days-number .unit,
.countup-side {
  grid-column: 3;
  justify-self: start;
  margin-left: 4px;
}

.countup-side {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
}

.countup-unit {
  position: static;
  font-size: 18px;
  font-weight: 500;
  color: var(--el-text-color-secondary);
}

.days-number .years,
.days-number .days {
  font-size: 48px;
  font-weight: 700;
}

.days-number.countdown .years,
.days-number.countdown .days {
  color: var(--el-color-primary);
}

.days-number.countup .years,
.days-number.countup .days {
  color: var(--el-color-success);
}

.days-number .unit {
  font-size: 18px;
  font-weight: 500;
  color: var(--el-text-color-secondary);
}

.days-number .plus-days {
  font-size: 16px;
  color: var(--el-text-color-secondary);
  margin-left: 4px;
}

.countup-extra {
  display: flex;
  align-items: baseline;
  gap: 2px;
  font-size: 16px;
  font-weight: 600;
  line-height: 1;
}

.countup-extra-value {
  color: var(--el-color-success);
}

.countup-extra-unit {
  color: var(--el-text-color-secondary);
}

.days-number.no-date {
  padding: 12px 0;
}

.days-number .no-date-text {
  font-size: 18px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
}

.days-label {
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.title {
  font-size: 16px;
  font-weight: 600;
  text-align: center;
  color: var(--el-text-color-primary);
  margin-top: 8px;
  margin-bottom: 8px;
  word-break: break-all;
}

.date-info {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 6px;
  font-size: 13px;
  color: var(--el-text-color-regular);
  text-align: center;
  margin-top: 8px;
  min-height: 36px;
}

.date-info-trash {
  cursor: help;
}

.anniversary-placeholder {
  display: inline-block;
  height: 1.5em;
}

.date-info .el-icon {
  margin-top: 2px;
  flex-shrink: 0;
}

.trash-date-info-sub,
.trash-date-tooltip-sub {
  color: var(--el-text-color-secondary);
}

.trash-date-tooltip {
  display: grid;
  gap: 4px;
  line-height: 1.5;
}

.description {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  text-align: center;
  margin-bottom: 12px;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
  margin-bottom: 12px;
}

.recurrence-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 12px;
  color: var(--el-color-info);
  margin-bottom: 12px;
}

/* 深色模式适配 */
.dark .important-day-card.is-countdown {
  background: linear-gradient(135deg, var(--el-color-primary-dark-8) 0%, var(--el-bg-color) 100%);
}

.dark .important-day-card.is-countup {
  background: linear-gradient(135deg, var(--el-color-success-dark-8) 0%, var(--el-bg-color) 100%);
}

.dark .important-day-card.is-selected {
  background: rgb(var(--el-color-primary-rgb) / 0.18);
}

/* 深色模式文字颜色调整 */
.dark .title {
  color: #ffffff;
}

.dark .days-label {
  color: #ffffff;
}

.dark .days-number .unit,
.dark .days-number .plus-days {
  color: #ffffff;
}

.dark .date-info {
  color: #ffffff;
}

.dark .date-info small {
  color: var(--el-text-color-secondary) !important;
}

.dark .description {
  color: var(--el-text-color-secondary);
}

.dark .recurrence-badge {
  color: #ffffff;
}

.dark .type-badge.countdown {
  background: var(--el-color-primary);
  color: #ffffff;
}

.dark .type-badge.countup {
  background: var(--el-color-success);
  color: #ffffff;
}

.select-indicator {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 26px;
  height: 26px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.85);
  color: var(--el-text-color-secondary);
  z-index: 2;
}

.select-indicator.is-selected {
  background: var(--el-color-primary);
  color: #fff;
}
</style>
