<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NCard, NGrid, NGridItem, NStatistic, NProgress, NSpin } from 'naive-ui'
import { ElIcon } from 'element-plus'
import { Monitor } from '@element-plus/icons-vue'
import api from '../../utils/api'

const loading = ref(true)
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

onMounted(async () => {
  try {
    const { data } = await api.get('/admin/system')
    sys.value = data
  } finally {
    loading.value = false
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
    <h2 style="display: flex; align-items: center; gap: 8px; margin-bottom: 24px">
      <ElIcon><Monitor /></ElIcon>
      <span>系统状态</span>
    </h2>
    <NSpin :show="loading">
      <NGrid :cols="3" :x-gap="16" :y-gap="16" responsive="screen" :item-responsive="true">
        <NGridItem span="0:3 640:1">
          <NCard title="CPU">
            <NProgress type="circle" :percentage="sys.cpu_percent" :color="statusColor(sys.cpu_percent)" />
            <p style="text-align: center; margin-top: 8px">{{ sys.cpu_percent }}%</p>
          </NCard>
        </NGridItem>
        <NGridItem span="0:3 640:1">
          <NCard title="内存">
            <NProgress type="circle" :percentage="sys.memory_percent" :color="statusColor(sys.memory_percent)" />
            <p style="text-align: center; margin-top: 8px">{{ sys.memory_used_gb }} / {{ sys.memory_total_gb }} GB</p>
          </NCard>
        </NGridItem>
        <NGridItem span="0:3 640:1">
          <NCard title="磁盘">
            <NProgress type="circle" :percentage="sys.disk_percent" :color="statusColor(sys.disk_percent)" />
            <p style="text-align: center; margin-top: 8px">{{ sys.disk_used_gb }} / {{ sys.disk_total_gb }} GB</p>
          </NCard>
        </NGridItem>
      </NGrid>

      <NCard title="运行时间" style="margin-top: 16px">
        <NStatistic :value="formatUptime(sys.uptime_seconds)" />
      </NCard>
    </NSpin>
  </div>
</template>
