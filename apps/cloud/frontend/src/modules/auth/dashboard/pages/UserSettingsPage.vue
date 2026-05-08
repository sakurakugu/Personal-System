<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElCard, ElIcon, ElMessage, ElSkeleton, ElSpace, ElSwitch, ElTag } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import { useAuthStore } from '@personal-system/domain/auth'
import { getApiErrorMessage } from '../../../../shared/api'

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
    ElMessage.error(getApiErrorMessage(error, '保存失败'))
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
  <div class="page-container">
    <h2 style="display: inline-flex; align-items: center; gap: 8px; margin-bottom: 24px">
      <ElIcon><Setting /></ElIcon>
      <span>用户设置</span>
    </h2>

    <ElSkeleton :loading="loading" animated>
      <ElCard header="首页内容展示" :body-style="{ padding: '16px 20px' }">
        <div class="settings-list">
          <div class="setting-item-vertical">
            <div class="setting-item-header">
              <span>首页显示自己的私有文章</span>
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
            </div>
            <div class="setting-description">
              开启后，首页动态流可以看到你自己的私有文章；关闭后依旧只显示公开内容。
            </div>
          </div>
        </div>
      </ElCard>
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

.page-container :deep(.el-card__header) {
  padding: 12px 20px;
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
  gap: 12px;
  flex-wrap: wrap;
}

.setting-description {
  margin-top: 4px;
  font-size: 12px;
  color: #888;
}

@media (max-width: 767px) {
  .setting-item-header {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>

