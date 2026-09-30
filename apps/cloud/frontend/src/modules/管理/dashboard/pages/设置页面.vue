<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElAlert, ElMessage, ElSwitch } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import { SettingsItem, SettingsPageLayout, SettingsSectionCard } from '@personal-system/ui'
import { 使用设置存储 } from '@personal-system/domain/system'
import { 获取管理设置, 更新管理设置 } from '../../api'
import { 获取API错误消息 } from '../../../../shared/api'

const settingsStore = 使用设置存储()
const loading = ref(true)
const loadError = ref(false)
const saving = ref(false)
const commentsEnabled = ref(true)
const commentsHidden = ref(false)
const toolsEnabled = ref(true)
const aiChatEnabled = ref(false)
async function fetchSettings() {
  const data = await 获取管理设置()
  commentsEnabled.value = data.comments_enabled !== false
  commentsHidden.value = data.comments_hidden === true
  toolsEnabled.value = data.tools_enabled !== false
  aiChatEnabled.value = data.ai_chat_enabled !== false
}

async function saveSettings(payload: {
  comments_enabled?: boolean
  comments_hidden?: boolean
  tools_enabled?: boolean
  ai_chat_enabled?: boolean
}) {
  saving.value = true
  try {
    const data = await 更新管理设置(payload)
    commentsEnabled.value = data.comments_enabled !== false
    commentsHidden.value = data.comments_hidden === true
    toolsEnabled.value = data.tools_enabled !== false
    aiChatEnabled.value = data.ai_chat_enabled !== false
    // 管理页保存后同步公开设置存储，避免当前应用继续使用旧值。
    await settingsStore.fetchPublicSettings()
    ElMessage.success('设置已保存')
  } catch (error) {
    console.error('系统设置：保存全站配置失败', error)
    ElMessage.error(获取API错误消息(error, '保存失败'))
  } finally {
    saving.value = false
  }
}

function saveCommentsEnabled(value: string | number | boolean) {
  return saveSettings({ comments_enabled: Boolean(value) })
}

function saveCommentsHidden(value: string | number | boolean) {
  return saveSettings({ comments_hidden: Boolean(value) })
}

function saveToolsEnabled(value: string | number | boolean) {
  return saveSettings({ tools_enabled: Boolean(value) })
}

function saveAiChatEnabled(value: string | number | boolean) {
  return saveSettings({ ai_chat_enabled: Boolean(value) })
}

onMounted(async () => {
  try {
    await fetchSettings()
  } catch (error) {
    loadError.value = true
    console.error('系统设置：加载全站配置失败', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <SettingsPageLayout title="系统设置" :icon="Setting">
    <ElAlert
      v-if="loadError"
      title="全站配置加载失败，请刷新页面重试"
      type="error"
      :closable="false"
      show-icon
    />
    <template v-else>
      <SettingsSectionCard header="评论区开关">
        <SettingsItem>
          <template #title>
            <span>关闭评论区</span>
          </template>
          <template #actions>
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
          </template>
          <template #tip> 关闭后前台仍保留评论卡片，但会显示“评论区已关闭” </template>
        </SettingsItem>

        <SettingsItem>
          <template #title>
            <span>隐藏评论区</span>
          </template>
          <template #actions>
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
          </template>
          <template #tip> 隐藏后前台不渲染评论区卡片，优先级高于“关闭评论区” </template>
        </SettingsItem>
      </SettingsSectionCard>
      <SettingsSectionCard header="工具页面开关">
        <SettingsItem>
          <template #title><span>显示工具页面</span></template>
          <template #actions>
            <ElSpace alignment="center">
              <ElTag :type="toolsEnabled ? 'success' : 'warning'">{{
                toolsEnabled ? '已显示' : '已隐藏'
              }}</ElTag>
              <ElSwitch
                :model-value="toolsEnabled"
                :loading="saving || loading"
                @update:model-value="saveToolsEnabled"
              />
            </ElSpace>
          </template>
          <template #tip>关闭后前台导航和工具路由均不可见。</template>
        </SettingsItem>
      </SettingsSectionCard>
      <SettingsSectionCard header="AI 对话开关">
        <SettingsItem>
          <template #title><span>显示 AI 对话挂件</span></template>
          <template #actions>
            <ElSpace alignment="center">
              <ElTag :type="aiChatEnabled ? 'success' : 'warning'">{{
                aiChatEnabled ? '已显示' : '已隐藏'
              }}</ElTag>
              <ElSwitch
                :model-value="aiChatEnabled"
                :loading="saving || loading"
                @update:model-value="saveAiChatEnabled"
              />
            </ElSpace>
          </template>
          <template #tip
            >仅控制前台是否渲染 AI 对话挂件，不影响后台「AI 管理」中的启用状态与调用配置。</template
          >
        </SettingsItem>
      </SettingsSectionCard>
    </template>
  </SettingsPageLayout>
</template>
