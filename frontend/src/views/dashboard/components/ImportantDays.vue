<script setup lang="ts">
import { computed } from 'vue'
import { ElButton, ElCard, ElEmpty, ElIcon, ElTag, ElTooltip } from 'element-plus'
import { Star, Calendar, ArrowUp, ArrowDown, Edit, Delete, RefreshRight } from '@element-plus/icons-vue'
import type { Todo } from '../../../stores/todo'

interface Props {
  todos: Todo[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  edit: [todo: Todo]
  delete: [id: string, mode: 'soft' | 'permanent']
  togglePin: [todo: Todo]
  changeStatus: [todo: Todo]
}>()

// 判断是否为重要日（包含"重要日"标签）
function isImportantDay(todo: Todo): boolean {
  if (!todo.tags) return false
  return todo.tags.split(/[,，]/).map(t => t.trim()).includes('重要日')
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

// 计算上一个周年日的年份
function getLastAnniversaryYear(startDate: Date): number {
  const today = getToday()
  const currentYear = today.getFullYear()
  const anniversaryThisYear = new Date(currentYear, startDate.getMonth(), startDate.getDate())
  
  // 如果今年的纪念日已过，取今年；否则取去年
  if (anniversaryThisYear <= today) {
    return currentYear
  }
  return currentYear - 1
}

// 重要日信息接口
interface ImportantDayInfo {
  todo: Todo
  type: 'countdown' | 'countup' // countdown: 倒计时, countup: 正计时
  days: number // 天数
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
      const years = getLastAnniversaryYear(startDate) - startDate.getFullYear()
      const lastAnniversary = new Date(getLastAnniversaryYear(startDate), startDate.getMonth(), startDate.getDate())
      const days = getDaysDiff(lastAnniversary, today)
      
      list.push({
        todo,
        type: 'countup',
        days,
        years,
        targetDate: startDate,
        nextAnniversary: new Date(getNextAnniversaryYear(startDate), startDate.getMonth(), startDate.getDate())
      })
      continue
    }

    // 情况2: 只有 end_date -> 倒计时（到 end_date 还剩多少天）
    if (!startDate && endDate) {
      const days = getDaysDiff(today, endDate)
      list.push({
        todo,
        type: 'countdown',
        days,
        years: 0,
        targetDate: endDate
      })
      continue
    }

    // 情况3: 两者都有，根据日期判断
    if (startDate && endDate) {
      // 如果 end_date 在未来，显示倒计时
      if (endDate > today) {
        const days = getDaysDiff(today, endDate)
        list.push({
          todo,
          type: 'countdown',
          days,
          years: 0,
          targetDate: endDate
        })
      } else {
        // end_date 已过，转换为正计时（从 start_date 开始）
        const years = getLastAnniversaryYear(startDate) - startDate.getFullYear()
        const lastAnniversary = new Date(getLastAnniversaryYear(startDate), startDate.getMonth(), startDate.getDate())
        const days = getDaysDiff(lastAnniversary, today)
        
        list.push({
          todo,
          type: 'countup',
          days,
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
        return a.days - b.days // 倒计时：天数少的在前
      } else {
        return b.years - a.years || b.days - a.days // 正计时：年数/天数多的在前
      }
    }
    // 倒计时优先于正计时
    return a.type === 'countdown' ? -1 : 1
  })
})

// 获取其他标签（排除"重要日"）
function getOtherTags(tagsStr: string | null): string[] {
  if (!tagsStr) return []
  return tagsStr.split(/[,，]/).map(t => t.trim()).filter(t => t && t !== '重要日')
}

// 格式化日期显示
function formatDate(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// 判断是否循环
function isYearlyRecurrence(todo: Todo): boolean {
  return todo.recurrence_type === 'yearly' || todo.recurrence_type === 'monthly'
}
</script>

<template>
  <div class="important-days-container">
    <div v-if="importantDays.length === 0" class="empty-wrapper">
      <ElEmpty description="暂无重要日">
        <template #description>
          <div style="text-align: center; color: var(--el-text-color-secondary)">
            <p>暂无重要日</p>
            <p style="font-size: 12px; margin-top: 8px">给待办添加 "重要日" 标签即可显示</p>
          </div>
        </template>
      </ElEmpty>
    </div>
    
    <div v-else class="important-days-grid">
      <ElCard
        v-for="item in importantDays"
        :key="item.todo.id"
        class="important-day-card"
        :class="{ 'is-pinned': item.todo.is_pinned, 'is-countdown': item.type === 'countdown', 'is-countup': item.type === 'countup' }"
        shadow="hover"
      >
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

        <!-- 日期信息 -->
        <div v-if="item.todo.start_date || item.todo.end_date" class="date-info">
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
              <small v-else class="anniversary-placeholder"></small>
            </template>
          </span>
        </div>

        <!-- 主要数字显示 -->
        <div class="days-display">
          <template v-if="item.todo.start_date || item.todo.end_date">
            <div class="days-label">
              {{ item.type === 'countdown' ? '还剩' : '已经' }}
            </div>
            <div class="days-number" :class="item.type">
              <template v-if="item.type === 'countup' && item.years > 0">
                <span class="years">{{ item.years }}</span>
                <span class="unit">年</span>
                <span v-if="item.days > 0" class="plus-days">+{{ item.days }}天</span>
              </template>
              <template v-else>
                <span class="days">{{ Math.abs(item.days) }}</span>
                <span class="unit">天</span>
              </template>
            </div>
          </template>
          <template v-else>
            <div class="days-label">点击编辑设置</div>
            <div class="days-number no-date">
              <span class="no-date-text">未设置日期</span>
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

        <!-- 操作按钮 -->
        <div class="actions">
          <ElTooltip content="编辑">
            <ElButton
              type="primary"
              text
              circle
              size="small"
              @click="emit('edit', item.todo)"
            >
              <ElIcon :size="18"><Edit /></ElIcon>
            </ElButton>
          </ElTooltip>
          <ElTooltip :content="item.todo.is_pinned ? '取消置顶' : '置顶'">
            <ElButton
              type="warning"
              text
              circle
              size="small"
              @click="emit('togglePin', item.todo)"
            >
              <ElIcon :size="18"><Star /></ElIcon>
            </ElButton>
          </ElTooltip>
          <ElTooltip content="删除">
            <ElButton
              type="danger"
              text
              circle
              size="small"
              @click="emit('delete', item.todo.id, 'soft')"
            >
              <ElIcon :size="18"><Delete /></ElIcon>
            </ElButton>
          </ElTooltip>
        </div>
      </ElCard>
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
}

.important-day-card {
  position: relative;
  transition: all 0.3s ease;
  border-radius: 12px;
}

.important-day-card:hover {
  transform: translateY(-2px);
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
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
  line-height: 1;
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
  margin-bottom: 8px;
  min-height: 36px;
}

.anniversary-placeholder {
  display: inline-block;
  height: 1.5em;
}

.date-info .el-icon {
  margin-top: 2px;
  flex-shrink: 0;
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

.actions {
  display: flex;
  justify-content: center;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

/* 深色模式适配 */
.dark .important-day-card.is-countdown {
  background: linear-gradient(135deg, var(--el-color-primary-dark-8) 0%, var(--el-bg-color) 100%);
}

.dark .important-day-card.is-countup {
  background: linear-gradient(135deg, var(--el-color-success-dark-8) 0%, var(--el-bg-color) 100%);
}

.dark .actions {
  border-top-color: var(--el-border-color);
}

.dark .actions .el-button {
  color: var(--el-text-color-regular);
  background-color: transparent;
  border-color: transparent;
}

.dark .actions .el-button--primary {
  color: var(--el-color-primary);
  background-color: transparent;
  border-color: transparent;
}

.dark .actions .el-button--warning {
  color: var(--el-color-warning);
  background-color: transparent;
  border-color: transparent;
}

.dark .actions .el-button--danger {
  color: var(--el-color-danger);
  background-color: transparent;
  border-color: transparent;
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
</style>
