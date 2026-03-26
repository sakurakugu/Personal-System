<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElButton, ElCard, ElEmpty, ElIcon, ElMessage, ElPopconfirm, ElSkeleton, ElSpace, ElText, ElUpload, type UploadRequestOptions } from 'element-plus'
import { FolderOpened, UploadFilled, Document } from '@element-plus/icons-vue'
import api from '../../utils/api'

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

async function handleUpload(opt: UploadRequestOptions) {
  const fd = new FormData()
  fd.append('file', opt.file)
  try {
    await api.post('/files', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    ElMessage.success('上传成功')
    await fetchFiles()
    opt.onSuccess({})
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '上传失败')
    opt.onError(e)
  }
}

async function deleteFile(id: string) {
  await api.delete(`/files/${id}`)
  files.value = files.value.filter(f => f.id !== id)
  ElMessage.success('已删除')
}

function formatSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

function copyUrl(url: string) {
  navigator.clipboard.writeText(url)
  ElMessage.success('链接已复制')
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 style="display: flex; align-items: center; gap: 8px">
        <ElIcon><FolderOpened /></ElIcon>
        <span>文件管理</span>
      </h2>
      <div class="page-actions">
        <ElUpload
          :http-request="handleUpload"
          :show-file-list="false"
          accept="image/*,.pdf,.zip,.md,.txt"
        >
          <ElButton type="primary">
            <ElIcon style="margin-right: 6px"><UploadFilled /></ElIcon>
            <span>上传文件</span>
          </ElButton>
        </ElUpload>
      </div>
    </div>

    <ElSkeleton :loading="loading" animated>
      <div v-if="files.length === 0 && !loading" class="empty-state">
        <ElEmpty description="暂无文件" />
      </div>
      <div class="file-grid">
        <ElCard v-for="f in files" :key="f.id" class="file-card">
          <div v-if="f.mime_type.startsWith('image/')" class="file-preview">
            <img :src="f.url" :alt="f.original_name">
          </div>
          <div v-else class="file-icon">
            <ElIcon><Document /></ElIcon>
          </div>
          <div class="file-info">
            <ElText tag="b" style="font-size: 13px; word-break: break-all">{{ f.original_name }}</ElText>
            <ElText type="info" style="font-size: 11px">{{ formatSize(f.size) }} · {{ new Date(f.created_at).toLocaleDateString() }}</ElText>
          </div>
          <ElSpace size="small" style="margin-top: 8px">
            <ElButton size="small" @click="copyUrl(f.url)">复制链接</ElButton>
            <ElPopconfirm @confirm="deleteFile(f.id)">
              <template #reference><ElButton size="small" type="danger" text>删除</ElButton></template>
              确定删除此文件？
            </ElPopconfirm>
          </ElSpace>
        </ElCard>
      </div>
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

.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.page-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
}

.empty-state {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
}

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
