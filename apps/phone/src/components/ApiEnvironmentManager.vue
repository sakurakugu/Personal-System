<script setup lang="ts">
import type { ApiEnvironmentConnectivityStatus } from '@/composables/use-api-environment-connectivity'
import type { ApiEnvironmentItem } from '@/stores/api-environment'
import { Close, EditPen, Refresh } from '@element-plus/icons-vue'
import { reactive, ref, watch } from 'vue'

interface EnvironmentSubmitPayload {
  editingId: string | null
  name: string
  baseUrl: string
}

interface Props {
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
  onSubmit: (payload: EnvironmentSubmitPayload) => void | Promise<void>
  onRemove: (id: string) => void | Promise<void>
}

const props = withDefaults(defineProps<Props>(), {
  showCloseButton: false,
  onClose: undefined,
})

const editingEnvironmentId = ref<string | null>(null)
const environmentForm = reactive({
  name: '',
  baseUrl: '',
})

function normalizeBaseUrl(value: string) {
  return value.trim().replace(/\/+$/, '')
}

function resetEnvironmentForm() {
  editingEnvironmentId.value = null
  environmentForm.name = ''
  environmentForm.baseUrl = ''
}

function handleEditEnvironment(item: ApiEnvironmentItem) {
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
  const baseUrl = normalizeBaseUrl(environmentForm.baseUrl)

  if (!name) {
    return
  }
  if (!/^https?:\/\//.test(baseUrl)) {
    return
  }

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
</script>

<template>
  <div class="stack">
    <div class="section-heading">
      <span class="field-label">接口环境</span>
      <div class="api-environment-manager__actions">
        <button
          class="chip-button icon-chip-button"
          type="button"
          :disabled="loading || refreshing"
          aria-label="重新检测接口环境"
          @click="handleRefreshConnectivity"
        >
          <Refresh :class="{ 'icon-chip-button__icon--spinning': refreshing }" aria-hidden="true" />
        </button>
        <button
          v-if="showCloseButton"
          class="chip-button icon-chip-button"
          type="button"
          :disabled="loading"
          aria-label="关闭接口环境设置"
          @click="handleClose"
        >
          <Close aria-hidden="true" />
        </button>
      </div>
    </div>

    <div class="stack">
      <button
        v-for="item in environments"
        :key="item.id"
        class="env-card"
        :class="{
          'env-card--active': item.id === activeEnvironmentId,
          'env-card--reachable': getStatus(item.id) === 'reachable',
          'env-card--unreachable': getStatus(item.id) === 'unreachable',
        }"
        type="button"
        :disabled="loading"
        @click="handleSelectEnvironment(item.id)"
      >
        <div class="env-card__content">
          <strong>{{ item.name }}</strong>
          <span class="env-card__url">{{ item.baseUrl }}</span>
        </div>
        <div class="env-card__actions" @click.stop>
          <button
            class="chip-button icon-chip-button"
            type="button"
            :disabled="loading"
            aria-label="编辑接口环境"
            @click="handleEditEnvironment(item)"
          >
            <EditPen aria-hidden="true" />
          </button>
          <button
            v-if="item.id.startsWith('custom-')"
            class="chip-button chip-button--danger"
            type="button"
            :disabled="loading"
            @click="handleRemoveEnvironment(item.id)"
          >
            删除
          </button>
        </div>
      </button>
    </div>

    <div class="stack env-form">
      <label class="field">
        <span class="field-label">{{ editingEnvironmentId ? '修改环境名称' : '新增环境名称' }}</span>
        <input v-model="environmentForm.name" class="field-input" placeholder="例如：办公室服务端">
      </label>
      <label class="field">
        <span class="field-label">接口基址</span>
        <input v-model="environmentForm.baseUrl" class="field-input" placeholder="http://192.168.1.23:8000/api/v1">
      </label>
      <div class="button-row">
        <button class="ghost-button" type="button" :disabled="loading" @click="handleSubmitEnvironment">
          {{ editingEnvironmentId ? updateActionText : createActionText }}
        </button>
        <button
          v-if="editingEnvironmentId"
          class="ghost-button"
          type="button"
          :disabled="loading"
          @click="resetEnvironmentForm"
        >
          取消
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.api-environment-manager__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
