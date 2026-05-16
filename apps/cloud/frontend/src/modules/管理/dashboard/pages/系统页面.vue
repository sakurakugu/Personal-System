<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import {
  ElAlert,
  ElButton,
  ElCard,
  ElCol,
  ElDescriptions,
  ElDescriptionsItem,
  ElEmpty,
  ElIcon,
  ElInputNumber,
  ElProgress,
  ElRow,
  ElSkeleton,
  ElSwitch,
  ElTag,
  ElMessage,
} from 'element-plus'
import {
  CircleCheckFilled,
  CircleCloseFilled,
  Collection,
  Cpu,
  FirstAidKit,
  Monitor,
  RefreshRight,
  Timer,
  WarningFilled,
} from '@element-plus/icons-vue'
import { 获取系统状态 } from '../../api'
import type { SystemRequestAggregate, SystemRequestEvent, SystemStatus } from '../../types'
import type { HealthComponentStatus } from '../../../../modules/系统/types'
import { getApiErrorMessage } from '../../../../shared/api'

interface AlertItem {
  key: string
  title: string
  description: string
  type: 'warning' | 'error'
}

const CPU_ALERT_THRESHOLD = 85
const MEMORY_ALERT_THRESHOLD = 85
const DISK_ALERT_THRESHOLD = 90
const DETAIL_PREVIEW_LENGTH = 160

const MIN_SAMPLING_SECONDS = 5
const MAX_SAMPLING_SECONDS = 60

const loading = ref(true)
const refreshing = ref(false)
const autoRefresh = ref(true)
const samplingSeconds = ref(15)
const errorMessage = ref('')
const requestDurationMs = ref<number | null>(null)
const lastRefreshAt = ref<Date | null>(null)
const pageHidden = ref(document.hidden)
const expandedDetailMap = ref<Record<string, boolean>>({})
let refreshTimer: number | undefined

const sys = ref<SystemStatus>({
  cpu_percent: 0,
  memory_total_gb: 0,
  memory_used_gb: 0,
  memory_percent: 0,
  disk_total_gb: 0,
  disk_used_gb: 0,
  disk_percent: 0,
  uptime_seconds: 0,
  health: {
    status: 'unknown',
    checked_at: '',
    database: { status: 'unknown', detail: null },
    redis: { status: 'unknown', detail: null },
    minio: { status: 'unknown', detail: null },
  },
  runtime: {
    recent_window_minutes: 30,
    slow_request_threshold_ms: 1000,
    error_count: 0,
    slow_request_count: 0,
    top_error_routes: [],
    top_slow_routes: [],
    recent_errors: [],
    recent_slow_requests: [],
  },
})

const dependencies = computed(() => [
  { key: 'database', label: '数据库', component: sys.value.health.database },
  { key: 'redis', label: 'Redis', component: sys.value.health.redis },
  { key: 'minio', label: 'MinIO', component: sys.value.health.minio },
])

const runtimeWindowLabel = computed(() => `最近 ${sys.value.runtime.recent_window_minutes} 分钟`)
const hasErrorRouteAggregates = computed(() => sys.value.runtime.top_error_routes.length > 0)
const hasRecentErrors = computed(() => sys.value.runtime.recent_errors.length > 0)
const hasErrorRuntimeContent = computed(() => hasErrorRouteAggregates.value || hasRecentErrors.value)
const hasSlowRouteAggregates = computed(() => sys.value.runtime.top_slow_routes.length > 0)
const hasRecentSlowRequests = computed(() => sys.value.runtime.recent_slow_requests.length > 0)
const hasSlowRuntimeContent = computed(() => hasSlowRouteAggregates.value || hasRecentSlowRequests.value)

const alertItems = computed<AlertItem[]>(() => {
  if (loading.value && !lastRefreshAt.value) {
    return []
  }

  const items: AlertItem[] = []

  for (const dependency of dependencies.value) {
    if (dependency.component.status !== 'healthy') {
      items.push({
        key: `dependency-${dependency.key}`,
        title: `${dependency.label} 异常`,
        description: dependency.component.detail || `${dependency.label} 当前不可用`,
        type: 'error',
      })
    }
  }

  if (sys.value.runtime.error_count > 0) {
    items.push({
      key: 'recent-errors',
      title: '最近存在接口错误',
      description: `${runtimeWindowLabel.value} 内记录到 ${sys.value.runtime.error_count} 次 5xx 错误，请优先查看错误摘要。`,
      type: 'error',
    })
  }

  if (sys.value.runtime.slow_request_count > 0) {
    items.push({
      key: 'recent-slow-requests',
      title: '最近存在慢请求',
      description: `${runtimeWindowLabel.value} 内记录到 ${sys.value.runtime.slow_request_count} 次慢请求，当前阈值 ${formatDuration(sys.value.runtime.slow_request_threshold_ms)}。`,
      type: 'warning',
    })
  }

  if (sys.value.cpu_percent >= CPU_ALERT_THRESHOLD) {
    items.push({
      key: 'cpu-high',
      title: 'CPU 使用率偏高',
      description: `当前 ${formatPercent(sys.value.cpu_percent)}，建议检查是否存在异常任务或高负载请求。`,
      type: 'warning',
    })
  }

  if (sys.value.memory_percent >= MEMORY_ALERT_THRESHOLD) {
    items.push({
      key: 'memory-high',
      title: '内存使用率偏高',
      description: `当前 ${formatPercent(sys.value.memory_percent)}，建议观察是否存在缓存堆积或进程泄漏。`,
      type: 'warning',
    })
  }

  if (sys.value.disk_percent >= DISK_ALERT_THRESHOLD) {
    items.push({
      key: 'disk-high',
      title: '磁盘空间偏紧',
      description: `当前 ${formatPercent(sys.value.disk_percent)}，建议清理日志、备份或历史文件。`,
      type: 'warning',
    })
  }

  return items
})

const overallStatus = computed(() => {
  if (loading.value && !lastRefreshAt.value) {
    return {
      label: '正在检查',
      description: '正在拉取系统资源和依赖服务状态。',
      tagType: 'info' as const,
      icon: Monitor,
    }
  }

  if (dependencies.value.some((item) => item.component.status !== 'healthy')) {
    return {
      label: '依赖异常',
      description: '存在不可用依赖，建议优先处理数据库、缓存或对象存储连通性。',
      tagType: 'danger' as const,
      icon: CircleCloseFilled,
    }
  }

  if (sys.value.runtime.error_count > 0) {
    return {
      label: '最近有错误',
      description: '最近出现过 5xx 错误，建议查看错误摘要并结合日志排查。',
      tagType: 'danger' as const,
      icon: CircleCloseFilled,
    }
  }

  if (alertItems.value.length > 0) {
    return {
      label: '需要关注',
      description: '系统核心依赖可用，但最近出现了慢请求或资源告警。',
      tagType: 'warning' as const,
      icon: WarningFilled,
    }
  }

  return {
    label: '运行正常',
    description: '系统资源稳定，依赖服务检查全部通过。',
    tagType: 'success' as const,
    icon: CircleCheckFilled,
  }
})

function formatPercent(value: number): string {
  return `${Number(value.toFixed(1))}%`
}

function formatNumber(value: number): string {
  return Number(value.toFixed(2)).toString()
}

function formatDuration(value: number): string {
  return `${Number(value.toFixed(1))} ms`
}

function formatAggregateSubtitle(item: SystemRequestAggregate): string {
  return `共 ${item.count} 次，峰值 ${formatDuration(item.max_duration_ms)}，均值 ${formatDuration(item.avg_duration_ms)}`
}

function buildAggregateDetailKey(kind: string, item: SystemRequestAggregate): string {
  return `${kind}-${item.method}-${item.path}-${item.last_happened_at}`
}

function buildEventDetailKey(kind: string, item: SystemRequestEvent): string {
  return `${kind}-${item.method}-${item.path}-${item.happened_at}-${item.status_code}-${item.duration_ms}`
}

function shouldCollapseDetail(detail: string | null): boolean {
  if (!detail) return false
  return detail.length > DETAIL_PREVIEW_LENGTH || detail.includes('\n')
}

function isDetailExpanded(key: string): boolean {
  return expandedDetailMap.value[key] === true
}

function toggleDetail(key: string): void {
  expandedDetailMap.value[key] = !expandedDetailMap.value[key]
}

function getDetailPreview(detail: string | null): string {
  if (!detail) return ''
  if (!shouldCollapseDetail(detail)) return detail
  return `${detail.slice(0, DETAIL_PREVIEW_LENGTH).trimEnd()}...`
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${days}天 ${hours}小时 ${minutes}分`
}

function readThemeColor(name: string, fallback: string): string {
  if (typeof window === 'undefined') {
    return fallback
  }

  return window.getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

function statusColor(percent: number): string {
  if (percent < 60) return readThemeColor('--el-color-primary', '#18a058')
  if (percent < 85) return '#f0a020'
  return '#d03050'
}

function formatDateTime(value: string | Date | null): string {
  if (!value) return '未刷新'
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return '时间无效'
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date)
}

function dependencyStatusType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  if (status === 'healthy') return 'success'
  if (status === 'unhealthy') return 'danger'
  return 'info'
}

function dependencyStatusLabel(status: string): string {
  if (status === 'healthy') return '正常'
  if (status === 'unhealthy') return '异常'
  return '未知'
}

function dependencyDescription(component: HealthComponentStatus): string {
  if (component.status === 'healthy') return '最近一次探活通过'
  return component.detail || '最近一次探活失败'
}

async function loadSystemStatus(options: { silent?: boolean } = {}) {
  if (refreshing.value) {
    return
  }

  const startAt = window.performance.now()
  refreshing.value = true

  try {
    sys.value = await 获取系统状态()
    requestDurationMs.value = Math.round(window.performance.now() - startAt)
    lastRefreshAt.value = new Date()
    errorMessage.value = ''
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '系统状态加载失败')
    if (!options.silent) {
      ElMessage.error(errorMessage.value)
    }
  } finally {
    refreshing.value = false
    loading.value = false
  }
}

function stopTimer() {
  if (refreshTimer !== undefined) {
    window.clearInterval(refreshTimer)
    refreshTimer = undefined
  }
}

function startTimer() {
  stopTimer()
  if (!autoRefresh.value || pageHidden.value) return
  refreshTimer = window.setInterval(() => {
    void loadSystemStatus({ silent: true })
  }, samplingSeconds.value * 1000)
}

function handleVisibilityChange() {
  pageHidden.value = document.hidden
  if (pageHidden.value) {
    stopTimer()
    return
  }
  void loadSystemStatus({ silent: true })
  startTimer()
}

async function refreshNow() {
  await loadSystemStatus()
}

watch(samplingSeconds, (value) => {
  const normalized = Math.min(MAX_SAMPLING_SECONDS, Math.max(MIN_SAMPLING_SECONDS, value))
  if (normalized !== value) {
    samplingSeconds.value = normalized
    return
  }
  startTimer()
})

watch(autoRefresh, () => {
  startTimer()
})

onMounted(async () => {
  document.addEventListener('visibilitychange', handleVisibilityChange)
  await loadSystemStatus({ silent: true })
  startTimer()
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  stopTimer()
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">
        <span class="page-title-main">
          <ElIcon><Monitor /></ElIcon>
          <span>系统状态</span>
        </span>
        <ElTag :type="overallStatus.tagType" effect="dark">{{ overallStatus.label }}</ElTag>
      </h2>
      <div class="page-actions">
        <label class="page-action-item">
          <span>自动刷新</span>
          <ElSwitch v-model="autoRefresh" />
        </label>
        <label class="page-action-item">
          <span>间隔</span>
          <ElInputNumber
            v-model="samplingSeconds"
            :min="MIN_SAMPLING_SECONDS"
            :max="MAX_SAMPLING_SECONDS"
            :step="1"
            size="small"
            :controls="true"
            style="width: 84px"
          />
          <span>秒</span>
        </label>
        <ElButton type="primary" :loading="refreshing" @click="refreshNow">
          <ElIcon><RefreshRight /></ElIcon>
          <span>立即刷新</span>
        </ElButton>
      </div>
    </div>

    <div class="alert-list">
      <ElAlert
        v-if="errorMessage"
        title="刷新失败"
        :description="errorMessage"
        type="error"
        show-icon
        :closable="false"
      />
      <ElAlert
        v-for="alert in alertItems"
        :key="alert.key"
        :title="alert.title"
        :description="alert.description"
        :type="alert.type"
        show-icon
        :closable="false"
      />
    </div>

    <ElSkeleton :loading="loading" animated>
      <ElCard class="summary-card">
        <div class="summary-layout">
          <div class="summary-main">
            <div class="summary-caption">系统总览</div>
            <div class="summary-status">
              <ElIcon class="summary-status-icon">
                <component :is="overallStatus.icon" />
              </ElIcon>
              <div>
                <div class="summary-status-title">{{ overallStatus.label }}</div>
                <p class="summary-status-description">{{ overallStatus.description }}</p>
              </div>
            </div>
            <div class="summary-tags">
              <ElTag v-if="alertItems.length" type="warning" plain>{{ alertItems.length }} 条待处理提醒</ElTag>
              <ElTag v-else type="success" plain>当前没有待处理告警</ElTag>
              <ElTag v-if="sys.runtime.error_count" type="danger" plain>最近错误 {{ sys.runtime.error_count }}</ElTag>
              <ElTag v-if="sys.runtime.slow_request_count" type="warning" plain>慢请求 {{ sys.runtime.slow_request_count }}</ElTag>
            </div>
          </div>

          <ElDescriptions :column="2" border class="summary-details">
            <ElDescriptionsItem label="最近刷新">
              {{ formatDateTime(lastRefreshAt) }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="健康检查时间">
              {{ formatDateTime(sys.health.checked_at || null) }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="请求耗时">
              {{ requestDurationMs === null ? '未记录' : `${requestDurationMs} ms` }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="自动刷新">
              {{ autoRefresh ? (pageHidden ? `已暂停 / 页面隐藏 / ${samplingSeconds} 秒` : `开启 / ${samplingSeconds} 秒`) : '已关闭' }}
            </ElDescriptionsItem>
          </ElDescriptions>
        </div>
      </ElCard>

      <ElRow :gutter="16" class="metric-row">
        <ElCol :xs="24" :sm="12" :xl="6">
          <ElCard class="metric-card">
            <template #header>
              <span class="card-header">
                <ElIcon><Cpu /></ElIcon>
                <span>CPU</span>
              </span>
            </template>
            <div class="system-metric">
              <ElProgress
                type="circle"
                :percentage="Number(sys.cpu_percent.toFixed(1))"
                :color="statusColor(sys.cpu_percent)"
              />
              <p class="system-metric-text">{{ formatPercent(sys.cpu_percent) }}</p>
              <p class="metric-hint">告警阈值：{{ CPU_ALERT_THRESHOLD }}%</p>
            </div>
          </ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="12" :xl="6">
          <ElCard class="metric-card">
            <template #header>
              <span class="card-header">
                <ElIcon><Collection /></ElIcon>
                <span>内存</span>
              </span>
            </template>
            <div class="system-metric">
              <ElProgress
                type="circle"
                :percentage="Number(sys.memory_percent.toFixed(1))"
                :color="statusColor(sys.memory_percent)"
              />
              <p class="system-metric-text">{{ formatNumber(sys.memory_used_gb) }} / {{ formatNumber(sys.memory_total_gb) }} GB</p>
              <p class="metric-hint">告警阈值：{{ MEMORY_ALERT_THRESHOLD }}%</p>
            </div>
          </ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="12" :xl="6">
          <ElCard class="metric-card">
            <template #header>
              <span class="card-header">
                <ElIcon><FirstAidKit /></ElIcon>
                <span>磁盘</span>
              </span>
            </template>
            <div class="system-metric">
              <ElProgress
                type="circle"
                :percentage="Number(sys.disk_percent.toFixed(1))"
                :color="statusColor(sys.disk_percent)"
              />
              <p class="system-metric-text">{{ formatNumber(sys.disk_used_gb) }} / {{ formatNumber(sys.disk_total_gb) }} GB</p>
              <p class="metric-hint">告警阈值：{{ DISK_ALERT_THRESHOLD }}%</p>
            </div>
          </ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="12" :xl="6">
          <ElCard class="metric-card">
            <template #header>
              <span class="card-header">
                <ElIcon><Timer /></ElIcon>
                <span>运行时间</span>
              </span>
            </template>
            <div class="uptime-metric">
              <div class="uptime-value">{{ formatUptime(sys.uptime_seconds) }}</div>
              <p class="metric-hint">系统启动后已连续运行</p>
            </div>
          </ElCard>
        </ElCol>
      </ElRow>

      <div class="section-header">
        <span>依赖服务状态</span>
        <span class="section-header-subtitle">以最近一次健康检查结果为准</span>
      </div>
      <ElRow :gutter="16" class="service-row">
        <ElCol v-for="dependency in dependencies" :key="dependency.key" :xs="24" :md="8">
          <ElCard class="service-card">
            <div class="service-card-header">
              <div>
                <div class="service-card-title">{{ dependency.label }}</div>
                <div class="service-card-description">{{ dependencyDescription(dependency.component) }}</div>
              </div>
              <ElTag :type="dependencyStatusType(dependency.component.status)" effect="dark">
                {{ dependencyStatusLabel(dependency.component.status) }}
              </ElTag>
            </div>
            <div class="service-card-meta">检查时间：{{ formatDateTime(sys.health.checked_at || null) }}</div>
          </ElCard>
        </ElCol>
      </ElRow>

      <div class="section-header">
        <span>运行摘要</span>
        <span class="section-header-subtitle">{{ runtimeWindowLabel }}</span>
      </div>
      <ElRow :gutter="16" class="runtime-row">
        <ElCol :xs="24" :xl="12">
          <ElCard class="runtime-card">
            <div class="runtime-card-header">
              <div>
                <div class="service-card-title">最近错误</div>
                <div class="service-card-description">展示最近出现的 5xx 错误，便于快速定位异常接口。</div>
              </div>
              <ElTag type="danger" effect="dark">{{ sys.runtime.error_count }} 条</ElTag>
            </div>
            <template v-if="hasErrorRuntimeContent">
              <div class="aggregate-panel">
                <div class="aggregate-title">错误接口 Top{{ sys.runtime.top_error_routes.length || 0 }}</div>
                <div v-if="hasErrorRouteAggregates" class="aggregate-list">
                  <div
                    v-for="item in sys.runtime.top_error_routes"
                    :key="`error-top-${item.method}-${item.path}`"
                    class="aggregate-item is-error"
                  >
                    <div class="aggregate-main">
                      <div class="event-title">
                        <ElTag size="small" effect="plain">{{ item.method }}</ElTag>
                        <span class="event-path">{{ item.path }}</span>
                      </div>
                      <ElTag type="danger" size="small">{{ item.count }} 次</ElTag>
                    </div>
                    <div class="event-meta">
                      <span>{{ formatAggregateSubtitle(item) }}</span>
                      <span>最近状态 {{ item.last_status_code }}</span>
                      <span>{{ formatDateTime(item.last_happened_at) }}</span>
                    </div>
                    <div v-if="item.detail" class="detail-block">
                      <div class="event-detail">
                        {{ isDetailExpanded(buildAggregateDetailKey('error-top', item)) ? item.detail : getDetailPreview(item.detail) }}
                      </div>
                      <ElButton
                        v-if="shouldCollapseDetail(item.detail)"
                        link
                        type="primary"
                        size="small"
                        class="detail-toggle"
                        @click="toggleDetail(buildAggregateDetailKey('error-top', item))"
                      >
                        {{ isDetailExpanded(buildAggregateDetailKey('error-top', item)) ? '收起详情' : '展开详情' }}
                      </ElButton>
                    </div>
                  </div>
                </div>
                <ElEmpty v-else description="最近没有异常接口聚合" :image-size="56" />
              </div>
              <div v-if="hasRecentErrors">
                <div class="aggregate-title">最近明细</div>
                <div class="event-list">
                  <div
                    v-for="item in sys.runtime.recent_errors"
                    :key="`${item.happened_at}-${item.path}-${item.status_code}`"
                    class="event-item is-error"
                  >
                    <div class="event-top">
                      <div class="event-title">
                        <ElTag size="small" effect="plain">{{ item.method }}</ElTag>
                        <span class="event-path">{{ item.path }}</span>
                      </div>
                      <ElTag type="danger" size="small">{{ item.status_code }}</ElTag>
                    </div>
                    <div class="event-meta">
                      <span>{{ formatDuration(item.duration_ms) }}</span>
                      <span>{{ formatDateTime(item.happened_at) }}</span>
                    </div>
                    <div v-if="item.detail" class="detail-block">
                      <div class="event-detail">
                        {{ isDetailExpanded(buildEventDetailKey('error-detail', item)) ? item.detail : getDetailPreview(item.detail) }}
                      </div>
                      <ElButton
                        v-if="shouldCollapseDetail(item.detail)"
                        link
                        type="primary"
                        size="small"
                        class="detail-toggle"
                        @click="toggleDetail(buildEventDetailKey('error-detail', item))"
                      >
                        {{ isDetailExpanded(buildEventDetailKey('error-detail', item)) ? '收起详情' : '展开详情' }}
                      </ElButton>
                    </div>
                  </div>
                </div>
              </div>
              <ElEmpty v-else description="最近没有 5xx 错误" :image-size="72" />
            </template>
            <ElEmpty v-else class="runtime-empty-state" :image-size="84">
              <template #description>
                <p class="runtime-empty-text">最近没有异常请求</p>
              </template>
            </ElEmpty>
          </ElCard>
        </ElCol>
        <ElCol :xs="24" :xl="12">
          <ElCard class="runtime-card">
            <div class="runtime-card-header">
              <div>
                <div class="service-card-title">慢请求摘要</div>
                <div class="service-card-description">
                  阈值 {{ formatDuration(sys.runtime.slow_request_threshold_ms) }}，用于观察接口抖动或性能退化。
                </div>
              </div>
              <ElTag type="warning" effect="dark">{{ sys.runtime.slow_request_count }} 条</ElTag>
            </div>
            <template v-if="hasSlowRuntimeContent">
              <div class="aggregate-panel">
                <div class="aggregate-title">慢请求接口 Top{{ sys.runtime.top_slow_routes.length || 0 }}</div>
                <div v-if="hasSlowRouteAggregates" class="aggregate-list">
                  <div
                    v-for="item in sys.runtime.top_slow_routes"
                    :key="`slow-top-${item.method}-${item.path}`"
                    class="aggregate-item is-warning"
                  >
                    <div class="aggregate-main">
                      <div class="event-title">
                        <ElTag size="small" effect="plain">{{ item.method }}</ElTag>
                        <span class="event-path">{{ item.path }}</span>
                      </div>
                      <ElTag type="warning" size="small">{{ item.count }} 次</ElTag>
                    </div>
                    <div class="event-meta">
                      <span>{{ formatAggregateSubtitle(item) }}</span>
                      <span>最近状态 {{ item.last_status_code }}</span>
                      <span>{{ formatDateTime(item.last_happened_at) }}</span>
                    </div>
                    <div v-if="item.detail" class="detail-block">
                      <div class="event-detail">
                        {{ isDetailExpanded(buildAggregateDetailKey('slow-top', item)) ? item.detail : getDetailPreview(item.detail) }}
                      </div>
                      <ElButton
                        v-if="shouldCollapseDetail(item.detail)"
                        link
                        type="primary"
                        size="small"
                        class="detail-toggle"
                        @click="toggleDetail(buildAggregateDetailKey('slow-top', item))"
                      >
                        {{ isDetailExpanded(buildAggregateDetailKey('slow-top', item)) ? '收起详情' : '展开详情' }}
                      </ElButton>
                    </div>
                  </div>
                </div>
                <ElEmpty v-else description="最近没有慢请求聚合" :image-size="56" />
              </div>
              <div v-if="hasRecentSlowRequests">
                <div class="aggregate-title">最近明细</div>
                <div class="event-list">
                  <div
                    v-for="item in sys.runtime.recent_slow_requests"
                    :key="`${item.happened_at}-${item.path}-${item.duration_ms}`"
                    class="event-item is-warning"
                  >
                    <div class="event-top">
                      <div class="event-title">
                        <ElTag size="small" effect="plain">{{ item.method }}</ElTag>
                        <span class="event-path">{{ item.path }}</span>
                      </div>
                      <ElTag :type="item.status_code >= 500 ? 'danger' : 'warning'" size="small">{{ item.status_code }}</ElTag>
                    </div>
                    <div class="event-meta">
                      <span>{{ formatDuration(item.duration_ms) }}</span>
                      <span>{{ formatDateTime(item.happened_at) }}</span>
                    </div>
                    <div v-if="item.detail" class="detail-block">
                      <div class="event-detail">
                        {{ isDetailExpanded(buildEventDetailKey('slow-detail', item)) ? item.detail : getDetailPreview(item.detail) }}
                      </div>
                      <ElButton
                        v-if="shouldCollapseDetail(item.detail)"
                        link
                        type="primary"
                        size="small"
                        class="detail-toggle"
                        @click="toggleDetail(buildEventDetailKey('slow-detail', item))"
                      >
                        {{ isDetailExpanded(buildEventDetailKey('slow-detail', item)) ? '收起详情' : '展开详情' }}
                      </ElButton>
                    </div>
                  </div>
                </div>
              </div>
              <ElEmpty v-else description="最近没有慢请求" :image-size="72" />
            </template>
            <ElEmpty v-else class="runtime-empty-state" :image-size="84">
              <template #description>
                <p class="runtime-empty-text">最近没有慢请求</p>
              </template>
            </ElEmpty>
          </ElCard>
        </ElCol>
      </ElRow>
    </ElSkeleton>
  </div>
</template>

<style scoped>
@import '@personal-system/ui/styles/media.css';

.page-container {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
  background:
    radial-gradient(circle at top right, rgb(var(--el-color-primary-rgb) / 0.08), transparent 24%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 250, 252, 0.98));
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 24px;
}

.page-title-main {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.page-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 12px;
}

.page-action-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.summary-card {
  margin-bottom: 16px;
}

.summary-layout {
  display: grid;
  grid-template-columns: minmax(280px, 1.2fr) minmax(320px, 1fr);
  gap: 20px;
  align-items: center;
}

.summary-main {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.summary-caption {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.summary-status {
  display: flex;
  align-items: center;
  gap: 14px;
}

.summary-status-icon {
  width: 54px;
  height: 54px;
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #fff;
  background: var(--theme-accent-gradient);
  box-shadow: 0 12px 28px rgb(var(--el-color-primary-rgb) / 0.22);
}

.summary-status-title {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.1;
}

.summary-status-description {
  margin: 6px 0 0;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}

.summary-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.summary-details {
  align-self: stretch;
}

.metric-row,
.service-row,
.runtime-row {
  row-gap: 16px;
}

.metric-card {
  height: 100%;
}

.card-header {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.system-metric,
.uptime-metric {
  min-height: 240px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.system-metric-text {
  margin: 12px 0 6px;
  font-size: 16px;
  font-weight: 600;
}

.metric-hint {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.uptime-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.3;
  margin-bottom: 10px;
}

.section-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin: 8px 0 16px;
  font-size: 18px;
  font-weight: 600;
}

.section-header-subtitle {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  font-weight: 400;
}

.service-card {
  height: 100%;
}

.runtime-card {
  height: 100%;
}

.service-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.runtime-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.service-card-title {
  font-size: 18px;
  font-weight: 600;
}

.service-card-description {
  margin-top: 8px;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}

.service-card-meta {
  margin-top: 20px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-light);
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.aggregate-panel {
  margin-bottom: 18px;
}

.runtime-empty-state {
  padding: 12px 0;
}

.runtime-empty-text {
  margin: 0;
}

.aggregate-title {
  margin-bottom: 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  font-weight: 600;
}

.aggregate-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.aggregate-item {
  border-radius: 12px;
  padding: 12px 14px;
  border: 1px solid var(--el-border-color-light);
}

.aggregate-item.is-error {
  background-color: rgba(254, 242, 242, 0.72);
  border-color: rgba(239, 68, 68, 0.16);
}

.aggregate-item.is-warning {
  background-color: rgba(255, 251, 235, 0.72);
  border-color: rgba(245, 158, 11, 0.16);
}

.aggregate-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.event-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.event-item {
  border-radius: 14px;
  padding: 14px 16px;
  border: 1px solid var(--el-border-color-light);
  background-color: rgba(248, 250, 252, 0.92);
}

.event-item.is-error {
  background-color: rgba(254, 242, 242, 0.92);
  border-color: rgba(239, 68, 68, 0.18);
}

.event-item.is-warning {
  background-color: rgba(255, 251, 235, 0.92);
  border-color: rgba(245, 158, 11, 0.18);
}

.event-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.event-title {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.event-path {
  font-family: Consolas, 'Courier New', monospace;
  font-size: 13px;
  word-break: break-all;
}

.event-meta {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.detail-block {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.event-detail {
  color: var(--el-text-color-regular);
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.detail-toggle {
  padding: 0;
  min-height: auto;
}

:deep(.el-card) {
  border-radius: 16px;
  border-color: rgba(15, 23, 42, 0.08);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
}

@media (max-width: 1100px) {
  .summary-layout {
    grid-template-columns: 1fr;
  }
}

@media (--mobile-viewport) {
  .page-container {
    padding: 16px;
  }

  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .page-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .page-title {
    font-size: 22px;
  }

  .summary-status-title {
    font-size: 24px;
  }

  .summary-status {
    align-items: flex-start;
  }

  .section-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .system-metric,
  .uptime-metric {
    min-height: 200px;
  }
}
</style>

