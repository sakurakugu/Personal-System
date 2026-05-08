import { reactive, ref, watch } from 'vue'
import type { ApiEnvironmentConnectivityStatus } from './connectivity'
import { normalizeApiEnvironmentBaseUrl, type ApiEnvironmentItem } from './store'

export interface ApiEnvironmentManagerSubmitPayload {
  editingId: string | null
  name: string
  baseUrl: string
}

export interface ApiEnvironmentManagerProps {
  environments: ApiEnvironmentItem[]
  activeEnvironmentId: string
  loading: boolean
  refreshing: boolean
  showCloseButton?: boolean
  createActionText: string
  updateActionText: string
  getStatus: (id: string) => ApiEnvironmentConnectivityStatus
  onRefresh: () => void | Promise<void>
  onClose?: () => void | Promise<void>
  onSelect: (id: string) => void | Promise<void>
  onSubmit: (payload: ApiEnvironmentManagerSubmitPayload) => void | Promise<void>
  onRemove: (id: string) => void | Promise<void>
}

export function useApiEnvironmentManager(props: ApiEnvironmentManagerProps) {
  const editingEnvironmentId = ref<string | null>(null)
  const formErrorMessage = ref('')
  const environmentForm = reactive({
    name: '',
    baseUrl: '',
  })

  function resetEnvironmentForm() {
    editingEnvironmentId.value = null
    formErrorMessage.value = ''
    environmentForm.name = ''
    environmentForm.baseUrl = ''
  }

  function handleEditEnvironment(item: ApiEnvironmentItem) {
    formErrorMessage.value = ''
    editingEnvironmentId.value = item.id
    environmentForm.name = item.name
    environmentForm.baseUrl = item.baseUrl
  }

  async function handleSelectEnvironment(id: string) {
    await props.onSelect(id)
  }

  async function handleRefreshConnectivity() {
    await props.onRefresh()
  }

  async function handleClose() {
    resetEnvironmentForm()
    if (props.onClose) {
      await props.onClose()
    }
  }

  async function handleRemoveEnvironment(id: string) {
    await props.onRemove(id)
    if (editingEnvironmentId.value === id) {
      resetEnvironmentForm()
    }
  }

  async function handleSubmitEnvironment() {
    const name = environmentForm.name.trim()
    const baseUrl = normalizeApiEnvironmentBaseUrl(environmentForm.baseUrl)

    if (!name) {
      formErrorMessage.value = '请输入环境名称'
      return
    }
    if (!/^https?:\/\//.test(baseUrl)) {
      formErrorMessage.value = '接口基址必须以 http:// 或 https:// 开头'
      return
    }

    formErrorMessage.value = ''
    await props.onSubmit({
      editingId: editingEnvironmentId.value,
      name,
      baseUrl,
    })
    resetEnvironmentForm()
  }

  watch(
    () => props.environments,
    (items) => {
      if (!editingEnvironmentId.value) {
        return
      }
      if (!items.some((item) => item.id === editingEnvironmentId.value)) {
        resetEnvironmentForm()
      }
    },
    { deep: false },
  )

  return {
    editingEnvironmentId,
    formErrorMessage,
    environmentForm,
    resetEnvironmentForm,
    handleEditEnvironment,
    handleSelectEnvironment,
    handleRefreshConnectivity,
    handleClose,
    handleRemoveEnvironment,
    handleSubmitEnvironment,
  }
}
