<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { ElCard, ElCol, ElIcon, ElInputNumber, ElProgress, ElRow, ElSkeleton } from 'element-plus'
import { Monitor } from '@element-plus/icons-vue'
import api from '../../utils/api'

const loading = ref(true)
let refreshTimer: number | undefined
const samplingSeconds = ref(5)
const sys = ref({
  cpu_percent: 0,
  memory_total_gb: 0,
  memory_used_gb: 0,
  memory_percent: 0,
  disk_total_gb: 0,
  disk_used_gb: 0,
  disk_percent: 0,
  uptime_seconds: 0,
})

async function fetchSystem() {
  const { data } = await api.get('/admin/system')
  sys.value = data
}

function startTimer() {
  if (refreshTimer !== undefined) {
    window.clearInterval(refreshTimer)
  }
  refreshTimer = window.setInterval(fetchSystem, samplingSeconds.value * 1000)
}

watch(samplingSeconds, (value) => {
  const normalized = Math.min(10, Math.max(2, value))
  if (normalized !== value) {
    samplingSeconds.value = normalized
    return
  }
  startTimer()
})

onMounted(async () => {
  try {
    await fetchSystem()
  } finally {
    loading.value = false
  }
  startTimer()
})

onUnmounted(() => {
  if (refreshTimer !== undefined) {
    window.clearInterval(refreshTimer)
    refreshTimer = undefined
  }
})

function formatUptime(seconds: number) {
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${d}天 ${h}小时 ${m}分`
}

function statusColor(pct: number): string {
  if (pct < 60) return '#18a058'
  if (pct < 85) return '#f0a020'
  return '#d03050'
}
</script>

<template>
  <div>
    <h2 style="display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 24px">
      <span style="display: inline-flex; align-items: center; gap: 8px">
        <ElIcon><Monitor /></ElIcon>
        <span>系统状态</span>
      </span>
      <span style="display: inline-flex; align-items: center; gap: 8px; font-size: 14px">
        <span>采样时间</span>
        <ElInputNumber
          v-model="samplingSeconds"
          :min="2"
          :max="10"
          :step="1"
          size="small"
          :controls="true"
          style="width: 84px"
        />
        <span>秒</span>
      </span>
    </h2>
    <ElSkeleton :loading="loading" animated>
      <ElRow :gutter="16">
        <ElCol :xs="24" :sm="8">
          <ElCard header="CPU">
            <div class="system-metric">
              <ElProgress type="circle" :percentage="sys.cpu_percent" :color="statusColor(sys.cpu_percent)" />
              <p class="system-metric-text">{{ sys.cpu_percent }}%</p>
            </div>
          </ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="8">
          <ElCard header="内存">
            <div class="system-metric">
              <ElProgress type="circle" :percentage="sys.memory_percent" :color="statusColor(sys.memory_percent)" />
              <p class="system-metric-text">{{ sys.memory_used_gb }} / {{ sys.memory_total_gb }} GB</p>
            </div>
          </ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="8">
          <ElCard header="磁盘">
            <div class="system-metric">
              <ElProgress type="circle" :percentage="sys.disk_percent" :color="statusColor(sys.disk_percent)" />
              <p class="system-metric-text">{{ sys.disk_used_gb }} / {{ sys.disk_total_gb }} GB</p>
            </div>
          </ElCard>
        </ElCol>
      </ElRow>

      <ElCard header="运行时间" style="margin-top: 16px">
        <p class="system-metric-text">{{ formatUptime(sys.uptime_seconds) }}</p>
      </ElCard>
    </ElSkeleton>
  </div>
</template>

<style scoped>
.system-metric {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.system-metric-text {
  text-align: center;
  margin-top: 8px;
}
</style>
