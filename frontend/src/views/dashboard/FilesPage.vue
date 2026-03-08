<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NCard, NButton, NUpload, NSpace, NEmpty, NSpin, NPopconfirm, NText, useMessage, type UploadFileInfo } from 'naive-ui'
import api from '../../utils/api'

const message = useMessage()

interface FileItem {
  id: string
  original_name: string
  url: string
  size: number
  mime_type: string
  created_at: string
}

const files = ref<FileItem[]>([])
const loading = ref(true)

onMounted(async () => {
  await fetchFiles()
})

async function fetchFiles() {
  loading.value = true
  try {
    const { data } = await api.get('/files')
    files.value = data
  } finally {
    loading.value = false
  }
}

async function handleUpload({ file }: { file: UploadFileInfo }) {
  if (!file.file) return
  const fd = new FormData()
  fd.append('file', file.file)
  try {
    await api.post('/files', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    message.success('上传成功')
    await fetchFiles()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '上传失败')
  }
}

async function deleteFile(id: string) {
  await api.delete(`/files/${id}`)
  files.value = files.value.filter(f => f.id !== id)
  message.success('已删除')
}

function formatSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

function copyUrl(url: string) {
  navigator.clipboard.writeText(url)
  message.success('链接已复制')
}
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px">
      <h2>📁 文件管理</h2>
      <NUpload
        :custom-request="(opt: any) => handleUpload({ file: opt.file })"
        :show-file-list="false"
        accept="image/*,.pdf,.zip,.md,.txt"
      >
        <NButton type="primary">📤 上传文件</NButton>
      </NUpload>
    </div>

    <NSpin :show="loading">
      <div v-if="files.length === 0 && !loading">
        <NEmpty description="暂无文件" />
      </div>
      <div class="file-grid">
        <NCard v-for="f in files" :key="f.id" size="small" class="file-card">
          <div v-if="f.mime_type.startsWith('image/')" class="file-preview">
            <img :src="f.url" :alt="f.original_name" />
          </div>
          <div v-else class="file-icon">📄</div>
          <div class="file-info">
            <NText strong style="font-size: 13px; word-break: break-all">{{ f.original_name }}</NText>
            <NText depth="3" style="font-size: 11px">{{ formatSize(f.size) }} · {{ new Date(f.created_at).toLocaleDateString() }}</NText>
          </div>
          <NSpace size="small" style="margin-top: 8px">
            <NButton size="tiny" @click="copyUrl(f.url)">复制链接</NButton>
            <NPopconfirm @positive-click="deleteFile(f.id)">
              <template #trigger><NButton size="tiny" type="error" quaternary>删除</NButton></template>
              确定删除此文件？
            </NPopconfirm>
          </NSpace>
        </NCard>
      </div>
    </NSpin>
  </div>
</template>

<style scoped>
.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.file-card {
  text-align: center;
}

.file-preview img {
  width: 100%;
  height: 120px;
  object-fit: cover;
  border-radius: 4px;
  margin-bottom: 8px;
}

.file-icon {
  font-size: 48px;
  padding: 16px 0;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
</style>
