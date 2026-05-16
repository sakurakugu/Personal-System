import { computed, onMounted, ref, watch, type ComputedRef } from 'vue'
import type { ApiEnvironmentItem } from './store'

export type ApiEnvironmentConnectivityStatus = 'idle' | 'checking' | 'reachable' | 'unreachable'

interface ConnectivitySnapshot {
  status: ApiEnvironmentConnectivityStatus
  message: string
}

function 构建健康检查URL(baseUrl: string): string {
  return `${baseUrl.replace(/\/+$/, '')}/health`
}

async function 探测环境(baseUrl: string): Promise<ConnectivitySnapshot> {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), 5000)

  try {
    const response = await fetch(构建健康检查URL(baseUrl), {
      method: 'GET',
      signal: controller.signal,
    })

    if (response.status === 200) {
      return {
        status: 'reachable',
        message: '可联通',
      }
    }

    if (response.status === 503) {
      return {
        status: 'reachable',
        message: '服务可达，但存在组件异常',
      }
    }

    return {
      status: 'unreachable',
      message: '无法连接',
    }
  } catch {
    return {
      status: 'unreachable',
      message: '无法连接',
    }
  } finally {
    window.clearTimeout(timeoutId)
  }
}

export function 使用API环境连接性(environments: ComputedRef<ApiEnvironmentItem[]>) {
  const snapshots = ref<Record<string, ConnectivitySnapshot>>({})
  const refreshing = ref(false)
  let refreshVersion = 0

  const environmentSignature = computed(() => {
    return environments.value.map((item) => `${item.id}:${item.baseUrl}`).join('|')
  })

  function 获取快照(id: string): ConnectivitySnapshot {
    return snapshots.value[id] || {
      status: 'idle',
      message: '未检测',
    }
  }

  async function 刷新连接性() {
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
      const snapshot = await 探测环境(item.baseUrl)
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
    void 刷新连接性()
  }, { immediate: true })

  onMounted(() => {
    if (!refreshing.value) {
      void 刷新连接性()
    }
  })

  return {
    refreshing,
    refreshConnectivity: 刷新连接性,
    getSnapshot: 获取快照,
  }
}
