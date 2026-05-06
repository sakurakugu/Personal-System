<script setup lang="ts">
import AppIconButton from '@/shared/components/AppIconButton.vue'
import type { ApiEnvironmentConnectivityStatus } from '@/shared/composables/use-api-environment-connectivity'
import type { ApiEnvironmentItem } from '@/shared/stores/api-environment'
import { ElAlert, ElButton, ElForm, ElFormItem, ElInput, ElTag } from 'element-plus'
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
const formErrorMessage = ref('')
const environmentForm = reactive({
  name: '',
  baseUrl: '',
})

function normalizeBaseUrl(value: string) {
  return value.trim().replace(/\/+$/, '')
}

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
  const baseUrl = normalizeBaseUrl(environmentForm.baseUrl)

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
</script>

<template>
  <div class="stack">
    <div class="section-heading">
      <span class="field-label">接口环境</span>
      <div class="api-environment-manager__actions">
        <AppIconButton
          size="sm"
          :disabled="loading || refreshing"
          label="重新检测接口环境"
          @click="handleRefreshConnectivity"
        >
          <Refresh :class="{ 'api-environment-manager__refresh-icon--spinning': refreshing }" aria-hidden="true" />
        </AppIconButton>
        <AppIconButton
          v-if="showCloseButton"
          size="sm"
          :disabled="loading"
          label="关闭接口环境设置"
          @click="handleClose"
        >
          <Close aria-hidden="true" />
        </AppIconButton>
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
          <div class="api-environment-manager__title-row">
            <strong>{{ item.name }}</strong>
            <ElTag
              size="small"
              effect="plain"
              :type="getStatus(item.id) === 'reachable' ? 'success' : getStatus(item.id) === 'unreachable' ? 'danger' : 'info'"
            >
              {{ getStatus(item.id) === 'reachable' ? '可用' : getStatus(item.id) === 'unreachable' ? '不可达' : '检测中' }}
            </ElTag>
          </div>
          <span class="env-card__url">{{ item.baseUrl }}</span>
        </div>
        <div class="env-card__actions" @click.stop>
          <AppIconButton
            size="sm"
            :disabled="loading"
            label="编辑接口环境"
            @click="handleEditEnvironment(item)"
          >
            <EditPen aria-hidden="true" />
          </AppIconButton>
          <ElButton
            v-if="item.id.startsWith('custom-')"
            class="api-environment-manager__danger-button"
            plain
            :disabled="loading"
            @click="handleRemoveEnvironment(item.id)"
          >
            删除
          </ElButton>
        </div>
      </button>
    </div>

    <ElForm class="stack env-form" label-position="top">
      <ElFormItem :label="editingEnvironmentId ? '修改环境名称' : '新增环境名称'" class="api-environment-manager__form-item">
        <ElInput
          v-model="environmentForm.name"
          class="api-environment-manager__input"
          placeholder="例如：办公室服务端"
          clearable
        />
      </ElFormItem>
      <ElFormItem label="接口基址" class="api-environment-manager__form-item">
        <ElInput
          v-model="environmentForm.baseUrl"
          class="api-environment-manager__input"
          placeholder="http://192.168.1.23:8000/api/v1"
          clearable
        />
      </ElFormItem>
      <ElAlert v-if="formErrorMessage" class="api-environment-manager__error" :closable="false" type="error" :title="formErrorMessage" />
      <div class="button-row">
        <ElButton class="api-environment-manager__primary-button" type="primary" :loading="loading" @click="handleSubmitEnvironment">
          {{ editingEnvironmentId ? updateActionText : createActionText }}
        </ElButton>
        <ElButton
          v-if="editingEnvironmentId"
          class="api-environment-manager__secondary-button"
          plain
          :disabled="loading"
          @click="resetEnvironmentForm"
        >
          取消
        </ElButton>
      </div>
    </ElForm>
  </div>
</template>

<style scoped>
.api-environment-manager__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.env-card {
  width: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--theme-card-border);
  border-radius: 18px;
  background: var(--theme-panel-muted);
  text-align: left;
  color: var(--text-primary);
}

.env-card--active {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--el-color-primary) 24%, transparent);
}

.env-card--reachable {
  border-color: color-mix(in srgb, var(--theme-success-strong) 28%, transparent);
  background: color-mix(in srgb, var(--theme-success-soft) 50%, var(--theme-panel-soft));
}

.env-card--unreachable {
  border-color: color-mix(in srgb, var(--theme-danger-strong) 24%, transparent);
  background: color-mix(in srgb, var(--theme-danger-soft) 44%, var(--theme-panel-soft));
}

.env-card__content {
  min-width: 0;
  display: grid;
  gap: 6px;
}

.env-card__url {
  color: var(--text-tertiary);
  font-size: 0.88rem;
  word-break: break-all;
}

.env-card__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.api-environment-manager__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.env-form {
  padding-top: 18px;
  border-top: 1px solid var(--theme-card-border);
}

.button-row {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.api-environment-manager__danger-button {
  border-radius: 14px;
}

.api-environment-manager__form-item {
  margin-bottom: 0;
}

.api-environment-manager__form-item :deep(.el-form-item__label) {
  padding-bottom: 8px;
  line-height: 1.3;
  font-size: 0.9rem;
  color: var(--theme-accent-strong);
}

.api-environment-manager__input {
  width: 100%;
}

.api-environment-manager__input :deep(.el-input__wrapper) {
  padding: 0 16px;
  border-radius: 16px;
  background: var(--theme-input-bg);
  box-shadow: 0 0 0 1px var(--theme-input-border) inset;
}

.api-environment-manager__input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--theme-input-border-hover) inset;
}

.api-environment-manager__input :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px var(--el-color-primary) inset,
    0 0 0 3px var(--theme-focus-ring);
}

.api-environment-manager__input :deep(.el-input__inner) {
  height: 48px;
  color: var(--text-primary);
}

.api-environment-manager__input :deep(.el-input__inner::placeholder) {
  color: var(--text-quaternary);
}

.api-environment-manager__input :deep(.el-input__clear) {
  color: color-mix(in srgb, var(--theme-accent-strong) 70%, transparent);
}

.api-environment-manager__input :deep(.el-input__clear:hover) {
  color: var(--theme-accent-strong);
}

.api-environment-manager__error {
  margin: 2px 0;
}

.api-environment-manager__error :deep(.el-alert) {
  border-radius: 14px;
}

.api-environment-manager__primary-button,
.api-environment-manager__secondary-button {
  border-radius: 16px;
}

.api-environment-manager__primary-button {
  min-height: 44px;
  border: 0;
  background: var(--theme-accent-gradient);
}

.api-environment-manager__primary-button:hover,
.api-environment-manager__primary-button:focus-visible {
  background: var(--theme-accent-gradient-hover);
}

.api-environment-manager__secondary-button {
  min-height: 44px;
  color: var(--theme-accent-strong);
  border-color: var(--theme-card-border);
  background: var(--theme-panel-soft);
}

.api-environment-manager__refresh-icon--spinning {
  animation: api-environment-manager-spin 0.9s linear infinite;
}

@keyframes api-environment-manager-spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}
</style>
