<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  ElButton,
  ElCard,
  ElDialog,
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
import { BellFilled, Plus, Edit, Delete } from '@element-plus/icons-vue'
import api from '../../utils/api'

interface Announcement {
  id: string
  title: string
  content: string
  is_active: boolean
  created_at: string
  updated_at: string
}

const loading = ref(false)
const announcements = ref<Announcement[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<string | null>(null)
const form = ref({
  title: '',
  content: '',
  is_active: true,
})
const formLoading = ref(false)

// 获取公告列表
async function fetchAnnouncements() {
  loading.value = true
  try {
    const { data } = await api.get('/announcements', {
      params: { page: page.value, page_size: pageSize.value },
    })
    announcements.value = data.items
    total.value = data.total
  } catch {
    ElMessage.error('获取公告列表失败')
  } finally {
    loading.value = false
  }
}

// 打开新建对话框
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

// 打开编辑对话框
function openEditDialog(row: Announcement) {
  isEdit.value = true
  editId.value = row.id
  form.value = {
    title: row.title,
    content: row.content,
    is_active: row.is_active,
  }
  dialogVisible.value = true
}

// 保存公告
async function saveAnnouncement() {
  if (!form.value.title.trim()) {
    ElMessage.warning('请输入标题')
    return
  }
  if (!form.value.content.trim()) {
    ElMessage.warning('请输入内容')
    return
  }

  formLoading.value = true
  try {
    if (isEdit.value && editId.value) {
      await api.patch(`/announcements/${editId.value}`, form.value)
      ElMessage.success('公告已更新')
    } else {
      await api.post('/announcements', form.value)
      ElMessage.success('公告已创建')
    }
    dialogVisible.value = false
    await fetchAnnouncements()
  } catch {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    formLoading.value = false
  }
}

// 删除公告
async function deleteAnnouncement(row: Announcement) {
  try {
    await ElMessageBox.confirm(
      `确定要删除公告 "${row.title}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await api.delete(`/announcements/${row.id}`)
    ElMessage.success('公告已删除')
    await fetchAnnouncements()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 切换状态
async function toggleStatus(row: Announcement) {
  try {
    await api.patch(`/announcements/${row.id}`, {
      is_active: !row.is_active,
    })
    ElMessage.success('状态已更新')
    await fetchAnnouncements()
  } catch {
    ElMessage.error('更新失败')
  }
}

onMounted(() => {
  fetchAnnouncements()
})
</script>

<template>
  <div>
    <h2 style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px">
      <span style="display: inline-flex; align-items: center; gap: 8px">
        <ElIcon><BellFilled /></ElIcon>
        <span>公告管理</span>
      </span>
      <ElButton type="primary" :icon="Plus" @click="openCreateDialog">
        新建公告
      </ElButton>
    </h2>

    <ElCard>
      <ElTable :data="announcements" v-loading="loading" stripe>
        <ElTableColumn prop="title" label="标题" min-width="180" show-overflow-tooltip />
        <ElTableColumn prop="content" label="内容" min-width="250" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="content-preview">{{ row.content }}</span>
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
            {{ new Date(row.created_at).toLocaleString() }}
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
              <ElButton type="danger" size="small" :icon="Delete" @click="deleteAnnouncement(row)">
                删除
              </ElButton>
            </ElSpace>
          </template>
        </ElTableColumn>
      </ElTable>

      <div style="display: flex; justify-content: center; margin-top: 20px">
        <ElPagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          layout="prev, pager, next, sizes, total"
          :page-sizes="[10, 20, 50]"
          @change="fetchAnnouncements"
        />
      </div>
    </ElCard>

    <!-- 新建/编辑对话框 -->
    <ElDialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑公告' : '新建公告'"
      width="600px"
      destroy-on-close
    >
      <ElForm :model="form" label-width="80px">
        <ElFormItem label="标题" required>
          <ElInput v-model="form.title" placeholder="请输入公告标题" maxlength="200" show-word-limit />
        </ElFormItem>
        <ElFormItem label="内容" required>
          <ElInput
            v-model="form.content"
            type="textarea"
            :rows="6"
            placeholder="请输入公告内容"
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
    </ElDialog>
  </div>
</template>

<style scoped>
.content-preview {
  display: inline-block;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
