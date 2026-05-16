<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElSpace, ElSwitch, ElTag } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import { SettingsItem, SettingsPageShell, SettingsSectionCard } from '@personal-system/ui'
import { 获取管理设置, 更新管理设置 } from '../../api'
import { getApiErrorMessage } from '../../../../shared/api'

const loading = ref(true)
const saving = ref(false)
const registerEnabled = ref(true)
const commentsEnabled = ref(true)
const commentsHidden = ref(false)

async function fetchSettings() {
  const data = await 获取管理设置()
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
    const data = await 更新管理设置(payload)
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
  <SettingsPageShell title="系统设置" :icon="Setting">
    <SettingsSectionCard header="用户注册开关">
      <SettingsItem>
        <template #title>
          <span>允许新用户注册</span>
        </template>
        <template #actions>
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
        </template>
        <template #tip>
          关闭后前端将隐藏注册入口，且无法提交注册请求
        </template>
      </SettingsItem>
    </SettingsSectionCard>

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
        <template #tip>
          关闭后前台仍保留评论卡片，但会显示“评论区已关闭”
        </template>
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
        <template #tip>
          隐藏后前台不渲染评论区卡片，优先级高于“关闭评论区”
        </template>
      </SettingsItem>
    </SettingsSectionCard>
  </SettingsPageShell>
</template>
