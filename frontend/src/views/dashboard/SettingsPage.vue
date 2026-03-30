<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElCard, ElIcon, ElMessage, ElOption, ElSelect, ElSpace, ElSwitch, ElTag } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import { fetchAdminSettings, updateAdminSettings } from '../../features/admin/api'
import { getApiErrorMessage } from '../../utils/api'

const loading = ref(true)
const saving = ref(false)
const savingRole = ref(false)
const savingRegister = ref(false)
const commentsEnabled = ref(true)
const commentsStealth = ref(false)
const commentsMinRole = ref('guest')
const registerEnabled = ref(true)

const roleOptions = [
  { label: '所有人（包括游客）', value: 'guest' },
  { label: '仅登录用户', value: 'user' },
  { label: '仅管理员', value: 'admin' },
  { label: '仅超级管理员', value: 'super_admin' },
]

async function fetchSettings() {
  const data = await fetchAdminSettings()
  commentsEnabled.value = data.comments_enabled
  commentsStealth.value = data.comments_stealth
  commentsMinRole.value = data.comments_min_role || 'guest'
  registerEnabled.value = data.register_enabled !== false
}

async function saveSettings(payload: { comments_enabled?: boolean; comments_stealth?: boolean; comments_min_role?: string; register_enabled?: boolean }) {
  saving.value = true
  try {
    const data = await updateAdminSettings(payload)
    commentsEnabled.value = data.comments_enabled
    commentsStealth.value = data.comments_stealth
    commentsMinRole.value = data.comments_min_role || 'guest'
    registerEnabled.value = data.register_enabled !== false
    ElMessage.success('设置已保存')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '保存失败'))
  } finally {
    saving.value = false
  }
}

async function saveCommentsEnabled(value: string | number | boolean) {
  await saveSettings({ comments_enabled: Boolean(value) })
}

async function saveCommentsStealth(value: string | number | boolean) {
  await saveSettings({ comments_stealth: Boolean(value) })
}

async function saveCommentsMinRole(value: string) {
  savingRole.value = true
  try {
    await saveSettings({ comments_min_role: value })
  } finally {
    savingRole.value = false
  }
}

async function saveRegisterEnabled(value: string | number | boolean) {
  savingRegister.value = true
  try {
    await saveSettings({ register_enabled: Boolean(value) })
  } finally {
    savingRegister.value = false
  }
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
    
    <!-- 评论设置 -->
    <ElCard header="评论设置" style="margin-bottom: 16px" :body-style="{ padding: '16px 20px' }">
      <div class="settings-list">
        <div class="setting-item">
          <span>前端评论页面状态</span>
          <ElSpace alignment="center">
            <ElTag :type="commentsEnabled ? 'success' : 'danger'">
              {{ commentsEnabled ? '已开启' : '已关闭' }}
            </ElTag>
            <ElSwitch
              :model-value="commentsEnabled"
              :loading="saving || loading"
              @update:model-value="saveCommentsEnabled"
            />
          </ElSpace>
        </div>
        <div class="setting-item">
          <span>隐藏评论区存在痕迹</span>
          <ElSpace alignment="center">
            <ElTag :type="commentsStealth ? 'warning' : 'info'">
              {{ commentsStealth ? '已隐藏痕迹' : '正常显示关闭提示' }}
            </ElTag>
            <ElSwitch
              :model-value="commentsStealth"
              :loading="saving || loading"
              @update:model-value="saveCommentsStealth"
            />
          </ElSpace>
        </div>
        <div class="setting-item-vertical">
          <div class="setting-item-header">
            <span>允许查看评论的用户等级</span>
            <ElSelect
              v-model="commentsMinRole"
              :loading="savingRole || loading"
              style="width: 180px"
              @change="saveCommentsMinRole"
            >
              <ElOption
                v-for="opt in roleOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </ElSelect>
          </div>
          <div style="font-size: 12px; color: #888; margin-top: 4px">
            低于该等级的用户将无法看到评论区
          </div>
        </div>
      </div>
    </ElCard>

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
                :loading="savingRegister || loading"
                @update:model-value="saveRegisterEnabled"
              />
            </ElSpace>
          </div>
          <div style="font-size: 12px; color: #888; margin-top: 4px">
            关闭后前端将隐藏注册入口，且无法提交注册请求
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

.settings-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
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
</style>
