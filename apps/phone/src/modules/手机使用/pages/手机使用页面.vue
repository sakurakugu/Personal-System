<script setup lang="ts">
import { 使用手机使用统计存储 } from '@personal-system/domain/phone-usage'
import { PageSectionShell, SegmentedSwitch } from '@personal-system/ui'
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

type 使用时段类型 = '使用' | '未用'

interface 可高亮时段 {
  开始时间戳: number
  结束时间戳: number
  类型: 使用时段类型
}

const trendChartRef = ref<趋势图元素 | null>(null)
const 已滚动趋势图 = ref(false)
const 趋势可见开始索引 = ref(7)
const 趋势可见结束索引 = ref(13)
const 选中日期 = ref('')
const 高亮时段 = ref<可高亮时段 | null>(null)
const 高亮解锁时间戳 = ref<number | null>(null)
const 使用时段展示模式 = ref<'使用' | '未用' | '占比'>('使用')
const 使用时段展示选项 = [
  { label: '使用', value: '使用' },
  { label: '未用', value: '未用' },
  { label: '占比', value: '占比' },
] as const

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
const 可滚动汇总列表 = computed(() => phoneUsage.最近历史汇总列表)
const 当前选中日期 = computed(() => 选中日期.value || phoneUsage.今日汇总.日期)
const 选中日期汇总 = computed(() => {
  const fallback = phoneUsage.今日汇总
  return 可滚动汇总列表.value.find((item) => item.日期 === 当前选中日期.value) ?? fallback
})
const 选中日期解锁时间点 = computed(() => (
  选中日期汇总.value.解锁时间点列表.map((timestamp) => ({
    时间戳: timestamp,
    文本: 格式化时间点(timestamp),
  }))
))
const 选中日期使用时段列表 = computed(() => (
  phoneUsage.每日使用时段映射.get(当前选中日期.value) ?? []
))
const 选中日期未使用时段列表 = computed(() => (
  获取日期内未使用时段列表(当前选中日期.value, 选中日期使用时段列表.value)
))
const 当前展示时段列表 = computed(() => (
  使用时段展示模式.value === '未用'
    ? 选中日期未使用时段列表.value
    : 选中日期使用时段列表.value
))
const 使用时段标题 = computed(() => {
  const label = 使用时段展示模式.value === '未用' ? '未使用时段' : '使用时段'
  if (当前选中日期.value === phoneUsage.今日汇总.日期) {
    return `今天${label}`
  }
  return `${格式化短日期(当前选中日期.value)} ${label}`
})
const 使用时段说明 = computed(() => {
  if (使用时段展示模式.value === '未用') {
    return `共 ${选中日期未使用时段列表.value.length} 段，${选中日期未使用时长.value}`
  }

  return `共 ${选中日期使用时段列表.value.length} 段，${格式化时长(选中日期汇总.value.解锁使用总时长毫秒)}`
})
const 选中日期使用占比 = computed(() => {
  const usedMilliseconds = 计算日期内使用时长(当前选中日期.value, 选中日期使用时段列表.value)
  return Math.min(100, Math.round((usedMilliseconds / 86400000) * 1000) / 10)
})
const 选中日期未使用时长 = computed(() => (
  格式化时长(Math.max(0, 86400000 - 计算日期内使用时长(当前选中日期.value, 选中日期使用时段列表.value)))
))
const 当前高亮时段 = computed(() => {
  if (!高亮时段.value) {
    return null
  }

  const dayStart = 获取日期起始时间戳(当前选中日期.value)
  const dayEnd = dayStart + 86400000
  if (高亮时段.value.结束时间戳 <= dayStart || 高亮时段.value.开始时间戳 >= dayEnd) {
    return null
  }

  return {
    ...高亮时段.value,
    开始时间戳: Math.max(dayStart, 高亮时段.value.开始时间戳),
    结束时间戳: Math.min(dayEnd, 高亮时段.value.结束时间戳),
  }
})
const 使用占比图背景 = computed(() => (
  生成使用占比图背景(当前选中日期.value, 选中日期使用时段列表.value, 当前高亮时段.value)
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

function 格式化使用时段范围(startAt: number, endAt: number) {
  return `${格式化时间点(startAt)} - ${格式化时间点(endAt)}`
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

function 获取日期起始时间戳(dateKey: string) {
  const [year, month, day] = dateKey.split('-').map(Number)
  return new Date(year, month - 1, day).getTime()
}

function 获取日期内使用范围列表(
  dateKey: string,
  periodList: Array<{ 开始时间戳: number, 结束时间戳: number }>,
) {
  const dayStart = 获取日期起始时间戳(dateKey)
  const dayEnd = dayStart + 86400000
  const sortedPeriodList = periodList
    .map((period) => ({
      start: Math.max(dayStart, period.开始时间戳),
      end: Math.min(dayEnd, period.结束时间戳),
    }))
    .filter((period) => period.end > period.start)
    .sort((a, b) => a.start - b.start)

  return sortedPeriodList.reduce<Array<{ start: number, end: number }>>((mergedPeriodList, period) => {
    const previousPeriod = mergedPeriodList.at(-1)
    if (!previousPeriod || period.start > previousPeriod.end) {
      mergedPeriodList.push(period)
      return mergedPeriodList
    }

    previousPeriod.end = Math.max(previousPeriod.end, period.end)
    return mergedPeriodList
  }, [])
}

function 计算日期内使用时长(
  dateKey: string,
  periodList: Array<{ 开始时间戳: number, 结束时间戳: number }>,
) {
  return 获取日期内使用范围列表(dateKey, periodList)
    .reduce((total, period) => total + period.end - period.start, 0)
}

function 获取日期内未使用时段列表(
  dateKey: string,
  periodList: Array<{ 开始时间戳: number, 结束时间戳: number }>,
) {
  const dayStart = 获取日期起始时间戳(dateKey)
  const dayEnd = dayStart + 86400000
  const usedRangeList = 获取日期内使用范围列表(dateKey, periodList)
  const unusedPeriodList: Array<{ 开始时间戳: number, 结束时间戳: number, 时长毫秒: number }> = []
  let cursor = dayStart

  usedRangeList.forEach((period) => {
    if (period.start > cursor) {
      unusedPeriodList.push({
        开始时间戳: cursor,
        结束时间戳: period.start,
        时长毫秒: period.start - cursor,
      })
    }
    cursor = Math.max(cursor, period.end)
  })

  if (cursor < dayEnd) {
    unusedPeriodList.push({
      开始时间戳: cursor,
      结束时间戳: dayEnd,
      时长毫秒: dayEnd - cursor,
    })
  }

  return unusedPeriodList
}

function 生成使用占比图背景(
  dateKey: string,
  periodList: Array<{ 开始时间戳: number, 结束时间戳: number }>,
  highlightedPeriod: 可高亮时段 | null = null,
) {
  const dayStart = 获取日期起始时间戳(dateKey)
  const dayEnd = dayStart + 86400000
  const usedRangeList = 获取日期内使用范围列表(dateKey, periodList)
  const boundarySet = new Set<number>([dayStart, dayEnd])
  usedRangeList.forEach((period) => {
    boundarySet.add(period.start)
    boundarySet.add(period.end)
  })

  if (highlightedPeriod) {
    boundarySet.add(Math.max(dayStart, highlightedPeriod.开始时间戳))
    boundarySet.add(Math.min(dayEnd, highlightedPeriod.结束时间戳))
  }

  const boundaries = [...boundarySet].sort((left, right) => left - right)
  const gradientSegments = boundaries.slice(0, -1).map((start, index) => {
    const end = boundaries[index + 1]
    const midpoint = start + (end - start) / 2
    const isHighlighted = highlightedPeriod
      && midpoint >= highlightedPeriod.开始时间戳
      && midpoint <= highlightedPeriod.结束时间戳
    const isUsed = usedRangeList.some((period) => midpoint >= period.start && midpoint <= period.end)
    const color = isHighlighted
      ? 'var(--usage-period-highlight)'
      : isUsed
        ? 'var(--usage-period-used)'
        : 'var(--usage-period-unused)'
    const startDegree = ((start - dayStart) / 86400000) * 360
    const endDegree = ((end - dayStart) / 86400000) * 360
    return `${color} ${startDegree}deg ${endDegree}deg`
  })

  return `conic-gradient(from -90deg, ${gradientSegments.join(', ')})`
}

function 判断时间戳在时段内(
  timestamp: number,
  period: { 开始时间戳: number, 结束时间戳: number },
) {
  return timestamp >= period.开始时间戳 && timestamp <= period.结束时间戳
}

function 判断时段被高亮(
  period: { 开始时间戳: number, 结束时间戳: number },
  type: 使用时段类型,
) {
  return 当前高亮时段.value?.类型 === type
    && 当前高亮时段.value.开始时间戳 === period.开始时间戳
    && 当前高亮时段.value.结束时间戳 === period.结束时间戳
}

function 判断解锁时间点被高亮(timestamp: number) {
  if (高亮解锁时间戳.value === timestamp) {
    return true
  }

  return 当前高亮时段.value?.类型 === '使用'
    && 判断时间戳在时段内(timestamp, 当前高亮时段.value)
}

function handleSelectUsagePeriod(period: { 开始时间戳: number, 结束时间戳: number }) {
  const type = 使用时段展示模式.value === '未用' ? '未用' : '使用'
  高亮时段.value = {
    开始时间戳: period.开始时间戳,
    结束时间戳: period.结束时间戳,
    类型: type,
  }
  高亮解锁时间戳.value = null
}

function handleSelectUnlockTime(timestamp: number) {
  const matchedPeriod = 选中日期使用时段列表.value.find((period) => 判断时间戳在时段内(timestamp, period))
  高亮解锁时间戳.value = timestamp

  if (matchedPeriod) {
    高亮时段.value = {
      开始时间戳: matchedPeriod.开始时间戳,
      结束时间戳: matchedPeriod.结束时间戳,
      类型: '使用',
    }
    使用时段展示模式.value = '使用'
    return
  }

  高亮时段.value = null
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
  高亮时段.value = null
  高亮解锁时间戳.value = null
}

function handleChangeUsagePeriodMode(value: string | number) {
  if (value === '使用' || value === '未用' || value === '占比') {
    使用时段展示模式.value = value
  }
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
      class="phone-usage-header"
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
      <button class="primary-button permission-panel__button" type="button" @click="handleOpenPermissionSettings">
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

    <section class="panel-card usage-period-panel">
      <div class="section-heading">
        <div class="section-heading__main">
          <strong class="section-title">{{ 使用时段标题 }}</strong>
          <span class="panel-meta">{{ 使用时段说明 }}</span>
        </div>
        <SegmentedSwitch
          class="usage-period-switch"
          aria-label="使用时段展示方式"
          size="small"
          :model-value="使用时段展示模式"
          :options="使用时段展示选项"
          @update:model-value="handleChangeUsagePeriodMode"
        />
      </div>

      <div
        v-if="使用时段展示模式 === '占比'"
        class="usage-period-ratio"
      >
        <div
          class="usage-ratio-chart"
          :style="{ background: 使用占比图背景 }"
          aria-label="24 小时使用占比"
        >
          <div class="usage-ratio-chart__center">
            <strong>{{ 选中日期使用占比 }}%</strong>
            <span>已使用</span>
          </div>
          <span class="usage-ratio-chart__mark usage-ratio-chart__mark--top">0</span>
          <span class="usage-ratio-chart__mark usage-ratio-chart__mark--right">6</span>
          <span class="usage-ratio-chart__mark usage-ratio-chart__mark--bottom">12</span>
          <span class="usage-ratio-chart__mark usage-ratio-chart__mark--left">18</span>
        </div>

        <div class="usage-ratio-summary">
          <span><i class="usage-ratio-summary__dot usage-ratio-summary__dot--used" />使用 {{ 格式化时长(计算日期内使用时长(当前选中日期, 选中日期使用时段列表)) }}</span>
          <span><i class="usage-ratio-summary__dot usage-ratio-summary__dot--unused" />未使用 {{ 选中日期未使用时长 }}</span>
        </div>
      </div>

      <div v-else-if="当前展示时段列表.length > 0" class="usage-period-list">
        <button
          v-for="(period, index) in 当前展示时段列表"
          :key="`${period.开始时间戳}-${period.结束时间戳}`"
          class="usage-period-item"
          :class="{ 'usage-period-item--active': 判断时段被高亮(period, 使用时段展示模式 === '未用' ? '未用' : '使用') }"
          type="button"
          @click="handleSelectUsagePeriod(period)"
        >
          <span class="usage-period-item__index">第 {{ index + 1 }} 段</span>
          <span class="usage-period-item__content">
            <strong class="usage-period-item__range">
              {{ 格式化使用时段范围(period.开始时间戳, period.结束时间戳) }}
            </strong>
            <span class="usage-period-item__duration">{{ 格式化时长(period.时长毫秒) }}</span>
          </span>
        </button>
      </div>

      <p v-else class="empty-text">
        {{ 使用时段展示模式 === '未用' ? '这天没有未使用时段' : '这天还没有采集到使用时段' }}
      </p>
    </section>

    <section class="panel-card unlock-panel">
      <div class="section-heading">
        <strong class="section-title">{{ 解锁时间点标题 }}</strong>
        <span class="panel-meta">{{ 选中日期解锁时间点.length }} 次</span>
      </div>

      <div v-if="选中日期解锁时间点.length > 0" class="unlock-list">
        <button
          v-for="time in 选中日期解锁时间点"
          :key="time.时间戳"
          class="unlock-chip"
          :class="{ 'unlock-chip--active': 判断解锁时间点被高亮(time.时间戳) }"
          type="button"
          @click="handleSelectUnlockTime(time.时间戳)"
        >
          {{ time.文本 }}
        </button>
      </div>

      <p v-else class="empty-text">
        这天还没有采集到解锁事件
      </p>
    </section>
  </section>
</template>

<style scoped>
.phone-usage-page {
  --usage-period-highlight: var(--theme-accent-strong);
  width: min(430px, 100%);
  display: grid;
  gap: 10px;
  align-content: start;
  margin: 0 auto;
}

.phone-usage-header {
  gap: 0;
}

.phone-usage-header :deep(.page-section-shell__header) {
  align-items: center;
  min-height: 34px;
}

.phone-usage-header :deep(.page-section-shell__content--with-back) {
  padding-top: 0;
}

.phone-usage-header :deep(.page-section-shell__body) {
  display: none;
}

.phone-usage-header :deep(.page-title) {
  font-size: 1.28rem;
  line-height: 1.15;
}

.phone-usage-header :deep(.page-section-shell__back) {
  min-width: 34px;
  width: 34px;
  height: 34px;
}

.phone-usage-header :deep(.page-section-shell__back svg) {
  width: 17px;
  height: 17px;
}

.refresh-button {
  flex: 0 0 auto;
  height: 30px;
  padding: 0 10px;
  border: 1px solid var(--theme-card-border);
  border-radius: 10px;
  color: var(--theme-accent-strong);
  background: var(--theme-panel-soft);
  font-size: 0.82rem;
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
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid color-mix(in srgb, var(--theme-danger-strong) 28%, var(--theme-card-border));
  border-radius: 12px;
  background: color-mix(in srgb, var(--theme-danger-soft) 42%, var(--theme-panel-soft));
}

.permission-panel__text {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.permission-panel__text strong {
  font-size: 0.9rem;
  line-height: 1.2;
}

.permission-panel__text span {
  color: var(--text-tertiary);
  font-size: 0.78rem;
  line-height: 1.35;
}

.permission-panel__button {
  min-height: 30px;
  padding: 0 10px;
  border-radius: 10px;
  font-size: 0.82rem;
  font-weight: 600;
  white-space: nowrap;
}

.status-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 10px;
  padding-left: 4px;
  color: var(--text-tertiary);
  font-size: 0.78rem;
  line-height: 1.25;
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
.unlock-panel,
.usage-period-panel {
  display: grid;
  gap: 14px;
  padding: 16px;
}

.section-heading__main {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.usage-period-panel {
  --usage-period-used: var(--el-color-primary);
  --usage-period-unused: color-mix(in srgb, var(--theme-card-border) 70%, transparent);
}

.usage-period-switch {
  flex: 0 0 auto;
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

.usage-period-list {
  display: grid;
  gap: 0;
  margin-inline: -8px;
  border-top: 1px solid color-mix(in srgb, var(--theme-card-border) 72%, transparent);
  border-bottom: 1px solid color-mix(in srgb, var(--theme-card-border) 72%, transparent);
}

.usage-period-ratio {
  display: grid;
  justify-items: center;
  gap: 14px;
  padding: 4px 0 2px;
}

.usage-ratio-chart {
  position: relative;
  width: min(248px, 76vw);
  aspect-ratio: 1;
  border-radius: 50%;
  box-shadow:
    inset 0 0 0 1px var(--theme-card-border),
    0 12px 28px color-mix(in srgb, var(--theme-card-border) 55%, transparent);
}

.usage-ratio-chart::before {
  position: absolute;
  inset: 13%;
  border-radius: 50%;
  border: 1px solid color-mix(in srgb, var(--theme-card-border) 68%, transparent);
  background: var(--theme-card-bg);
  content: '';
}

.usage-ratio-chart__center {
  position: absolute;
  inset: 28%;
  z-index: 1;
  display: grid;
  place-content: center;
  gap: 4px;
  border-radius: 50%;
  text-align: center;
}

.usage-ratio-chart__center strong {
  color: var(--text-primary);
  font-size: 1.46rem;
  line-height: 1;
}

.usage-ratio-chart__center span {
  color: var(--text-tertiary);
  font-size: 0.82rem;
  line-height: 1;
}

.usage-ratio-chart__mark {
  position: absolute;
  z-index: 1;
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  color: var(--text-tertiary);
  background: color-mix(in srgb, var(--theme-card-bg) 86%, transparent);
  font-size: 0.72rem;
  font-weight: 700;
  line-height: 1;
}

.usage-ratio-chart__mark--top {
  top: 6px;
  left: 50%;
  transform: translateX(-50%);
}

.usage-ratio-chart__mark--right {
  top: 50%;
  right: 6px;
  transform: translateY(-50%);
}

.usage-ratio-chart__mark--bottom {
  bottom: 6px;
  left: 50%;
  transform: translateX(-50%);
}

.usage-ratio-chart__mark--left {
  top: 50%;
  left: 6px;
  transform: translateY(-50%);
}

.usage-ratio-summary {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px 14px;
  color: var(--text-tertiary);
  font-size: 0.84rem;
}

.usage-ratio-summary span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.usage-ratio-summary__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.usage-ratio-summary__dot--used {
  background: var(--usage-period-used);
}

.usage-ratio-summary__dot--unused {
  background: var(--usage-period-unused);
  outline: 1px solid var(--theme-card-border);
}

.usage-period-item {
  min-width: 0;
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr);
  align-items: stretch;
  padding: 0;
  border: 0;
  color: inherit;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition:
    background 0.18s ease,
    box-shadow 0.18s ease;
}

.usage-period-item + .usage-period-item {
  border-top: 1px solid color-mix(in srgb, var(--theme-card-border) 64%, transparent);
}

.usage-period-item--active {
  background: color-mix(in srgb, var(--usage-period-highlight) 12%, transparent);
  box-shadow: inset 3px 0 0 var(--usage-period-highlight);
}

.usage-period-item--active .usage-period-item__index,
.usage-period-item--active .usage-period-item__duration {
  color: var(--usage-period-highlight);
}

.usage-period-item--active .usage-period-item__range {
  color: var(--text-primary);
  font-weight: 800;
}

.usage-period-item__index {
  display: flex;
  align-items: center;
  padding: 13px 12px 13px 8px;
  color: var(--text-tertiary);
  font-size: 0.78rem;
  line-height: 1.2;
  white-space: nowrap;
}

.usage-period-item__content {
  min-width: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 13px 8px 13px 12px;
}

.usage-period-item__range {
  min-width: 0;
  color: var(--text-primary);
  font-size: 1rem;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.usage-period-item__duration {
  color: var(--theme-accent-strong);
  font-size: 0.84rem;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
}

.unlock-chip {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  border: 1px solid transparent;
  border-radius: 10px;
  color: var(--theme-accent-strong);
  background: var(--theme-accent-soft);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.18s ease,
    border-color 0.18s ease,
    color 0.18s ease,
    transform 0.18s ease;
}

.unlock-chip--active {
  border-color: color-mix(in srgb, var(--usage-period-highlight) 58%, transparent);
  color: var(--usage-period-highlight);
  background: color-mix(in srgb, var(--usage-period-highlight) 16%, var(--theme-card-bg));
  transform: translateY(-1px);
}

.empty-text {
  margin: 0;
  color: var(--text-tertiary);
  font-size: 0.92rem;
}
</style>
