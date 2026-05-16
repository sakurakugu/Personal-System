<script setup lang="ts">
import { ElAlert, ElButton, ElCard, ElDescriptions, ElDescriptionsItem, ElForm, ElFormItem, ElInput, ElMessage, ElSpace, ElText } from 'element-plus'
import { ref } from 'vue'
import { BaseDialog } from '@personal-system/ui'
import {
  issueWidgetToken,
} from '@personal-system/domain/auth'
import type { DeviceLoginResponse, DeviceSessionInfo } from '@personal-system/domain/auth'
import { getApiErrorMessage } from '@personal-system/api'

const props = defineProps<{
  syncToken?: (payload: { token: string; widgetName: string }) => Promise<string>
}>()

const issuingWidgetToken = ref(false)
const syncingWidgetToken = ref(false)
const widgetDialogVisible = ref(false)
const issuedWidgetPayload = ref<DeviceLoginResponse | null>(null)
const widgetForm = ref({
  device_name: 'Personal System Widget',
  client_version: '0.1.0',
  platform: navigator.platform || 'desktop',
})

function formatDateTime(value: string | null): string {
  if (!value) {
    return '未记录'
  }
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

function formatScopeLabel(scope: DeviceSessionInfo['scope']): string {
  if (scope === 'widget_basic') {
    return '小工具受限权限'
  }
  return '完整客户端权限'
}

function formatDeviceTypeLabel(deviceType: DeviceSessionInfo['device_type']): string {
  if (deviceType === 'desktop') {
    return '桌面端'
  }
  if (deviceType === 'widget') {
    return '桌面小工具'
  }
  if (deviceType === 'phone') {
    return '手机端'
  }
  return '其他设备'
}

function openWidgetDialog() {
  issuedWidgetPayload.value = null
  widgetDialogVisible.value = true
}

async function handleIssueWidgetToken() {
  issuingWidgetToken.value = true
  try {
    const payload = await issueWidgetToken({
      device_name: widgetForm.value.device_name,
      client_version: widgetForm.value.client_version || undefined,
      platform: widgetForm.value.platform || undefined,
    })
    issuedWidgetPayload.value = payload
    ElMessage.success('小工具凭证已生成')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '生成小工具凭证失败'))
  } finally {
    issuingWidgetToken.value = false
  }
}

async function copyIssuedWidgetToken() {
  const token = issuedWidgetPayload.value?.token
  if (!token) {
    return
  }

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(token)
    } else {
      const textArea = document.createElement('textarea')
      textArea.value = token
      textArea.style.position = 'fixed'
      textArea.style.opacity = '0'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
    }
    ElMessage.success('小工具凭证已复制')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '复制小工具凭证失败'))
  }
}

async function syncIssuedWidgetToken() {
  const token = issuedWidgetPayload.value?.token
  if (!token || !props.syncToken) {
    return
  }

  syncingWidgetToken.value = true
  try {
    const configPath = await props.syncToken({
      token,
      widgetName: widgetForm.value.device_name,
    })
    ElMessage.success(`已同步到桌面小工具：${configPath}`)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '同步小工具凭证失败'))
  } finally {
    syncingWidgetToken.value = false
  }
}
</script>

<template>
  <ElCard>
    <template #header>
      <div class="card-header">
        <div class="card-header-title">
          <span>小工具接入</span>
          <ElText type="info">通过当前桌面端为 Qt 小工具签发 `widget_basic` 凭证</ElText>
        </div>
        <ElButton type="primary" @click="openWidgetDialog">
          <span>生成小工具凭证</span>
        </ElButton>
      </div>
    </template>

    <ElSpace direction="vertical" fill :size="12">
      <ElAlert
        type="warning"
        :closable="false"
        title="生成后的凭证只会在当前窗口显示一次。可直接同步到 Qt 小工具，也可手动复制。"
      />
      <ElDescriptions :column="2" border>
        <ElDescriptionsItem label="签发来源">当前桌面端</ElDescriptionsItem>
        <ElDescriptionsItem label="目标类型">桌面小工具</ElDescriptionsItem>
        <ElDescriptionsItem label="权限范围">widget_basic</ElDescriptionsItem>
        <ElDescriptionsItem label="默认用途">待办、摘要、提醒等轻量能力</ElDescriptionsItem>
      </ElDescriptions>
    </ElSpace>
  </ElCard>

  <BaseDialog
    v-model="widgetDialogVisible"
    title="生成小工具凭证"
    width="680px"
    destroy-on-close
  >
    <ElSpace direction="vertical" fill :size="16">
      <ElAlert
        type="info"
        :closable="false"
        title="该凭证将固定使用 `widget_basic` 权限范围，适合 Qt 小工具接入。"
      />

      <ElForm label-position="top">
        <ElFormItem label="小工具名称">
          <ElInput v-model="widgetForm.device_name" maxlength="100" show-word-limit />
        </ElFormItem>
        <ElFormItem label="客户端版本">
          <ElInput v-model="widgetForm.client_version" maxlength="50" placeholder="例如 0.1.0" />
        </ElFormItem>
        <ElFormItem label="平台标识">
          <ElInput v-model="widgetForm.platform" maxlength="50" placeholder="例如 windows" />
        </ElFormItem>
      </ElForm>

      <div class="dialog-actions">
        <ElButton type="primary" :loading="issuingWidgetToken" @click="handleIssueWidgetToken">
          <span>生成凭证</span>
        </ElButton>
      </div>

      <template v-if="issuedWidgetPayload">
        <ElAlert
          type="warning"
          :closable="false"
          title="下面的 token 只会在当前界面展示，请立即复制。后续如忘记，只能重新生成。"
        />

        <ElForm label-position="top">
          <ElFormItem label="小工具 Token">
            <ElInput
              :model-value="issuedWidgetPayload.token"
              type="textarea"
              :rows="3"
              readonly
            />
          </ElFormItem>
        </ElForm>

        <div class="dialog-actions">
          <ElButton v-if="syncToken" :loading="syncingWidgetToken" @click="syncIssuedWidgetToken">
            <span>同步到桌面小工具</span>
          </ElButton>
          <ElButton type="success" @click="copyIssuedWidgetToken">
            <span>复制 Token</span>
          </ElButton>
        </div>

        <ElDescriptions :column="2" border>
          <ElDescriptionsItem label="设备名称">
            {{ issuedWidgetPayload.session.device_name }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="权限范围">
            {{ formatScopeLabel(issuedWidgetPayload.session.scope) }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="设备类型">
            {{ formatDeviceTypeLabel(issuedWidgetPayload.session.device_type) }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="过期时间">
            {{ formatDateTime(issuedWidgetPayload.session.expires_at) }}
          </ElDescriptionsItem>
        </ElDescriptions>
      </template>
    </ElSpace>
  </BaseDialog>
</template>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.card-header-title {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
}
</style>
