import { computed, onMounted, ref, watch, type ComputedRef } from 'vue'
import axios from 'axios'
import type { ApiEnvironmentItem } from '@/shared/stores/api-environment'

export type ApiEnvironmentConnectivityStatus = 'idle' | 'checking' | 'reachable' | 'unreachable'

interface ConnectivitySnapshot {
  status: ApiEnvironmentConnectivityStatus
  message: string
}

function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, '')
}

function buildHealthCheckUrl(baseUrl: string): string {
  return `${normalizeBaseUrl(baseUrl)}/health`
}

async function probeEnvironment(baseUrl: string): Promise<ConnectivitySnapshot> {
  try {
    const response = await axios.get(buildHealthCheckUrl(baseUrl), {
      timeout: 5000,
      validateStatus: (status) => status === 200 || status === 503,
    })
    if (response.status === 200) {
      return {
        status: 'reachable',
        message: '可联通',
      }
    }
    return {
      status: 'reachable',
      message: '服务可达，但存在组件异常',
    }
  } catch {
    return {
      status: 'unreachable',
      message: '无法连接',
    }
  }
}

export function useApiEnvironmentConnectivity(environments: ComputedRef<ApiEnvironmentItem[]>) {
  const snapshots = ref<Record<string, ConnectivitySnapshot>>({})
  const refreshing = ref(false)
  let refreshVersion = 0

  const environmentSignature = computed(() => {
    return environments.value.map((item) => `${item.id}:${item.baseUrl}`).join('|')
  })

  function getSnapshot(id: string): ConnectivitySnapshot {
    return snapshots.value[id] || {
      status: 'idle',
      message: '未检测',
    }
  }

  async function refreshConnectivity() {
    const currentVersion = ++refreshVersion
    refreshing.value = true
    const nextSnapshots: Record<string, ConnectivitySnapshot> = {}

    environments.value.forEach((item) => {
      nextSnapshots[item.id] = {
        status: 'checking',
        message: '检测中',
      }
    })
    snapshots.value = nextSnapshots

    const results = await Promise.all(environments.value.map(async (item) => {
      const snapshot = await probeEnvironment(item.baseUrl)
      return {
        id: item.id,
        snapshot,
      }
    }))

    if (currentVersion !== refreshVersion) {
      return
    }

    const resolvedSnapshots: Record<string, ConnectivitySnapshot> = {}
    results.forEach(({ id, snapshot }) => {
      resolvedSnapshots[id] = snapshot
    })
    snapshots.value = resolvedSnapshots
    refreshing.value = false
  }

  watch(environmentSignature, () => {
    void refreshConnectivity()
  }, { immediate: true })

  onMounted(() => {
    if (!refreshing.value) {
      void refreshConnectivity()
    }
  })

  return {
    refreshing,
    refreshConnectivity,
    getSnapshot,
  }
}
