import { computed, ref } from 'vue'
import { 使用API环境连接性 } from './connectivity'
import type { ApiEnvironmentItem } from './store'
import type { ApiEnvironmentManagerSubmitPayload } from './manager'

export interface ApiEnvironmentStoreLike {
  canSwitchEnvironment: boolean
  activeEnvironmentId: string
  activeBaseUrl: string
  environments: ApiEnvironmentItem[]
  setActiveEnvironment: (id: string) => void
  addEnvironment: (name: string, baseUrl: string) => void
  updateEnvironment: (id: string, name: string, baseUrl: string) => void
  removeEnvironment: (id: string) => void
}

interface UseApiEnvironmentPageOptions {
  store: ApiEnvironmentStoreLike
  logout: () => Promise<unknown>
}

export function 使用API环境页面(options: UseApiEnvironmentPageOptions) {
  const environmentLoading = ref(false)
  const canSwitchEnvironment = computed(() => options.store.canSwitchEnvironment)
  const activeEnvironmentId = computed(() => options.store.activeEnvironmentId)
  const activeBaseUrl = computed(() => options.store.activeBaseUrl)
  const environments = computed(() => options.store.environments)
  const { refreshing: connectivityRefreshing, refreshConnectivity: 刷新连接性, getSnapshot: 获取快照 } = 使用API环境连接性(environments)

  async function 环境变更后重新加载() {
    try {
      await options.logout()
    } catch {
      // 后端不可达时也要允许本地退出并刷新。
    }
    window.location.reload()
  }

  async function 处理选择环境(id: string) {
    if (id === options.store.activeEnvironmentId) {
      return
    }
    environmentLoading.value = true
    try {
      options.store.setActiveEnvironment(id)
      await 环境变更后重新加载()
    } finally {
      environmentLoading.value = false
    }
  }

  async function 处理移除环境(id: string) {
    const removedActive = options.store.activeEnvironmentId === id
    options.store.removeEnvironment(id)
    if (!removedActive) {
      return
    }

    environmentLoading.value = true
    try {
      await 环境变更后重新加载()
    } finally {
      environmentLoading.value = false
    }
  }

  async function 处理提交环境(payload: ApiEnvironmentManagerSubmitPayload) {
    environmentLoading.value = true
    try {
      const currentActiveId = options.store.activeEnvironmentId
      const currentActiveBaseUrl = activeBaseUrl.value

      if (payload.editingId) {
        const targetId = payload.editingId
        options.store.updateEnvironment(targetId, payload.name, payload.baseUrl)
        if (targetId === currentActiveId && payload.baseUrl !== currentActiveBaseUrl) {
          await 环境变更后重新加载()
        }
        return
      }

      options.store.addEnvironment(payload.name, payload.baseUrl)
      await 环境变更后重新加载()
    } finally {
      environmentLoading.value = false
    }
  }

  function 获取环境状态(id: string) {
    return 获取快照(id).status
  }

  return {
    environmentLoading,
    canSwitchEnvironment,
    activeEnvironmentId,
    environments,
    connectivityRefreshing,
    refreshConnectivity: 刷新连接性,
    handleSelectEnvironment: 处理选择环境,
    handleRemoveEnvironment: 处理移除环境,
    handleSubmitEnvironment: 处理提交环境,
    getEnvironmentStatus: 获取环境状态,
  }
}
