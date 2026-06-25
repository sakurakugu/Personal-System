<script setup lang="ts">
import { ChatDotRound, RefreshRight } from '@element-plus/icons-vue'
import { 解析当前API基地址 } from '@personal-system/api'
import { PageSectionShell } from '@personal-system/ui'
import {
  ElAlert,
  ElButton,
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElOption,
  ElPagination,
  ElSelect,
  ElSpace,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { 获取API错误消息 } from '../../../../shared/api'
import {
  创建MCP令牌,
  更新AI密钥,
  更新AI设置,
  测试AI配置,
  获取AI设置,
  获取AI调用日志,
} from '../../api'
import type { AIAccessPolicy, AICallLog, AISettings, MCPScope, MCPTokenCreateResponse } from '../../types'

const loading = ref(true)
const saving = ref(false)
const secretSaving = ref(false)
const testing = ref(false)
const logsLoading = ref(false)
const mcpTokenGenerating = ref(false)
const secretInput = ref('')
const testMessage = ref('你好，请用一句话介绍当前 AI 对话配置是否可用。')
const testResult = ref('')
const testDuration = ref<number | null>(null)
const mcpDeviceName = ref('本机 MCP')
const mcpScope = ref<MCPScope>('mcp_full')
const mcpTokenResult = ref<MCPTokenCreateResponse | null>(null)
const mcpImportApps = ref<MCPImportApp[]>(['codex'])
const logs = ref<AICallLog[]>([])
const logTotal = ref(0)
const logPage = ref(1)
const logPageSize = ref(10)

const form = reactive<AISettings>({
  enabled: false,
  access_policy: 'login',
  provider: 'openai_compatible',
  base_url: '',
  model: '',
  max_tokens: 1024,
  timeout_seconds: 30,
  system_prompt: '',
  allow_attachments: false,
  max_attachment_size_mb: 10,
  daily_limit_per_user: 100,
  has_secret: false,
  secret_updated_at: null,
  updated_at: null,
})

const policyOptions: Array<{ label: string; value: AIAccessPolicy }> = [
  { label: '仅登录用户', value: 'login' },
  { label: '仅管理员', value: 'admin' },
]

const providerOptions = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'OpenAI 兼容接口', value: 'openai_compatible' },
  { label: '本地模型', value: 'local' },
]

type MCPImportApp = 'claude' | 'codex' | 'gemini' | 'opencode' | 'hermes'

const mcpImportAppOptions: Array<{ label: string; value: MCPImportApp }> = [
  { label: 'Claude', value: 'claude' },
  { label: 'Codex', value: 'codex' },
  { label: 'Gemini', value: 'gemini' },
  { label: 'OpenCode', value: 'opencode' },
  { label: 'Hermes', value: 'hermes' },
]

const statusTagType = computed(() => (form.enabled ? 'success' : 'info'))
const secretStatusType = computed(() => (form.has_secret ? 'success' : 'warning'))
const mcpEndpoint = computed(() => {
  const apiBase = 解析当前API基地址()
  const normalizedBase = apiBase.replace(/\/+$/, '')
  if (/\/api\/v1$/.test(normalizedBase)) {
    return normalizedBase.replace(/\/api\/v1$/, '/mcp')
  }
  if (typeof window !== 'undefined') {
    return `${window.location.origin}/mcp`
  }
  return '/mcp'
})
const mcpClientConfig = computed(() => JSON.stringify({
  mcpServers: {
    'personal-system-cloud': {
      type: 'http',
      url: mcpEndpoint.value,
      headers: {
        Authorization: `Bearer ${mcpTokenResult.value?.token ?? '<token>'}`,
      },
    },
  },
}, null, 2))
const mcpCCSwitchDeepLink = computed(() => {
  const config = mcpClientConfig.value
  const encodedConfig = base64UrlEncode(config)
  const params = new globalThis.URLSearchParams({
    resource: 'mcp',
    apps: mcpImportApps.value.join(','),
    enabled: 'true',
    config: encodedConfig,
  })
  return `ccswitch://v1/import?${params.toString()}`
})

function base64UrlEncode(value: string): string {
  const bytes = new globalThis.TextEncoder().encode(value)
  let binary = ''
  for (const byte of bytes) {
    binary += String.fromCharCode(byte)
  }
  return globalThis.btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

function assignSettings(data: AISettings) {
  Object.assign(form, data)
}

function formatDateTime(value: string | null): string {
  if (!value) return '未记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '时间无效'
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date)
}

function statusType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  if (status === 'success') return 'success'
  if (status === 'error') return 'danger'
  return 'info'
}

async function loadSettings() {
  assignSettings(await 获取AI设置())
}

async function loadLogs() {
  logsLoading.value = true
  try {
    const data = await 获取AI调用日志(logPage.value, logPageSize.value)
    logs.value = data.items
    logTotal.value = data.total
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '调用日志加载失败'))
  } finally {
    logsLoading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  try {
    const data = await 更新AI设置({
      enabled: form.enabled,
      access_policy: form.access_policy,
      provider: form.provider,
      base_url: form.base_url,
      model: form.model,
      max_tokens: form.max_tokens,
      timeout_seconds: form.timeout_seconds,
      system_prompt: form.system_prompt,
      allow_attachments: form.allow_attachments,
      max_attachment_size_mb: form.max_attachment_size_mb,
      daily_limit_per_user: form.daily_limit_per_user,
    })
    assignSettings(data)
    ElMessage.success('AI 设置已保存')
  } catch (error) {
    ElMessage.error(获取API错误消息(error, 'AI 设置保存失败'))
  } finally {
    saving.value = false
  }
}

async function saveSecret() {
  if (!secretInput.value.trim()) {
    ElMessage.warning('请输入密钥')
    return
  }
  secretSaving.value = true
  try {
    const data = await 更新AI密钥(secretInput.value.trim())
    assignSettings(data)
    secretInput.value = ''
    ElMessage.success('AI 密钥已更新')
  } catch (error) {
    ElMessage.error(获取API错误消息(error, 'AI 密钥保存失败'))
  } finally {
    secretSaving.value = false
  }
}

async function runTest() {
  if (!testMessage.value.trim()) {
    ElMessage.warning('请输入测试消息')
    return
  }
  testing.value = true
  testResult.value = ''
  testDuration.value = null
  try {
    const data = await 测试AI配置(testMessage.value.trim())
    testResult.value = data.content
    testDuration.value = data.duration_ms
    await loadLogs()
  } catch (error) {
    ElMessage.error(获取API错误消息(error, 'AI 测试失败'))
  } finally {
    testing.value = false
  }
}

async function copyText(text: string, successMessage: string) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(successMessage)
  } catch {
    ElMessage.error('复制失败，请手动选择文本')
  }
}

function importToCCSwitch() {
  if (!mcpImportApps.value.length) {
    ElMessage.warning('请选择导入目标')
    return
  }
  window.location.href = mcpCCSwitchDeepLink.value
}

async function generateMCPToken() {
  if (!mcpDeviceName.value.trim()) {
    ElMessage.warning('请输入设备名称')
    return
  }
  mcpTokenGenerating.value = true
  try {
    mcpTokenResult.value = await 创建MCP令牌({
      device_name: mcpDeviceName.value.trim(),
      scope: mcpScope.value,
      platform: 'cloud-frontend',
      client_version: 'gui',
    })
    ElMessage.success('MCP 令牌已生成')
  } catch (error) {
    ElMessage.error(获取API错误消息(error, 'MCP 令牌生成失败'))
  } finally {
    mcpTokenGenerating.value = false
  }
}

async function refreshAll() {
  loading.value = true
  try {
    await Promise.all([loadSettings(), loadLogs()])
  } finally {
    loading.value = false
  }
}

function handleLogPageChange(page: number) {
  logPage.value = page
  void loadLogs()
}

onMounted(refreshAll)
</script>

<template>
  <div class="ai-page">
    <PageSectionShell title="AI 管理" :icon="ChatDotRound" title-tag="h2">
      <template #title-extra>
        <ElTag :type="statusTagType" effect="dark">{{ form.enabled ? '已启用' : '已关闭' }}</ElTag>
      </template>
      <template #header-extra>
        <ElButton :loading="loading" @click="refreshAll">
          <RefreshRight />
          <span>刷新</span>
        </ElButton>
      </template>

      <ElAlert
        v-if="!form.has_secret"
        class="page-alert"
        type="warning"
        title="AI 密钥未配置"
        description="未配置密钥时，聊天接口和测试面板会返回配置错误。密钥只保存状态，不会回显明文。"
        show-icon
        :closable="false"
      />

      <div class="page-grid">
        <ElCard class="settings-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>运行配置</span>
              <ElButton type="primary" :loading="saving" @click="saveSettings">保存配置</ElButton>
            </div>
          </template>

          <ElForm label-position="top" :model="form" class="settings-form">
            <div class="form-row">
              <ElFormItem label="启用 AI 对话">
                <ElSwitch v-model="form.enabled" />
              </ElFormItem>
              <ElFormItem label="访问策略">
                <ElSelect v-model="form.access_policy">
                  <ElOption v-for="item in policyOptions" :key="item.value" :label="item.label" :value="item.value" />
                </ElSelect>
              </ElFormItem>
            </div>

            <div class="form-row">
              <ElFormItem label="供应商">
                <ElSelect v-model="form.provider" filterable allow-create>
                  <ElOption v-for="item in providerOptions" :key="item.value" :label="item.label" :value="item.value" />
                </ElSelect>
              </ElFormItem>
              <ElFormItem label="模型">
                <ElInput v-model="form.model" placeholder="gpt-4.1-mini" />
              </ElFormItem>
            </div>

            <ElFormItem label="Base URL">
              <ElInput v-model="form.base_url" placeholder="https://api.openai.com/v1" />
            </ElFormItem>

            <div class="form-row">
              <ElFormItem label="Max Tokens">
                <ElInputNumber v-model="form.max_tokens" :min="1" :max="128000" :step="128" />
              </ElFormItem>
              <ElFormItem label="超时秒数">
                <ElInputNumber v-model="form.timeout_seconds" :min="1" :max="300" :step="1" />
              </ElFormItem>
            </div>

            <ElFormItem label="系统提示词">
              <ElInput v-model="form.system_prompt" type="textarea" :rows="5" resize="vertical" />
            </ElFormItem>

            <div class="form-row form-row--three">
              <ElFormItem label="允许附件">
                <ElSwitch v-model="form.allow_attachments" disabled />
              </ElFormItem>
              <ElFormItem label="附件上限 MB">
                <ElInputNumber v-model="form.max_attachment_size_mb" :min="1" :max="200" />
              </ElFormItem>
              <ElFormItem label="每日次数">
                <ElInputNumber v-model="form.daily_limit_per_user" :min="0" :max="100000" />
              </ElFormItem>
            </div>
          </ElForm>
        </ElCard>

        <div class="side-column">
          <ElCard shadow="never">
            <template #header>
              <div class="card-header">
                <span>密钥状态</span>
                <ElTag :type="secretStatusType">{{ form.has_secret ? '已配置' : '未配置' }}</ElTag>
              </div>
            </template>
            <ElDescriptions :column="1" border>
              <ElDescriptionsItem label="更新时间">
                {{ formatDateTime(form.secret_updated_at) }}
              </ElDescriptionsItem>
              <ElDescriptionsItem label="配置更新时间">
                {{ formatDateTime(form.updated_at) }}
              </ElDescriptionsItem>
            </ElDescriptions>
            <ElSpace direction="vertical" alignment="stretch" class="secret-form">
              <ElInput v-model="secretInput" type="password" show-password placeholder="输入新密钥" />
              <ElButton type="primary" :loading="secretSaving" @click="saveSecret">更新密钥</ElButton>
            </ElSpace>
          </ElCard>

          <ElCard shadow="never">
            <template #header>
              <div class="card-header">
                <span>测试面板</span>
                <ElTag v-if="testDuration !== null" type="success">{{ testDuration }} ms</ElTag>
              </div>
            </template>
            <ElSpace direction="vertical" alignment="stretch" class="test-panel">
              <ElInput v-model="testMessage" type="textarea" :rows="4" resize="vertical" />
              <ElButton type="primary" :loading="testing" @click="runTest">发送测试</ElButton>
              <div v-if="testResult" class="test-result">{{ testResult }}</div>
            </ElSpace>
          </ElCard>

          <ElCard shadow="never">
            <template #header>
              <div class="card-header">
                <span>MCP 令牌</span>
                <ElTag :type="mcpScope === 'mcp_full' ? 'warning' : 'info'">
                  {{ mcpScope === 'mcp_full' ? '可读写' : '只读' }}
                </ElTag>
              </div>
            </template>
            <ElSpace direction="vertical" alignment="stretch" class="mcp-panel">
              <ElForm label-position="top">
                <ElFormItem label="设备名称">
                  <ElInput v-model="mcpDeviceName" maxlength="100" />
                </ElFormItem>
                <ElFormItem label="权限范围">
                  <ElSelect v-model="mcpScope">
                    <ElOption label="只读" value="mcp_readonly" />
                    <ElOption label="读写" value="mcp_full" />
                  </ElSelect>
                </ElFormItem>
                <ElFormItem label="CC Switch 导入目标">
                  <ElSelect v-model="mcpImportApps" multiple collapse-tags collapse-tags-tooltip>
                    <ElOption
                      v-for="item in mcpImportAppOptions"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </ElSelect>
                </ElFormItem>
              </ElForm>
              <ElButton type="primary" :loading="mcpTokenGenerating" @click="generateMCPToken">
                生成令牌
              </ElButton>
              <div class="mcp-field">
                <div class="mcp-field__label">连接地址</div>
                <div class="mcp-field__value">{{ mcpEndpoint }}</div>
                <ElButton plain size="small" @click="copyText(mcpEndpoint, '连接地址已复制')">复制地址</ElButton>
              </div>
              <template v-if="mcpTokenResult">
                <ElAlert
                  type="warning"
                  title="令牌只会在本次生成后显示"
                  :closable="false"
                  show-icon
                />
                <div class="mcp-field">
                  <div class="mcp-field__label">Bearer Token</div>
                  <ElInput :model-value="mcpTokenResult.token" type="textarea" :rows="4" readonly />
                  <ElButton plain size="small" @click="copyText(mcpTokenResult.token, 'MCP 令牌已复制')">
                    复制令牌
                  </ElButton>
                </div>
                <div class="mcp-field">
                  <div class="mcp-field__label">客户端配置</div>
                  <ElInput :model-value="mcpClientConfig" type="textarea" :rows="8" readonly />
                  <div class="mcp-actions">
                    <ElButton plain size="small" @click="copyText(mcpClientConfig, '客户端配置已复制')">
                      复制配置
                    </ElButton>
                    <ElButton type="primary" plain size="small" :disabled="!mcpImportApps.length" @click="importToCCSwitch">
                      导入 CC Switch
                    </ElButton>
                    <ElButton
                      plain
                      size="small"
                      :disabled="!mcpImportApps.length"
                      @click="copyText(mcpCCSwitchDeepLink, 'CC Switch 导入链接已复制')"
                    >
                      复制导入链接
                    </ElButton>
                  </div>
                  <div class="mcp-field__hint">
                    如果 CC Switch 中已存在 personal-system-cloud，深链只会合并应用开关；需要更新令牌时请先删除旧项或手动编辑。
                  </div>
                </div>
                <ElDescriptions :column="1" border>
                  <ElDescriptionsItem label="过期时间">
                    {{ formatDateTime(mcpTokenResult.expires_at) }}
                  </ElDescriptionsItem>
                  <ElDescriptionsItem label="会话 ID">
                    {{ mcpTokenResult.session.id }}
                  </ElDescriptionsItem>
                </ElDescriptions>
              </template>
            </ElSpace>
          </ElCard>
        </div>
      </div>

      <ElCard class="logs-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>调用日志</span>
            <ElButton :loading="logsLoading" @click="loadLogs">刷新日志</ElButton>
          </div>
        </template>
        <ElTable v-loading="logsLoading" :data="logs" row-key="id">
          <ElTableColumn label="时间" min-width="180">
            <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
          </ElTableColumn>
          <ElTableColumn prop="provider" label="供应商" min-width="130" />
          <ElTableColumn prop="model" label="模型" min-width="160" />
          <ElTableColumn label="状态" width="100">
            <template #default="{ row }">
              <ElTag :type="statusType(row.status)">{{ row.status }}</ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn prop="duration_ms" label="耗时 ms" width="110" />
          <ElTableColumn prop="message_count" label="消息数" width="90" />
          <ElTableColumn prop="total_tokens" label="Tokens" width="110" />
          <ElTableColumn prop="error_message" label="错误摘要" min-width="220" show-overflow-tooltip />
        </ElTable>
        <div class="pagination-row">
          <ElPagination
            layout="prev, pager, next, total"
            :total="logTotal"
            :page-size="logPageSize"
            :current-page="logPage"
            @current-change="handleLogPageChange"
          />
        </div>
      </ElCard>
    </PageSectionShell>
  </div>
</template>

<style scoped>
@import '@personal-system/ui/styles/media.css';

.ai-page {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.98));
}

.page-alert {
  margin-bottom: 16px;
}

.page-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
  align-items: start;
}

.side-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-weight: 600;
}

.settings-form {
  max-width: 100%;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.form-row--three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.secret-form,
.test-panel,
.mcp-panel {
  width: 100%;
  margin-top: 16px;
}

.mcp-field {
  display: grid;
  gap: 8px;
}

.mcp-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mcp-field__label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.mcp-field__hint {
  font-size: 12px;
  line-height: 1.6;
  color: var(--el-text-color-secondary);
}

.mcp-field__value {
  overflow-wrap: anywhere;
  padding: 10px 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  font-size: 13px;
}

.test-result {
  padding: 12px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
  line-height: 1.7;
  white-space: pre-wrap;
}

.logs-card {
  margin-top: 16px;
}

.pagination-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

:deep(.el-input-number) {
  width: 100%;
}

@media (max-width: 1180px) {
  .page-grid {
    grid-template-columns: 1fr;
  }
}

@media (--mobile-viewport) {
  .ai-page {
    padding: 16px;
  }

  .form-row,
  .form-row--three {
    grid-template-columns: 1fr;
  }
}
</style>
