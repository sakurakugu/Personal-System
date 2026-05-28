<script setup lang="ts">
import { 使用手机使用统计存储 } from '@personal-system/domain/phone-usage'
import { PageSectionShell } from '@personal-system/ui'
import { ElMessage } from 'element-plus'
import { computed, nextTick, onMounted, ref } from 'vue'

const phoneUsage = 使用手机使用统计存储()
interface 趋势图元素 {
  scrollLeft: number
  scrollWidth: number
  clientWidth: number
  querySelector: (selector: string) => null | {
    offsetWidth: number
  }
}

const trendChartRef = ref<趋势图元素 | null>(null)
const 已滚动趋势图 = ref(false)
const 趋势可见开始索引 = ref(7)
const 趋势可见结束索引 = ref(13)
const 选中日期 = ref('')

const statCards = computed(() => [
  {
    label: '亮屏',
    value: `${phoneUsage.今日汇总.亮屏次数}`,
    hint: 格式化时长(phoneUsage.今日汇总.亮屏总时长毫秒),
  },
  {
    label: '解锁',
    value: `${phoneUsage.今日汇总.解锁次数}`,
    hint: 格式化时长(phoneUsage.今日汇总.解锁使用总时长毫秒),
  },
  {
    label: '使用中',
    value: phoneUsage.当前状态.是否正在使用手机 ? '是' : '否',
    hint: phoneUsage.当前状态.是否亮屏 ? '当前亮屏' : '当前未亮屏',
  },
])
const 可滚动汇总列表 = computed(() => phoneUsage.最近14天汇总列表)
const 当前选中日期 = computed(() => 选中日期.value || phoneUsage.今日汇总.日期)
const 选中日期汇总 = computed(() => {
  const fallback = phoneUsage.今日汇总
  return 可滚动汇总列表.value.find((item) => item.日期 === 当前选中日期.value) ?? fallback
})
const 选中日期解锁时间点 = computed(() => (
  选中日期汇总.value.解锁时间点列表.map((timestamp) => 格式化时间点(timestamp))
))
const 趋势标题 = computed(() => {
  if (!已滚动趋势图.value) {
    return '最近 7 天解锁次数'
  }

  const startDate = 可滚动汇总列表.value[趋势可见开始索引.value]?.日期
  const endDate = 可滚动汇总列表.value[趋势可见结束索引.value]?.日期
  if (!startDate || !endDate) {
    return '最近 7 天解锁次数'
  }
  return `${格式化短日期(startDate)} ~ ${格式化短日期(endDate)} 解锁次数`
})
const 解锁时间点标题 = computed(() => {
  if (当前选中日期.value === phoneUsage.今日汇总.日期) {
    return '今天解锁时间点'
  }
  return `${格式化短日期(当前选中日期.value)} 解锁时间点`
})
const maxUnlockCount = computed(() => Math.max(
  1,
  ...可滚动汇总列表.value.map((item) => item.解锁次数),
))
const permissionText = computed(() => (
  phoneUsage.元数据.是否已授权使用情况访问 ? '已授权' : '未授权'
))
const lastCollectedText = computed(() => (
  phoneUsage.元数据.最后采集时间戳
    ? 格式化完整时间(phoneUsage.元数据.最后采集时间戳)
    : '尚未采集'
))

function 格式化时长(milliseconds: number) {
  const totalMinutes = Math.max(0, Math.round(milliseconds / 60000))
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  if (hours <= 0) {
    return `${minutes} 分钟`
  }
  return `${hours} 小时 ${minutes} 分钟`
}

function 格式化时间点(timestamp: number) {
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(new Date(timestamp))
}

function 格式化短日期(dateKey: string) {
  return dateKey.slice(5)
}

function 格式化完整时间(timestamp: number) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(new Date(timestamp))
}

function 获取趋势柱高度(unlockCount: number) {
  return `${Math.max(8, Math.round((unlockCount / maxUnlockCount.value) * 72))}px`
}

function 同步趋势可见区间(isUserScroll = true) {
  const chart = trendChartRef.value
  if (!chart) {
    return
  }

  const firstItem = chart.querySelector('.trend-chart__item')
  if (!firstItem) {
    return
  }

  const itemGap = Number.parseFloat(
    window.getComputedStyle(chart as Parameters<typeof window.getComputedStyle>[0]).columnGap || '0',
  )
  const itemWidth = firstItem.offsetWidth + itemGap
  if (itemWidth <= 0) {
    return
  }

  const visibleCount = Math.min(7, 可滚动汇总列表.value.length)
  const maxStartIndex = Math.max(0, 可滚动汇总列表.value.length - visibleCount)
  const startIndex = Math.min(maxStartIndex, Math.max(0, Math.round(chart.scrollLeft / itemWidth)))
  趋势可见开始索引.value = startIndex
  趋势可见结束索引.value = Math.min(可滚动汇总列表.value.length - 1, startIndex + visibleCount - 1)
  已滚动趋势图.value = isUserScroll && chart.scrollLeft < chart.scrollWidth - chart.clientWidth - 2
}

async function 滚动到最近7天() {
  await nextTick()
  const chart = trendChartRef.value
  if (!chart) {
    return
  }
  chart.scrollLeft = chart.scrollWidth - chart.clientWidth
  同步趋势可见区间(false)
}

function handleSelectDate(dateKey: string) {
  选中日期.value = dateKey
}

async function handleRefresh() {
  try {
    await phoneUsage.补采屏幕使用事件()
    if (!phoneUsage.元数据.是否已授权使用情况访问) {
      ElMessage.warning('请先在系统设置中开启使用情况访问')
      return
    }
    ElMessage.success('手机使用统计已刷新')
  } catch {
    ElMessage.error(phoneUsage.最后错误 || '刷新手机使用统计失败')
  }
}

async function handleOpenPermissionSettings() {
  await phoneUsage.打开使用情况权限设置()
}

onMounted(() => {
  void phoneUsage.补采屏幕使用事件()
  void 滚动到最近7天()
})
</script>

<template>
  <section class="page phone-usage-page">
    <PageSectionShell
      title="手机使用"
      to="/me"
      :show-back="true"
    >
      <template #header-extra>
        <button
          class="refresh-button"
          type="button"
          :disabled="phoneUsage.正在补采"
          @click="handleRefresh"
        >
          {{ phoneUsage.正在补采 ? '刷新中' : '刷新' }}
        </button>
      </template>
    </PageSectionShell>

    <section
      v-if="!phoneUsage.元数据.是否已授权使用情况访问"
      class="permission-panel"
    >
      <div class="permission-panel__text">
        <strong>需要使用情况访问权限</strong>
        <span>开启后才能读取系统记录的亮屏和解锁事件。</span>
      </div>
      <button class="primary-button" type="button" @click="handleOpenPermissionSettings">
        去设置
      </button>
    </section>

    <section class="status-row">
      <span>权限：{{ permissionText }}</span>
      <span>最后采集：{{ lastCollectedText }}</span>
    </section>

    <section class="stat-grid" aria-label="今日手机使用统计">
      <article v-for="item in statCards" :key="item.label" class="stat-card">
        <span class="stat-card__label">{{ item.label }}</span>
        <strong class="stat-card__value">{{ item.value }}</strong>
        <span class="stat-card__hint">{{ item.hint }}</span>
      </article>
    </section>

    <section class="panel-card trend-panel">
      <div class="section-heading">
        <strong class="section-title">{{ 趋势标题 }}</strong>
      </div>

      <div
        ref="trendChartRef"
        class="trend-chart"
        @scroll.passive="同步趋势可见区间(true)"
      >
        <button
          v-for="item in 可滚动汇总列表"
          :key="item.日期"
          class="trend-chart__item"
          :class="{ 'trend-chart__item--active': item.日期 === 当前选中日期 }"
          type="button"
          @click="handleSelectDate(item.日期)"
        >
          <span class="trend-chart__value">{{ item.解锁次数 }}</span>
          <span class="trend-chart__bar" :style="{ height: 获取趋势柱高度(item.解锁次数) }" />
          <span class="trend-chart__date">{{ 格式化短日期(item.日期) }}</span>
        </button>
      </div>
    </section>

    <section class="panel-card unlock-panel">
      <div class="section-heading">
        <strong class="section-title">{{ 解锁时间点标题 }}</strong>
        <span class="panel-meta">{{ 选中日期解锁时间点.length }} 次</span>
      </div>

      <div v-if="选中日期解锁时间点.length > 0" class="unlock-list">
        <span
          v-for="time in 选中日期解锁时间点"
          :key="time"
          class="unlock-chip"
        >
          {{ time }}
        </span>
      </div>

      <p v-else class="empty-text">
        这天还没有采集到解锁事件
      </p>
    </section>
  </section>
</template>

<style scoped>
.phone-usage-page {
  width: min(430px, 100%);
  display: grid;
  gap: 14px;
  align-content: start;
  margin: 0 auto;
}

.refresh-button {
  flex: 0 0 auto;
  height: 36px;
  padding: 0 14px;
  border: 1px solid var(--theme-card-border);
  border-radius: 12px;
  color: var(--theme-accent-strong);
  background: var(--theme-panel-soft);
  cursor: pointer;
}

.refresh-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.permission-panel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid color-mix(in srgb, var(--theme-danger-strong) 28%, var(--theme-card-border));
  border-radius: 18px;
  background: color-mix(in srgb, var(--theme-danger-soft) 42%, var(--theme-panel-soft));
}

.permission-panel__text {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.permission-panel__text span {
  color: var(--text-tertiary);
  font-size: 0.9rem;
  line-height: 1.45;
}

.status-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  color: var(--text-tertiary);
  font-size: 0.85rem;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.stat-card {
  min-width: 0;
  display: grid;
  gap: 5px;
  padding: 14px 12px;
  border: 1px solid var(--theme-card-border);
  border-radius: 18px;
  background: var(--theme-card-bg);
}

.stat-card__label,
.stat-card__hint {
  color: var(--text-tertiary);
  font-size: 0.78rem;
  line-height: 1.25;
}

.stat-card__value {
  color: var(--text-primary);
  font-size: 1.28rem;
  line-height: 1.15;
  word-break: break-all;
}

.trend-panel,
.unlock-panel {
  display: grid;
  gap: 14px;
  padding: 16px;
}

.trend-chart {
  display: flex;
  align-items: end;
  gap: 8px;
  min-height: 112px;
  overflow-x: auto;
  overscroll-behavior-x: contain;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
}

.trend-chart::-webkit-scrollbar {
  display: none;
}

.trend-chart__item {
  flex: 0 0 calc((100% - 48px) / 7);
  min-width: calc((100% - 48px) / 7);
  display: grid;
  justify-items: center;
  align-items: end;
  gap: 6px;
  padding: 0;
  border: 0;
  color: inherit;
  background: transparent;
  cursor: pointer;
  scroll-snap-align: start;
}

.trend-chart__value {
  color: var(--text-tertiary);
  font-size: 0.74rem;
  line-height: 1;
}

.trend-chart__bar {
  width: 100%;
  max-width: 24px;
  border-radius: 8px 8px 3px 3px;
  background: var(--theme-accent-gradient);
  opacity: 0.72;
  transition:
    opacity 0.18s ease,
    transform 0.18s ease;
}

.trend-chart__date {
  color: var(--text-tertiary);
  font-size: 0.72rem;
  line-height: 1;
}

.trend-chart__item--active .trend-chart__value,
.trend-chart__item--active .trend-chart__date {
  color: var(--theme-accent-strong);
  font-weight: 700;
}

.trend-chart__item--active .trend-chart__bar {
  opacity: 1;
  transform: scaleX(1.14);
}

.unlock-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.unlock-chip {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  border-radius: 10px;
  color: var(--theme-accent-strong);
  background: var(--theme-accent-soft);
  font-size: 0.9rem;
  font-weight: 600;
}

.empty-text {
  margin: 0;
  color: var(--text-tertiary);
  font-size: 0.92rem;
}
</style>
