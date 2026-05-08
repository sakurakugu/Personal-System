<script setup lang="ts">
import { Close, EditPen, Refresh } from '@element-plus/icons-vue'
import { ElAlert, ElButton, ElForm, ElFormItem, ElInput } from 'element-plus'
import {
  type ApiEnvironmentConnectivityStatus,
  type ApiEnvironmentItem,
  type ApiEnvironmentManagerSubmitPayload,
  useApiEnvironmentManager,
} from '@personal-system/domain/api-environment'

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
  onSubmit: (payload: ApiEnvironmentManagerSubmitPayload) => void | Promise<void>
  onRemove: (id: string) => void | Promise<void>
}

const props = withDefaults(defineProps<Props>(), {
  showCloseButton: false,
  onClose: undefined,
})

const {
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
} = useApiEnvironmentManager(props)
</script>

<template>
  <div class="stack">
    <div class="section-heading">
      <span class="field-label">接口环境</span>
      <div class="api-environment-manager__actions">
        <ElButton
          class="api-environment-manager__icon-button api-environment-manager__icon-button--sm"
          :disabled="loading || refreshing"
          aria-label="重新检测接口环境"
          @click="handleRefreshConnectivity"
        >
          <Refresh :class="{ 'api-environment-manager__refresh-icon--spinning': refreshing }" aria-hidden="true" />
        </ElButton>
        <ElButton
          v-if="showCloseButton"
          class="api-environment-manager__icon-button api-environment-manager__icon-button--sm"
          :disabled="loading"
          aria-label="关闭接口环境设置"
          @click="handleClose"
        >
          <Close aria-hidden="true" />
        </ElButton>
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
          </div>
          <span class="env-card__url">{{ item.baseUrl }}</span>
        </div>
        <div class="env-card__actions" @click.stop>
          <ElButton
            class="api-environment-manager__icon-button api-environment-manager__icon-button--sm"
            :disabled="loading"
            aria-label="编辑接口环境"
            @click="handleEditEnvironment(item)"
          >
            <EditPen aria-hidden="true" />
          </ElButton>
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
.stack {
  display: grid;
  gap: 14px;
}

.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.field-label {
  font-size: 0.9rem;
  color: var(--theme-accent-strong);
}

.api-environment-manager__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
}

.api-environment-manager__icon-button {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  width: 42px;
  height: 42px;
  padding: 0;
  border: 1px solid var(--theme-card-border);
  --el-button-border-radius: 12px;
  border-radius: var(--el-button-border-radius);
  color: var(--theme-accent-strong);
  background: var(--theme-panel-soft);
  box-shadow: none;
}

.api-environment-manager__icon-button:hover {
  color: var(--theme-accent-deeper);
  background: var(--theme-accent-soft);
}

.api-environment-manager__icon-button:disabled {
  opacity: 0.6;
}

.api-environment-manager__icon-button--sm {
  min-width: 40px;
  width: 40px;
  height: 40px;
}

.api-environment-manager__icon-button :deep(.el-icon),
.api-environment-manager__icon-button :deep(svg) {
  width: 20px;
  height: 20px;
  color: currentColor;
  fill: currentColor;
}

.api-environment-manager__icon-button--sm :deep(.el-icon),
.api-environment-manager__icon-button--sm :deep(svg) {
  width: 18px;
  height: 18px;
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
  flex-wrap: nowrap;
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
  flex-wrap: nowrap;
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

@media (max-width: 640px) {
  .env-card {
    gap: 10px;
  }

  .env-card__actions {
    flex-wrap: wrap;
  }

  .button-row {
    flex-wrap: wrap;
  }
}
</style>
