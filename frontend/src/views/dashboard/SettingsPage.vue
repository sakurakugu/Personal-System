<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElCard, ElIcon, ElMessage, ElSpace, ElSwitch, ElTag } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import api from '../../utils/api'

const loading = ref(true)
const saving = ref(false)
const commentsEnabled = ref(true)
const commentsStealth = ref(false)

async function fetchSettings() {
  const { data } = await api.get('/admin/settings')
  commentsEnabled.value = data.comments_enabled
  commentsStealth.value = data.comments_stealth
}

async function saveSettings(payload: { comments_enabled?: boolean; comments_stealth?: boolean }) {
  saving.value = true
  try {
    const { data } = await api.patch('/admin/settings', payload)
    commentsEnabled.value = data.comments_enabled
    commentsStealth.value = data.comments_stealth
    if (data.comments_stealth) {
      ElMessage.success('评论区痕迹已完全隐藏')
      return
    }
    ElMessage.success(data.comments_enabled ? '评论功能已开启' : '评论功能已关闭')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
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

onMounted(async () => {
  try {
    await fetchSettings()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <h2 style="display: inline-flex; align-items: center; gap: 8px; margin-bottom: 24px">
      <ElIcon><Setting /></ElIcon>
      <span>系统设置</span>
    </h2>
    <ElCard header="评论页面开关">
      <ElSpace direction="vertical" :size="16" fill>
        <ElSpace alignment="center" justify="space-between">
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
        </ElSpace>
        <ElSpace alignment="center" justify="space-between">
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
        </ElSpace>
      </ElSpace>
    </ElCard>
  </div>
</template>
