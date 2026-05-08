import { computed, ref } from 'vue'
import { useApiEnvironmentConnectivity } from './connectivity'
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

export function useApiEnvironmentPage(options: UseApiEnvironmentPageOptions) {
  const environmentLoading = ref(false)
  const canSwitchEnvironment = computed(() => options.store.canSwitchEnvironment)
  const activeEnvironmentId = computed(() => options.store.activeEnvironmentId)
  const activeBaseUrl = computed(() => options.store.activeBaseUrl)
  const environments = computed(() => options.store.environments)
  const { refreshing: connectivityRefreshing, refreshConnectivity, getSnapshot } = useApiEnvironmentConnectivity(environments)

  async function reloadAfterEnvironmentChange() {
    try {
      await options.logout()
    } catch {
      // 后端不可达时也要允许本地退出并刷新。
    }
    window.location.reload()
  }

  async function handleSelectEnvironment(id: string) {
    if (id === options.store.activeEnvironmentId) {
      return
    }
    environmentLoading.value = true
    try {
      options.store.setActiveEnvironment(id)
      await reloadAfterEnvironmentChange()
    } finally {
      environmentLoading.value = false
    }
  }

  async function handleRemoveEnvironment(id: string) {
    const removedActive = options.store.activeEnvironmentId === id
    options.store.removeEnvironment(id)
    if (!removedActive) {
      return
    }

    environmentLoading.value = true
    try {
      await reloadAfterEnvironmentChange()
    } finally {
      environmentLoading.value = false
    }
  }

  async function handleSubmitEnvironment(payload: ApiEnvironmentManagerSubmitPayload) {
    environmentLoading.value = true
    try {
      const currentActiveId = options.store.activeEnvironmentId
      const currentActiveBaseUrl = activeBaseUrl.value

      if (payload.editingId) {
        const targetId = payload.editingId
        options.store.updateEnvironment(targetId, payload.name, payload.baseUrl)
        if (targetId === currentActiveId && payload.baseUrl !== currentActiveBaseUrl) {
          await reloadAfterEnvironmentChange()
        }
        return
      }

      options.store.addEnvironment(payload.name, payload.baseUrl)
      await reloadAfterEnvironmentChange()
    } finally {
      environmentLoading.value = false
    }
  }

  function getEnvironmentStatus(id: string) {
    return getSnapshot(id).status
  }

  return {
    environmentLoading,
    canSwitchEnvironment,
    activeEnvironmentId,
    environments,
    connectivityRefreshing,
    refreshConnectivity,
    handleSelectEnvironment,
    handleRemoveEnvironment,
    handleSubmitEnvironment,
    getEnvironmentStatus,
  }
}
