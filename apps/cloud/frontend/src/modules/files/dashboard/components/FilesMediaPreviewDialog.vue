<script setup lang="ts">
import { ElButton, ElSpace, ElText } from 'element-plus'
import { BaseDialog } from '@personal-system/ui'
import type { 文件展示项 } from '../../core/shared'
import {
  获取可预览文件链接,
  格式化大小,
  是否内容图片,
  是否图片,
  是否视频,
} from '../../core/resource'

defineProps<{
  visible: boolean
  当前预览媒体: 文件展示项 | null
  当前预览媒体索引: number
  可预览媒体总数: number
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  switch: [offset: number]
  'open-file': [url: string]
  'copy-image-link': [url: string]
}>()
</script>

<template>
  <BaseDialog
    :model-value="visible"
    title="媒体预览"
    width="min(980px, 94vw)"
    top="4vh"
    class="image-preview-dialog"
    @update:model-value="emit('update:visible', $event)"
  >
    <template v-if="当前预览媒体">
      <div class="image-preview">
        <img
          v-if="是否图片(当前预览媒体)"
          :src="获取可预览文件链接(当前预览媒体.url)"
          :alt="当前预览媒体.original_name"
        >
        <video
          v-else-if="是否视频(当前预览媒体)"
          :src="获取可预览文件链接(当前预览媒体.url)"
          controls
          preload="metadata"
        />
      </div>
      <div class="image-preview__footer">
        <div class="image-preview__meta">
          <strong>{{ 当前预览媒体.original_name }}</strong>
          <ElText type="info">
            {{ 当前预览媒体索引 + 1 }} / {{ 可预览媒体总数 }} · {{ 格式化大小(当前预览媒体.size) }}
          </ElText>
        </div>
        <ElSpace wrap>
          <ElButton :disabled="当前预览媒体索引 <= 0" @click="emit('switch', -1)">上一项</ElButton>
          <ElButton :disabled="当前预览媒体索引 >= 可预览媒体总数 - 1" @click="emit('switch', 1)">下一项</ElButton>
          <ElButton @click="emit('open-file', 当前预览媒体.url)">新窗口打开</ElButton>
          <ElButton
            v-if="是否内容图片(当前预览媒体)"
            @click="emit('copy-image-link', 当前预览媒体.url)"
          >
            复制图片链接
          </ElButton>
        </ElSpace>
      </div>
    </template>
  </BaseDialog>
</template>

<style scoped>
.image-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  border-radius: 16px;
  background:
    radial-gradient(circle at top, rgb(var(--el-color-primary-rgb) / 0.12), transparent 48%),
    linear-gradient(135deg, rgba(15, 23, 42, 0.05), rgba(15, 23, 42, 0.12));
  overflow: hidden;
}

.image-preview img {
  max-width: 100%;
  max-height: 72vh;
  object-fit: contain;
  display: block;
}

.image-preview video {
  width: 100%;
  max-height: 72vh;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.92);
}

.image-preview__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 14px;
  flex-wrap: wrap;
}

.image-preview__meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}
</style>
