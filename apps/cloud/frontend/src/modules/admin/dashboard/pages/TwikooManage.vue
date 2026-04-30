<script setup lang="ts">
import { ArrowDown, ArrowUp, ChatDotRound, Key } from '@element-plus/icons-vue'
import { ElAlert, ElButton, ElIcon, ElInput, ElMessage, ElSpace, ElSwitch } from 'element-plus'
import { computed, onMounted, ref, watch } from 'vue'
import { getApiErrorMessage } from '../../../../shared/api'
import { useAuthStore } from '../../../auth/store'
import { fetchTwikooPasswordState, resetTwikooPassword } from '../../api'
import type { TwikooPasswordState } from '../../types'
import TwikooPanel from '../../../blog/components/TwikooPanel.vue'

const 自动进入管理页存储键 = 'twikoo-manage-auto-open-admin'
const 密码备忘展开存储键 = 'twikoo-manage-password-expanded'
const auth = useAuthStore()
const isSuperAdmin = computed(() => auth.isSuperAdmin)

function 读取自动进入设置() {
  if (typeof window === 'undefined') {
    return true
  }
  const 已保存值 = window.localStorage.getItem(自动进入管理页存储键)
  if (已保存值 === null) {
    return true
  }
  return 已保存值 === 'true'
}

function 读取密码备忘展开设置() {
  if (typeof window === 'undefined') {
    return false
  }
  const 已保存值 = window.localStorage.getItem(密码备忘展开存储键)
  if (已保存值 === null) {
    return false
  }
  return 已保存值 === 'true'
}

const autoOpenAdmin = ref(读取自动进入设置())
const twikooPasswordState = ref<TwikooPasswordState | null>(null)
const twikooPasswordLoading = ref(false)
const twikooPasswordInput = ref('')
const panelRenderKey = ref(0)
const twikooPasswordExpanded = ref(读取密码备忘展开设置())

watch(autoOpenAdmin, (value) => {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.setItem(自动进入管理页存储键, String(value))
})

watch(twikooPasswordExpanded, (value) => {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.setItem(密码备忘展开存储键, String(value))
})

const 最近重置时间文本 = computed(() => {
  const 时间值 = twikooPasswordState.value?.last_reset_at
  if (!时间值) {
    return '暂无记录'
  }
  return new Date(时间值).toLocaleString('zh-CN', { hour12: false })
})

async function 读取Twikoo密码状态() {
  if (!isSuperAdmin.value) {
    twikooPasswordState.value = null
    return
  }
  twikooPasswordLoading.value = true
  try {
    twikooPasswordState.value = await fetchTwikooPasswordState()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '读取 Twikoo 密码状态失败'))
  } finally {
    twikooPasswordLoading.value = false
  }
}

async function 重置Twikoo密码() {
  const 新密码 = twikooPasswordInput.value.trim()
  if (新密码.length < 6) {
    ElMessage.warning('Twikoo 管理密码至少需要 6 位')
    return
  }
  twikooPasswordLoading.value = true
  try {
    twikooPasswordState.value = await resetTwikooPassword(新密码)
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('twikoo-access-token')
    }
    panelRenderKey.value += 1
    twikooPasswordInput.value = ''
    ElMessage.success('Twikoo 管理密码已重置，旧登录态已清理')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '重置 Twikoo 管理密码失败'))
  } finally {
    twikooPasswordLoading.value = false
  }
}

async function 复制最近密码备忘() {
  const 密码 = twikooPasswordState.value?.last_reset_password
  if (!密码) {
    ElMessage.warning('暂无可复制的密码备忘')
    return
  }
  try {
    await navigator.clipboard.writeText(密码)
    ElMessage.success('已复制最近一次密码备忘')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

onMounted(() => {
  if (isSuperAdmin.value) {
    void 读取Twikoo密码状态()
  }
})

watch(isSuperAdmin, (value) => {
  if (value) {
    void 读取Twikoo密码状态()
    return
  }
  twikooPasswordState.value = null
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">
        <span class="page-title-main">
          <ElIcon><ChatDotRound /></ElIcon>
          <span>评论管理</span>
        </span>
      </h2>

      <ElSpace alignment="center" class="page-actions">
        <div class="auto-open-switch">
          <span class="auto-open-switch__label">自动进入管理页</span>
          <ElSwitch v-model="autoOpenAdmin" />
        </div>
      </ElSpace>
    </div>

    <section v-if="isSuperAdmin" class="twikoo-password-card">
      <div class="twikoo-password-card__header">
        <div class="twikoo-password-card__title">
          <ElIcon><Key /></ElIcon>
          <span>Twikoo 管理密码备忘</span>
        </div>
        <div class="twikoo-password-card__header-actions">
          <span v-if="twikooPasswordExpanded" class="twikoo-password-card__meta">最近重置：{{ 最近重置时间文本 }}</span>
          <button
            type="button"
            class="twikoo-password-card__toggle"
            :aria-label="twikooPasswordExpanded ? '收起 Twikoo 管理密码备忘' : '展开 Twikoo 管理密码备忘'"
            :aria-expanded="twikooPasswordExpanded"
            @click="twikooPasswordExpanded = !twikooPasswordExpanded"
          >
            <ElIcon>
              <ArrowUp v-if="twikooPasswordExpanded" />
              <ArrowDown v-else />
            </ElIcon>
          </button>
        </div>
      </div>

      <template v-if="twikooPasswordExpanded">
        <ElAlert
          :title="twikooPasswordState?.detail || '正在读取 Twikoo 密码运维状态...'"
          type="info"
          :closable="false"
          show-icon
        />

        <p class="twikoo-password-card__tip">
          这里只保存最近一次通过本站重置的密码备忘；如果你后来在 Twikoo 面板里手动改过密码，这里的值可能已经过期。
        </p>

        <div class="twikoo-password-grid">
          <div class="twikoo-password-field">
            <label class="twikoo-password-field__label" for="twikoo-password-reset">新的 Twikoo 管理密码</label>
            <ElInput
              id="twikoo-password-reset"
              v-model="twikooPasswordInput"
              type="password"
              show-password
              placeholder="输入新的 Twikoo 管理密码，至少 6 位"
              :disabled="twikooPasswordLoading || !twikooPasswordState?.available"
              @keyup.enter="重置Twikoo密码"
            />
          </div>

          <div class="twikoo-password-field">
            <label class="twikoo-password-field__label" for="twikoo-password-last">最近一次本站重置的密码备忘</label>
            <ElInput
              id="twikoo-password-last"
              :model-value="twikooPasswordState?.last_reset_password || ''"
              type="password"
              show-password
              readonly
              placeholder="暂无密码备忘"
            />
          </div>
        </div>

        <div class="twikoo-password-actions">
          <ElButton
            type="primary"
            :loading="twikooPasswordLoading"
            :disabled="!twikooPasswordState?.available"
            @click="重置Twikoo密码"
          >
            重置并保存备忘
          </ElButton>
          <ElButton plain :disabled="!twikooPasswordState?.last_reset_password" @click="复制最近密码备忘">
            复制最近密码备忘
          </ElButton>
        </div>
      </template>
    </section>

    <TwikooPanel
      :key="panelRenderKey"
      class="page-panel"
      path="/dashboard/twikoo"
      title="评论面板"
      empty-description="后台评论面板尚未配置 Twikoo 服务地址"
      :fill-height="true"
      :show-panel-header="false"
      :force-admin-entry="true"
      :auto-open-admin="autoOpenAdmin"
    />
  </div>
</template>

<style scoped>
.page-container {
  height: 100%;
  overflow: hidden;
  padding: 24px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-panel {
  flex: 1;
  min-height: 0;
}

.twikoo-password-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px 20px;
  border-radius: var(--radius-large);
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  box-shadow: 0 14px 34px rgba(148, 163, 184, 0.12);
  background-color: rgba(255, 255, 255, var(--overlay-card-opacity)) !important;
}

.dark .twikoo-password-card {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 14px 32px rgba(2, 6, 23, 0.28);
  background-color: rgba(15, 23, 42, var(--overlay-card-opacity)) !important;
}

.twikoo-password-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.twikoo-password-card__header-actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.twikoo-password-card__title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
}

.twikoo-password-card__title :deep(.el-icon) {
  color: var(--el-color-primary);
}

.twikoo-password-card__meta {
  font-size: 13px;
  color: var(--text-secondary);
}

.twikoo-password-card__toggle {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(148, 163, 184, 0.12);
  color: var(--text-secondary);
  cursor: pointer;
  transition:
    background-color 0.2s ease,
    color 0.2s ease,
    transform 0.2s ease;
}

.twikoo-password-card__toggle:hover {
  background: rgba(59, 130, 246, 0.14);
  color: var(--el-color-primary);
}

.twikoo-password-card__toggle:focus-visible {
  outline: 2px solid rgba(59, 130, 246, 0.35);
  outline-offset: 2px;
}

.twikoo-password-card__toggle:active {
  transform: scale(0.96);
}

.twikoo-password-card__tip {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.twikoo-password-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.twikoo-password-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.twikoo-password-field__label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.twikoo-password-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex: 0 0 auto;
}

.page-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.3;
}

.page-title-main {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.page-title-main :deep(.el-icon) {
  color: var(--el-color-primary);
}

.page-actions {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.auto-open-switch {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.auto-open-switch__label {
  font-size: 14px;
  color: var(--text-secondary);
  white-space: nowrap;
}

@media (max-width: 768px) {
  .page-container {
    padding: 16px;
  }

  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .twikoo-password-card {
    padding: 16px;
  }

  .twikoo-password-card__header {
    align-items: flex-start;
    gap: 10px;
  }

  .twikoo-password-card__header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .twikoo-password-grid {
    grid-template-columns: 1fr;
  }

  .page-actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
