<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  ElButton,
  ElCard,
  ElConfigProvider,
  ElForm,
  ElFormItem,
  ElInput,
  ElPagination,
  ElSpace,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTag,
  ElMessage,
  ElMessageBox,
} from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { BellFilled, Plus, Edit, Delete } from '@element-plus/icons-vue'
import {
  createAnnouncement,
  deleteAnnouncement,
  fetchAnnouncements as requestAnnouncements,
  updateAnnouncement,
} from '../../features/admin/api'
import type { AnnouncementPayload, AnnouncementRecord } from '../../features/admin/types'
import { getApiErrorMessage } from '../../utils/api'
import BaseDialog from '../../components/BaseDialog.vue'

const loading = ref(false)
const announcements = ref<AnnouncementRecord[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<string | null>(null)
const form = ref<AnnouncementPayload>({
  title: '',
  content: '',
  is_active: true,
})
const formLoading = ref(false)

function buildAnnouncementPayload(): AnnouncementPayload {
  return {
    title: form.value.title.trim(),
    content: form.value.content.trim(),
    is_active: form.value.is_active,
  }
}

async function fetchAnnouncements() {
  loading.value = true
  try {
    const data = await requestAnnouncements(page.value, pageSize.value)
    announcements.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '获取公告列表失败'))
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  isEdit.value = false
  editId.value = null
  form.value = {
    title: '',
    content: '',
    is_active: true,
  }
  dialogVisible.value = true
}

function openEditDialog(row: AnnouncementRecord) {
  isEdit.value = true
  editId.value = row.id
  form.value = {
    title: row.title,
    content: row.content,
    is_active: row.is_active,
  }
  dialogVisible.value = true
}

async function saveAnnouncement() {
  const payload = buildAnnouncementPayload()

  if (!payload.title) {
    ElMessage.warning('请输入标题')
    return
  }

  formLoading.value = true
  try {
    if (isEdit.value && editId.value) {
      await updateAnnouncement(editId.value, payload)
      ElMessage.success('公告已更新')
    } else {
      await createAnnouncement(payload)
      ElMessage.success('公告已创建')
    }
    dialogVisible.value = false
    await fetchAnnouncements()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, isEdit.value ? '更新失败' : '创建失败'))
  } finally {
    formLoading.value = false
  }
}

async function handleDeleteAnnouncement(row: AnnouncementRecord) {
  try {
    await ElMessageBox.confirm(
      `确定要删除公告 "${row.title}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await deleteAnnouncement(row.id)
    ElMessage.success('公告已删除')
    await fetchAnnouncements()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(getApiErrorMessage(error, '删除失败'))
    }
  }
}

async function toggleStatus(row: AnnouncementRecord) {
  try {
    await updateAnnouncement(row.id, {
      title: row.title,
      content: row.content,
      is_active: !row.is_active,
    })
    ElMessage.success('状态已更新')
    await fetchAnnouncements()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '更新失败'))
  }
}

onMounted(() => {
  void fetchAnnouncements()
})
</script>

<template>
  <ElConfigProvider :locale="zhCn">
    <div class="page-container">
      <div class="page-header">
        <h2 class="page-title">
          <span class="page-title-text">
            <ElIcon><BellFilled /></ElIcon>
            <span>公告管理</span>
          </span>
          <ElButton type="primary" :icon="Plus" @click="openCreateDialog">
            新建公告
          </ElButton>
        </h2>
      </div>

      <ElCard class="announcements-card">
        <div class="announcements-body">
          <div class="announcements-table-wrap">
            <ElTable
              v-loading="loading"
              :data="announcements"
              stripe
              height="100%"
              class="announcements-table"
            >
              <ElTableColumn prop="title" label="标题" min-width="180" show-overflow-tooltip />
              <ElTableColumn prop="content" label="内容" min-width="250" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="content-preview">{{ row.content || '仅标题' }}</span>
                </template>
              </ElTableColumn>
              <ElTableColumn prop="is_active" label="状态" width="100" align="center">
                <template #default="{ row }">
                  <ElTag :type="row.is_active ? 'success' : 'info'" size="small">
                    {{ row.is_active ? '生效中' : '已下架' }}
                  </ElTag>
                </template>
              </ElTableColumn>
              <ElTableColumn prop="created_at" label="创建时间" width="160">
                <template #default="{ row }">
                  {{ new Date(row.created_at).toLocaleString('zh-CN') }}
                </template>
              </ElTableColumn>
              <ElTableColumn label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <ElSpace>
                    <ElButton type="primary" size="small" :icon="Edit" @click="openEditDialog(row)">
                      编辑
                    </ElButton>
                    <ElButton
                      :type="row.is_active ? 'warning' : 'success'"
                      size="small"
                      @click="toggleStatus(row)"
                    >
                      {{ row.is_active ? '下架' : '上架' }}
                    </ElButton>
                    <ElButton
                      type="danger"
                      size="small"
                      :icon="Delete"
                      @click="handleDeleteAnnouncement(row)"
                    >
                      删除
                    </ElButton>
                  </ElSpace>
                </template>
              </ElTableColumn>
            </ElTable>
          </div>

          <div class="pagination-wrap">
            <ElPagination
              v-model:current-page="page"
              v-model:page-size="pageSize"
              :total="total"
              layout="total, sizes, prev, pager, next"
              :page-sizes="[10, 20, 50]"
              @change="fetchAnnouncements"
            />
          </div>
        </div>
      </ElCard>

      <!-- 新建/编辑对话框 -->
      <BaseDialog
        v-model="dialogVisible"
        :title="isEdit ? '编辑公告' : '新建公告'"
        width="600px"
        destroy-on-close
      >
        <ElForm :model="form" label-width="80px">
          <ElFormItem label="标题" required>
            <ElInput v-model="form.title" placeholder="请输入公告标题" maxlength="200" show-word-limit />
          </ElFormItem>
          <ElFormItem label="内容">
            <ElInput
              v-model="form.content"
              type="textarea"
              :rows="6"
              placeholder="请输入公告内容（选填）"
            />
          </ElFormItem>
          <ElFormItem label="立即生效">
            <ElSwitch v-model="form.is_active" />
          </ElFormItem>
        </ElForm>
        <template #footer>
          <ElSpace>
            <ElButton @click="dialogVisible = false">取消</ElButton>
            <ElButton type="primary" :loading="formLoading" @click="saveAnnouncement">
              {{ isEdit ? '保存' : '创建' }}
            </ElButton>
          </ElSpace>
        </template>
      </BaseDialog>
    </div>
  </ElConfigProvider>
</template>

<style scoped>
.page-container {
  height: 100%;
  padding: 24px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow: hidden;
}

.page-header {
  flex-shrink: 0;
}

.page-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 0;
}

.page-title-text {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.announcements-card {
  flex: 1;
  min-height: 0;
  border-radius: var(--dashboard-panel-radius, 12px);
  overflow: hidden;
}

.announcements-card :deep(.el-card__body) {
  height: 100%;
  padding: 0;
}

.announcements-body {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.announcements-table-wrap {
  flex: 1;
  min-height: 0;
  padding: 20px 20px 0;
}

.announcements-table {
  height: 100%;
}

.announcements-table :deep(.el-table) {
  border-radius: var(--dashboard-panel-radius, 12px) var(--dashboard-panel-radius, 12px) 0 0;
}

.pagination-wrap {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px 20px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.content-preview {
  display: inline-block;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 768px) {
  .page-container {
    padding: 16px;
    gap: 16px;
  }

  .page-title {
    align-items: flex-start;
    flex-direction: column;
  }

  .announcements-table-wrap {
    padding: 16px 16px 0;
  }

  .pagination-wrap {
    justify-content: center;
    padding: 16px;
  }
}
</style>
