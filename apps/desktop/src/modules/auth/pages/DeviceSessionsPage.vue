<script setup lang="ts">
import { Delete, Monitor, RefreshRight } from '@element-plus/icons-vue'
import {
  ElAlert,
  ElButton,
  ElCard,
  ElEmpty,
  ElIcon,
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
import { listDeviceSessions, revokeDeviceSession, useAuthStore } from '@personal-system/domain/auth'
import type { DeviceSessionInfo } from '@personal-system/domain/auth'
import { getApiErrorMessage } from '@personal-system/api'

type DeviceSessionTableItem = DeviceSessionInfo & {
  is_current: boolean
}

const auth = useAuthStore()
const loading = ref(true)
const refreshing = ref(false)
const revokingSessionId = ref<string | null>(null)
const sessions = ref<DeviceSessionTableItem[]>([])

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
              <span>设备会话列表</span>
              <ElText type="info">当前活跃 {{ activeSessions.length }} 台设备</ElText>
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
</style>
