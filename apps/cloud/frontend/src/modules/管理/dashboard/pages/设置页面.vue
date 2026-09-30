<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElAlert, ElMessage, ElSkeleton, ElSpace, ElSwitch, ElTag } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import { SettingsItem, SettingsPageLayout, SettingsSectionCard } from '@personal-system/ui'
import { 使用设置存储 } from '@personal-system/domain/system'
import { 使用认证存储 } from '@personal-system/domain/auth'
import { 获取管理设置, 更新管理设置 } from '../../api'
import { 获取API错误消息 } from '../../../../shared/api'

const settingsStore = 使用设置存储()
const auth = 使用认证存储()
const loading = ref(true)
const loadError = ref(false)
const saving = ref(false)
const commentsEnabled = ref(true)
const commentsHidden = ref(false)
const toolsEnabled = ref(true)
const aiChatEnabled = ref(false)
const loadingHomePrivate = ref(true)
const homePrivateLoadError = ref(false)
const savingHomePrivate = ref(false)
const showPrivateArticlesOnHome = ref(false)

async function saveHomePrivateSetting(value: string | number | boolean) {
  const nextValue = Boolean(value)
  const previousValue = auth.user?.settings.show_private_articles_on_home ?? false
  showPrivateArticlesOnHome.value = nextValue
  savingHomePrivate.value = true
  try {
    await auth.更新个人资料({ settings: { show_private_articles_on_home: nextValue } })
    ElMessage.success(nextValue ? '首页已允许显示私有文章' : '首页已关闭私有文章显示')
  } catch (error) {
    showPrivateArticlesOnHome.value = previousValue
    console.error('系统设置：保存首页私有文章展示偏好失败', error)
    ElMessage.error(获取API错误消息(error, '保存失败'))
  } finally {
    savingHomePrivate.value = false
  }
}

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

onMounted(async () => {
  try {
    await auth.需要时恢复用户()
    if (!auth.user) {
      throw new Error('未能获取当前用户设置')
    }
    showPrivateArticlesOnHome.value = auth.user.settings.show_private_articles_on_home ?? false
  } catch (error) {
    homePrivateLoadError.value = true
    console.error('系统设置：加载首页私有文章展示偏好失败', error)
  } finally {
    loadingHomePrivate.value = false
  }
})
</script>

<template>
  <SettingsPageLayout title="系统设置" :icon="Setting">
    <SettingsSectionCard header="首页内容展示">
      <ElAlert
        v-if="homePrivateLoadError"
        title="首页内容展示设置加载失败，请刷新页面重试"
        type="error"
        :closable="false"
        show-icon
      />
      <ElSkeleton v-else :loading="loadingHomePrivate" animated>
        <SettingsItem>
          <template #title>
            <span>首页显示自己的私有文章</span>
          </template>
          <template #actions>
            <ElSpace alignment="center">
              <ElTag :type="showPrivateArticlesOnHome ? 'warning' : 'info'">
                {{ showPrivateArticlesOnHome ? '已开启' : '已关闭' }}
              </ElTag>
              <ElSwitch
                :model-value="showPrivateArticlesOnHome"
                :loading="savingHomePrivate || loadingHomePrivate"
                @update:model-value="saveHomePrivateSetting"
              />
            </ElSpace>
          </template>
          <template #tip>
            开启后，首页动态流可以看到你自己的私有文章；关闭后依旧只显示公开内容。
          </template>
        </SettingsItem>
      </ElSkeleton>
    </SettingsSectionCard>
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
