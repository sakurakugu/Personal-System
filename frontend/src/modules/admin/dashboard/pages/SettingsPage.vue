<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElCard, ElIcon, ElMessage, ElSpace, ElSwitch, ElTag } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import { fetchAdminSettings, updateAdminSettings } from '../../api'
import { getApiErrorMessage } from '../../../../shared/api'

const loading = ref(true)
const saving = ref(false)
const registerEnabled = ref(true)
const commentsEnabled = ref(true)
const commentsHidden = ref(false)

async function fetchSettings() {
  const data = await fetchAdminSettings()
  registerEnabled.value = data.register_enabled !== false
  commentsEnabled.value = data.comments_enabled !== false
  commentsHidden.value = data.comments_hidden === true
}

async function saveSettings(payload: {
  register_enabled?: boolean
  comments_enabled?: boolean
  comments_hidden?: boolean
}) {
  saving.value = true
  try {
    const data = await updateAdminSettings(payload)
    registerEnabled.value = data.register_enabled !== false
    commentsEnabled.value = data.comments_enabled !== false
    commentsHidden.value = data.comments_hidden === true
    ElMessage.success('设置已保存')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '保存失败'))
  } finally {
    saving.value = false
  }
}

function saveRegisterEnabled(value: string | number | boolean) {
  return saveSettings({ register_enabled: Boolean(value) })
}

function saveCommentsEnabled(value: string | number | boolean) {
  return saveSettings({ comments_enabled: Boolean(value) })
}

function saveCommentsHidden(value: string | number | boolean) {
  return saveSettings({ comments_hidden: Boolean(value) })
}

onMounted(async () => {
  try {
    await fetchSettings()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page-container">
    <h2 style="display: inline-flex; align-items: center; gap: 8px; margin-bottom: 24px">
      <ElIcon><Setting /></ElIcon>
      <span>系统设置</span>
    </h2>

    <ElCard header="用户注册开关" :body-style="{ padding: '16px 20px' }">
      <div class="settings-list">
        <div class="setting-item-vertical">
          <div class="setting-item-header">
            <span>允许新用户注册</span>
            <ElSpace alignment="center">
              <ElTag :type="registerEnabled ? 'success' : 'danger'">
                {{ registerEnabled ? '已开启' : '已关闭' }}
              </ElTag>
              <ElSwitch
                :model-value="registerEnabled"
                :loading="saving || loading"
                @update:model-value="saveRegisterEnabled"
              />
            </ElSpace>
          </div>
          <div class="setting-tip">
            关闭后前端将隐藏注册入口，且无法提交注册请求
          </div>
        </div>
      </div>
    </ElCard>

    <ElCard header="评论区开关" :body-style="{ padding: '16px 20px' }" class="settings-card">
      <div class="settings-list">
        <div class="setting-item-vertical">
          <div class="setting-item-header">
            <span>关闭评论区</span>
            <ElSpace alignment="center">
              <ElTag :type="commentsEnabled ? 'success' : 'warning'">
                {{ commentsEnabled ? '已开启评论' : '前台显示已关闭' }}
              </ElTag>
              <ElSwitch
                :model-value="commentsEnabled"
                :loading="saving || loading"
                @update:model-value="saveCommentsEnabled"
              />
            </ElSpace>
          </div>
          <div class="setting-tip">
            关闭后前台仍保留评论卡片，但会显示“评论区已关闭”
          </div>
        </div>

        <div class="setting-item-vertical">
          <div class="setting-item-header">
            <span>隐藏评论区</span>
            <ElSpace alignment="center">
              <ElTag :type="commentsHidden ? 'info' : 'success'">
                {{ commentsHidden ? '前台不显示卡片' : '前台显示卡片' }}
              </ElTag>
              <ElSwitch
                :model-value="commentsHidden"
                :loading="saving || loading"
                @update:model-value="saveCommentsHidden"
              />
            </ElSpace>
          </div>
          <div class="setting-tip">
            隐藏后前台不渲染评论区卡片，优先级高于“关闭评论区”
          </div>
        </div>
      </div>
    </ElCard>
  </div>
</template>

<style scoped>
.page-container {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

.page-container :deep(.el-card__header) {
  padding: 12px 20px;
}

.settings-card {
  margin-top: 16px;
}

.settings-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.setting-item-vertical {
  display: flex;
  flex-direction: column;
}

.setting-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.setting-tip {
  font-size: 12px;
  color: #888;
  margin-top: 4px;
}
</style>
