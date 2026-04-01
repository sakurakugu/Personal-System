<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElButton, ElForm, ElFormItem, ElInput, ElMessage, ElTag } from 'element-plus'
import BaseDialog from './BaseDialog.vue'
import { useApiEnvironmentStore } from '../stores/api-environment'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const environmentStore = useApiEnvironmentStore()
const editingId = ref<string | null>(null)
const form = ref({
  name: '',
  baseUrl: '',
})

const dialogTitle = computed(() => editingId.value ? '编辑接口环境' : '接口环境切换')

watch(() => props.modelValue, (value) => {
  if (!value) {
    resetForm()
  }
}, { immediate: true })

function resetForm() {
  editingId.value = null
  form.value = {
    name: '',
    baseUrl: '',
  }
}

function handleSelect(id: string) {
  environmentStore.setActiveEnvironment(id)
  ElMessage.success('已切换接口环境')
}

function handleEdit(id: string) {
  const item = environmentStore.environments.find((env) => env.id === id)
  if (!item) {
    return
  }
  editingId.value = id
  form.value = {
    name: item.name,
    baseUrl: item.baseUrl,
  }
}

function handleRemove(id: string) {
  environmentStore.removeEnvironment(id)
  if (editingId.value === id) {
    resetForm()
  }
  ElMessage.success('已删除环境')
}

function handleSubmit() {
  const name = form.value.name.trim()
  const baseUrl = form.value.baseUrl.trim()

  if (!name) {
    ElMessage.warning('请填写环境名称')
    return
  }
  if (!/^https?:\/\//.test(baseUrl)) {
    ElMessage.warning('接口地址必须以 http:// 或 https:// 开头')
    return
  }

  if (editingId.value) {
    environmentStore.updateEnvironment(editingId.value, name, baseUrl)
    ElMessage.success('环境已更新')
  } else {
    environmentStore.addEnvironment(name, baseUrl)
    ElMessage.success('环境已新增并切换')
  }
  resetForm()
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="dialogTitle"
    width="640px"
    style="max-width: 96vw"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="api-env-dialog">
      <div class="api-env-tip">
        当前环境切换后立即生效，后续接口请求会直接使用新的地址。
      </div>

      <div class="api-env-list">
        <button
          v-for="item in environmentStore.environments"
          :key="item.id"
          type="button"
          class="api-env-card"
          :class="{ 'is-active': item.id === environmentStore.activeEnvironmentId }"
          @click="handleSelect(item.id)"
        >
          <div class="api-env-card-main">
            <div class="api-env-card-header">
              <span class="api-env-name">{{ item.name }}</span>
              <ElTag v-if="item.id === environmentStore.activeEnvironmentId" type="success">当前</ElTag>
            </div>
            <div class="api-env-url">{{ item.baseUrl }}</div>
          </div>
          <div class="api-env-actions" @click.stop>
            <ElButton size="small" text @click="handleEdit(item.id)">编辑</ElButton>
            <ElButton
              v-if="item.id.startsWith('custom-')"
              size="small"
              text
              type="danger"
              @click="handleRemove(item.id)"
            >
              删除
            </ElButton>
          </div>
        </button>
      </div>

      <div class="api-env-form">
        <ElForm label-position="top">
          <ElFormItem :label="editingId ? '修改环境名称' : '新增环境名称'">
            <ElInput v-model="form.name" placeholder="例如：家里电脑 / 办公室服务端" />
          </ElFormItem>
          <ElFormItem label="接口基址">
            <ElInput v-model="form.baseUrl" placeholder="http://192.168.1.23:8000/api/v1" />
          </ElFormItem>
        </ElForm>
        <div class="api-env-form-actions">
          <ElButton type="primary" @click="handleSubmit">
            {{ editingId ? '保存修改' : '新增并切换' }}
          </ElButton>
          <ElButton v-if="editingId" @click="resetForm">取消编辑</ElButton>
        </div>
      </div>
    </div>
  </BaseDialog>
</template>

<style scoped>
.api-env-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.api-env-tip {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.api-env-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.api-env-card {
  width: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  background: var(--el-bg-color-overlay);
  cursor: pointer;
  text-align: left;
}

.api-env-card.is-active {
  border-color: #18a058;
  box-shadow: 0 0 0 1px rgba(24, 160, 88, 0.12);
}

.api-env-card-main {
  min-width: 0;
  flex: 1;
}

.api-env-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.api-env-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.api-env-url {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  word-break: break-all;
}

.api-env-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
}

.api-env-form {
  padding-top: 4px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.api-env-form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
