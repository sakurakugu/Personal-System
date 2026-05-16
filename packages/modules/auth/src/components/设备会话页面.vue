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
import {
  获取设备会话列表,
  撤销所有设备会话,
  撤销设备会话,
  使用认证存储,
} from '@personal-system/domain/auth'
import type { DeviceSessionInfo } from '@personal-system/domain/auth'
import { 获取API错误消息 } from '@personal-system/api'

type DeviceSessionTableItem = DeviceSessionInfo & {
  is_current: boolean
}

const props = withDefaults(defineProps<{
  infoTitle?: string
}>(), {
  infoTitle: '这里管理的是原生设备令牌会话，当前浏览器 Cookie 登录不会出现在列表中。',
})

const auth = 使用认证存储()
const loading = ref(true)
const refreshing = ref(false)
const revokingSessionId = ref<string | null>(null)
const revokingAll = ref(false)
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
    const data = await 获取设备会话列表()
    sessions.value = data.map((item) => ({
      ...item,
      is_current: Boolean(item.is_current),
    }))
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '加载设备会话失败'))
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

async function handleRevoke(sessionId: string) {
  revokingSessionId.value = sessionId
  try {
    await 撤销设备会话(sessionId)
    ElMessage.success('设备会话已吊销')
    await loadSessions({ silent: true })
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '吊销设备会话失败'))
  } finally {
    revokingSessionId.value = null
  }
}

async function handleRevokeAll() {
  revokingAll.value = true
  try {
    await 撤销所有设备会话()
    ElMessage.success('全部原生设备会话已吊销')
    await loadSessions({ silent: true })
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '批量吊销设备会话失败'))
  } finally {
    revokingAll.value = false
  }
}

onMounted(async () => {
  try {
    await auth.需要时恢复用户()
    await loadSessions()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">
        <ElIcon><Monitor /></ElIcon>
        <span>登录设备</span>
      </h2>
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
          :title="infoTitle"
        />

        <slot name="before-list" />

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

          <ElTable v-else :data="sessions" border stripe class="sessions-table">
            <ElTableColumn label="设备" min-width="220">
              <template #default="{ row }">
                <div class="device-cell">
                  <div class="device-name-row">
                    <strong>{{ row.device_name }}</strong>
                    <ElTag v-if="row.is_current" type="success" size="small">当前设备</ElTag>
                    <ElTag v-if="row.revoked_at" type="info" size="small">已吊销</ElTag>
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

            <ElTableColumn label="平台信息" min-width="180">
              <template #default="{ row }">
                <div class="meta-stack">
                  <span>{{ row.platform || '未记录平台' }}</span>
                  <ElText type="info">{{ row.client_version || '未记录版本' }}</ElText>
                </div>
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
                    <ElButton
                      type="danger"
                      text
                      :loading="revokingSessionId === row.id"
                    >
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
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 24px;
}

.page-title {
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

.sessions-table {
  width: 100%;
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

.meta-stack {
  display: grid;
  gap: 4px;
}

@media (max-width: 767px) {
  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
