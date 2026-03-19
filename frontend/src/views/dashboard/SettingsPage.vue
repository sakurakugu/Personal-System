<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NButton, NCard, NSpace, NSwitch, NTag, useMessage } from 'naive-ui'
import { ElIcon } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import api from '../../utils/api'

const message = useMessage()
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
      message.success('评论区痕迹已完全隐藏')
      return
    }
    message.success(data.comments_enabled ? '评论功能已开启' : '评论功能已关闭')
  } catch (e: any) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function saveCommentsEnabled(value: boolean) {
  await saveSettings({ comments_enabled: value })
}

async function saveCommentsStealth(value: boolean) {
  await saveSettings({ comments_stealth: value })
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
    <NCard title="评论页面开关">
      <NSpace vertical :size="16">
        <NSpace align="center" justify="space-between">
          <span>前端评论页面状态</span>
          <NSpace align="center">
            <NTag :type="commentsEnabled ? 'success' : 'error'">
              {{ commentsEnabled ? '已开启' : '已关闭' }}
            </NTag>
            <NSwitch
              :value="commentsEnabled"
              :loading="saving || loading"
              @update:value="saveCommentsEnabled"
            />
          </NSpace>
        </NSpace>
        <NSpace align="center" justify="space-between">
          <span>隐藏评论区存在痕迹</span>
          <NSpace align="center">
            <NTag :type="commentsStealth ? 'warning' : 'default'">
              {{ commentsStealth ? '已隐藏痕迹' : '正常显示关闭提示' }}
            </NTag>
            <NSwitch
              :value="commentsStealth"
              :loading="saving || loading"
              @update:value="saveCommentsStealth"
            />
          </NSpace>
        </NSpace>
      </NSpace>
    </NCard>
  </div>
</template>
