<script setup lang="ts">
import { Delete, Monitor, RefreshRight } from '@element-plus/icons-vue'
import {
  ElAlert,
  ElButton,
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElDialog,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElMessage,
  ElPopconfirm,
  ElSkeleton,
  ElSpace,
  ElTable,
  ElTableColumn,
  ElTag,
  ElText,
} from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import {
  issueWidgetToken,
  listDeviceSessions,
  revokeAllDeviceSessions,
  revokeDeviceSession,
  useAuthStore,
} from '@personal-system/domain/auth'
import type { DeviceLoginResponse, DeviceSessionInfo } from '@personal-system/domain/auth'
import { getApiErrorMessage } from '@personal-system/api'

type DeviceSessionTableItem = DeviceSessionInfo & {
  is_current: boolean
}

const auth = useAuthStore()
const loading = ref(true)
const refreshing = ref(false)
const revokingSessionId = ref<string | null>(null)
const revokingAll = ref(false)
const sessions = ref<DeviceSessionTableItem[]>([])

const widgetDialogVisible = ref(false)
const issuingWidgetToken = ref(false)
const issuedWidgetPayload = ref<DeviceLoginResponse | null>(null)
const widgetForm = ref({
  device_name: 'Personal System Widget',
  client_version: '0.1.0',
  platform: navigator.platform || 'desktop',
})

const activeSessions = computed(() => sessions.value.filter((item) => !item.revoked_at))

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

async function loadSessions(options: { silent?: boolean } = {}) {
  const { silent = false } = options
  if (silent) {
    refreshing.value = true
  } else {
    loading.value = true
  }

  try {
    const data = await listDeviceSessions()
    sessions.value = data.map((item) => ({
      ...item,
      is_current: Boolean(item.is_current),
    }))
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '加载设备会话失败'))
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

async function handleRevoke(sessionId: string) {
  revokingSessionId.value = sessionId
  try {
    await revokeDeviceSession(sessionId)
    ElMessage.success('设备会话已吊销')
    await loadSessions({ silent: true })
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '吊销设备会话失败'))
  } finally {
    revokingSessionId.value = null
  }
}

async function handleRevokeAll() {
  revokingAll.value = true
  try {
    await revokeAllDeviceSessions()
    ElMessage.success('全部原生设备会话已吊销')
    await loadSessions({ silent: true })
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '批量吊销设备会话失败'))
  } finally {
    revokingAll.value = false
  }
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
    await loadSessions({ silent: true })
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

onMounted(async () => {
  try {
    await auth.restoreUserIfNeeded()
    await loadSessions()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h1>
        <ElIcon><Monitor /></ElIcon>
        <span>登录设备</span>
      </h1>
      <ElButton :loading="refreshing" @click="loadSessions({ silent: true })">
        <ElIcon><RefreshRight /></ElIcon>
        <span>刷新</span>
      </ElButton>
    </div>

    <ElSkeleton :loading="loading" animated>
      <ElSpace direction="vertical" fill :size="16">
        <ElAlert
          type="info"
          :closable="false"
          title="桌面端当前使用设备令牌登录，这里列出的就是原生设备会话。"
        />

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
              title="生成后的凭证只会在当前窗口显示一次。请立即复制到 Qt 小工具配置中。"
            />
            <ElDescriptions :column="2" border>
              <ElDescriptionsItem label="签发来源">当前桌面端</ElDescriptionsItem>
              <ElDescriptionsItem label="目标类型">桌面小工具</ElDescriptionsItem>
              <ElDescriptionsItem label="权限范围">widget_basic</ElDescriptionsItem>
              <ElDescriptionsItem label="默认用途">待办、摘要、提醒等轻量能力</ElDescriptionsItem>
            </ElDescriptions>
          </ElSpace>
        </ElCard>

        <ElCard>
          <template #header>
            <div class="card-header">
              <div class="card-header-title">
                <span>设备会话列表</span>
                <ElText type="info">当前活跃 {{ activeSessions.length }} 台设备</ElText>
              </div>
              <ElPopconfirm
                v-if="activeSessions.length > 0"
                title="确认吊销全部原生设备会话？"
                width="260"
                @confirm="handleRevokeAll"
              >
                <template #reference>
                  <ElButton type="danger" plain :loading="revokingAll">
                    <ElIcon><Delete /></ElIcon>
                    <span>踢掉全部原生设备</span>
                  </ElButton>
                </template>
              </ElPopconfirm>
            </div>
          </template>

          <ElEmpty v-if="sessions.length === 0" description="暂无设备会话记录" />

          <ElTable v-else :data="sessions" border stripe>
            <ElTableColumn label="设备" min-width="220">
              <template #default="{ row }">
                <div class="device-cell">
                  <div class="device-name-row">
                    <strong>{{ row.device_name }}</strong>
                    <ElTag v-if="row.is_current" size="small" type="success">当前设备</ElTag>
                    <ElTag v-if="row.revoked_at" size="small" type="info">已吊销</ElTag>
                  </div>
                  <ElText type="info">{{ formatDeviceTypeLabel(row.device_type) }}</ElText>
                </div>
              </template>
            </ElTableColumn>

            <ElTableColumn label="权限范围" min-width="160">
              <template #default="{ row }">
                <ElTag :type="row.scope === 'widget_basic' ? 'warning' : 'primary'" effect="plain">
                  {{ formatScopeLabel(row.scope) }}
                </ElTag>
              </template>
            </ElTableColumn>

            <ElTableColumn label="最近活跃" min-width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.last_used_at) }}
              </template>
            </ElTableColumn>

            <ElTableColumn label="过期时间" min-width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.expires_at) }}
              </template>
            </ElTableColumn>

            <ElTableColumn label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <ElPopconfirm
                  v-if="!row.revoked_at"
                  title="确认吊销该设备会话？"
                  width="220"
                  @confirm="handleRevoke(row.id)"
                >
                  <template #reference>
                    <ElButton type="danger" text :loading="revokingSessionId === row.id">
                      <ElIcon><Delete /></ElIcon>
                      <span>吊销</span>
                    </ElButton>
                  </template>
                </ElPopconfirm>
                <ElText v-else type="info">已失效</ElText>
              </template>
            </ElTableColumn>
          </ElTable>
        </ElCard>
      </ElSpace>
    </ElSkeleton>

    <ElDialog
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
    </ElDialog>
  </div>
</template>

<style scoped>
.page-container {
  display: grid;
  gap: 20px;
  padding: 28px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.page-header h1 {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

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

.device-cell {
  display: grid;
  gap: 4px;
}

.device-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
}
</style>
