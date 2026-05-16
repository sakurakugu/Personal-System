<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElSkeleton, ElSpace, ElSwitch, ElTag } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import { useAuthStore } from '@personal-system/domain/auth'
import { SettingsItem, SettingsPageShell, SettingsSectionCard } from '@personal-system/ui'
import { 获取API错误消息 } from '../../../../shared/api'

const auth = useAuthStore()
const loading = ref(true)
const savingHomePrivate = ref(false)
const showPrivateArticlesOnHome = ref(false)

function syncSettingsFromUser() {
  showPrivateArticlesOnHome.value = auth.user?.settings.show_private_articles_on_home ?? false
}

async function saveHomePrivateSetting(value: string | number | boolean) {
  const nextValue = Boolean(value)
  const previousValue = auth.user?.settings.show_private_articles_on_home ?? false
  showPrivateArticlesOnHome.value = nextValue
  savingHomePrivate.value = true
  try {
    await auth.updateProfile({ settings: { show_private_articles_on_home: nextValue } })
    ElMessage.success(nextValue ? '首页已允许显示私有文章' : '首页已关闭私有文章显示')
  } catch (error) {
    showPrivateArticlesOnHome.value = previousValue
    ElMessage.error(获取API错误消息(error, '保存失败'))
  } finally {
    savingHomePrivate.value = false
  }
}

onMounted(async () => {
  try {
    await auth.restoreUserIfNeeded()
    syncSettingsFromUser()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <SettingsPageShell title="用户设置" :icon="Setting">
    <ElSkeleton :loading="loading" animated>
      <SettingsSectionCard header="首页内容展示">
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
                :loading="savingHomePrivate || loading"
                @update:model-value="saveHomePrivateSetting"
              />
            </ElSpace>
          </template>
          <template #tip>
            开启后，首页动态流可以看到你自己的私有文章；关闭后依旧只显示公开内容。
          </template>
        </SettingsItem>
      </SettingsSectionCard>
    </ElSkeleton>
  </SettingsPageShell>
</template>

