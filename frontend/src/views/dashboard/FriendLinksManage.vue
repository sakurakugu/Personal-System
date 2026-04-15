<script setup lang="ts">
import { ElButton, ElCard, ElForm, ElFormItem, ElIcon, ElInput, ElMessage, ElOption, ElPagination, ElPopconfirm, ElSelect, ElSkeleton, ElSpace, ElTag } from 'element-plus'
import { Link } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import {
  approveFriendLink as requestApproveFriendLink,
  createFriendLink,
  deleteFriendLink as requestDeleteFriendLink,
  fetchFriendLinkCategories,
  fetchFriendLinks as requestFriendLinks,
  rejectFriendLink as requestRejectFriendLink,
  updateFriendLink,
} from '../../features/friend-links/api'
import type { FriendLinkAdminPayload, FriendLinkRecord, FriendLinkStatus } from '../../features/friend-links/types'
import { getApiErrorMessage } from '../../utils/api'
import BaseDialog from '../../components/BaseDialog.vue'

const initialLoading = ref(true)
const refreshing = ref(false)
const friendLinks = ref<FriendLinkRecord[]>([])
const pagination = ref({ page: 1, pageSize: 10, total: 0, pageCount: 0 })
const statusFilter = ref<FriendLinkStatus | ''>('')
const categories = ref<string[]>([])

const showDialog = ref(false)
const isEdit = ref(false)
const currentId = ref('')
const dialogLoading = ref(false)

const form = ref<FriendLinkAdminPayload>({
  name: '',
  url: '',
  description: '',
  logo_url: '',
  category: '',
  status: 'approved',
})
const showSkeleton = computed(() => initialLoading.value && friendLinks.value.length === 0)

async function fetchFriendLinks(page = 1, options: { silent?: boolean } = {}) {
  const silent = options.silent ?? !initialLoading.value
  if (silent) {
    refreshing.value = true
  } else {
    initialLoading.value = true
  }
  try {
    const data = await requestFriendLinks(page, pagination.value.pageSize, statusFilter.value)
    friendLinks.value = data.items
    pagination.value = {
      page: data.page,
      pageSize: data.page_size,
      total: data.total,
      pageCount: data.pages,
    }
  } finally {
    if (silent) {
      refreshing.value = false
    } else {
      initialLoading.value = false
    }
  }
}

function openCreate() {
  isEdit.value = false
  currentId.value = ''
  form.value = {
    name: '',
    url: '',
    description: '',
    logo_url: '',
    category: '',
    status: 'approved',
  }
  showDialog.value = true
}

function openEdit(friendLink: FriendLinkRecord) {
  isEdit.value = true
  currentId.value = friendLink.id
  form.value = {
    name: friendLink.name,
    url: friendLink.url,
    description: friendLink.description || '',
    logo_url: friendLink.logo_url || '',
    category: friendLink.category || '',
    status: friendLink.status,
  }
  showDialog.value = true
}

async function save() {
  if (!form.value.name.trim() || !form.value.url.trim()) {
    ElMessage.warning('请填写完整信息')
    return
  }

  dialogLoading.value = true
  try {
    if (isEdit.value) {
      await updateFriendLink(currentId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createFriendLink(form.value)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    void fetchFriendLinks(pagination.value.page)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '保存失败'))
  } finally {
    dialogLoading.value = false
  }
}

async function deleteFriendLink(id: string) {
  try {
    await requestDeleteFriendLink(id)
    ElMessage.success('删除成功')
    void fetchFriendLinks(pagination.value.page)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '删除失败'))
  }
}

async function approveFriendLink(friendLink: FriendLinkRecord) {
  try {
    await requestApproveFriendLink(friendLink.id)
    ElMessage.success('已通过')
    void fetchFriendLinks(pagination.value.page)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '操作失败'))
  }
}

async function rejectFriendLink(friendLink: FriendLinkRecord) {
  try {
    await requestRejectFriendLink(friendLink.id)
    ElMessage.success('已拒绝')
    void fetchFriendLinks(pagination.value.page)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '操作失败'))
  }
}

function getStatusType(status: string) {
  switch (status) {
    case 'approved':
      return 'success'
    case 'pending':
      return 'warning'
    case 'rejected':
      return 'danger'
    default:
      return 'info'
  }
}

function getStatusLabel(status: string) {
  switch (status) {
    case 'approved':
      return '已通过'
    case 'pending':
      return '待审核'
    case 'rejected':
      return '已拒绝'
    default:
      return status
  }
}

function getCardStatusClass(status: string) {
  switch (status) {
    case 'approved':
      return 'link-card--approved'
    case 'pending':
      return 'link-card--pending'
    case 'rejected':
      return 'link-card--rejected'
    default:
      return ''
  }
}

async function loadCategories() {
  try {
    categories.value = await fetchFriendLinkCategories()
  } catch {
    categories.value = []
  }
}

onMounted(() => {
  void fetchFriendLinks()
  void loadCategories()
})
</script>

<template>
  <div class="page-container">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px">
      <h2 style="display: flex; align-items: center; gap: 8px">
        <ElIcon><Link /></ElIcon>
        <span>友链管理</span>
      </h2>
      <ElButton type="primary" @click="openCreate">+ 添加友链</ElButton>
    </div>

    <ElCard style="margin-bottom: 16px">
      <ElSpace>
        <span>状态筛选：</span>
        <ElSelect v-model="statusFilter" placeholder="全部状态" clearable style="width: 120px" @change="fetchFriendLinks(1)">
          <ElOption label="全部" value="" />
          <ElOption label="待审核" value="pending" />
          <ElOption label="已通过" value="approved" />
          <ElOption label="已拒绝" value="rejected" />
        </ElSelect>
      </ElSpace>
    </ElCard>

    <ElSkeleton :loading="showSkeleton" animated>
      <div v-loading="refreshing" class="links-list">
        <ElCard
          v-for="friendLink in friendLinks"
          :key="friendLink.id"
          shadow="hover"
          :class="['link-card', getCardStatusClass(friendLink.status)]"
        >
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px">
            <div style="flex: 1; min-width: 0">
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px">
                <strong style="font-size: 16px">{{ friendLink.name }}</strong>
                <ElTag :type="getStatusType(friendLink.status)" size="small">
                  {{ getStatusLabel(friendLink.status) }}
                </ElTag>
                <ElTag v-if="friendLink.is_auto_exchange" type="info" size="small">自动交换</ElTag>
                <ElTag v-if="friendLink.category" type="primary" size="small">{{ friendLink.category }}</ElTag>
              </div>
              <div style="color: #666; font-size: 13px; margin-bottom: 4px">
                <a :href="friendLink.url" target="_blank" style="color: var(--el-color-primary); text-decoration: none">{{ friendLink.url }}</a>
              </div>
              <div v-if="friendLink.description" style="color: #888; font-size: 13px; margin-bottom: 4px">
                {{ friendLink.description }}
              </div>
              <div v-if="friendLink.contact_name || friendLink.contact_email" style="color: #999; font-size: 12px">
                联系人: {{ friendLink.contact_name || '未填写' }} · {{ friendLink.contact_email || '未填写邮箱' }}
              </div>
            </div>
            <ElSpace size="small">
              <template v-if="friendLink.status === 'pending'">
                <ElButton type="success" size="small" @click="approveFriendLink(friendLink)">通过</ElButton>
                <ElButton type="danger" size="small" @click="rejectFriendLink(friendLink)">拒绝</ElButton>
              </template>
              <ElButton size="small" @click="openEdit(friendLink)">编辑</ElButton>
              <ElPopconfirm @confirm="deleteFriendLink(friendLink.id)">
                <template #reference>
                  <ElButton size="small" type="danger" text>删除</ElButton>
                </template>
                确定删除这个友链？
              </ElPopconfirm>
            </ElSpace>
          </div>
        </ElCard>
      </div>
    </ElSkeleton>

    <div v-if="pagination.pageCount > 1" style="display: flex; justify-content: center; margin-top: 24px">
      <ElPagination
        :current-page="pagination.page"
        :page-count="pagination.pageCount"
        layout="prev, pager, next"
        @update:current-page="fetchFriendLinks"
      />
    </div>

    <!-- 添加/编辑对话框 -->
    <BaseDialog v-model="showDialog" :title="isEdit ? '编辑友链' : '添加友链'" width="500px">
      <ElForm label-position="top">
        <ElFormItem label="网站名称">
          <ElInput v-model="form.name" placeholder="网站名称" maxlength="100" />
        </ElFormItem>
        <ElFormItem label="网站链接">
          <ElInput v-model="form.url" placeholder="https://example.com" maxlength="500" />
        </ElFormItem>
        <ElFormItem label="描述">
          <ElInput v-model="form.description" type="textarea" :rows="2" placeholder="网站描述" maxlength="200" />
        </ElFormItem>
        <ElFormItem label="Logo">
          <ElInput v-model="form.logo_url" placeholder="https://example.com/logo.png" maxlength="500" />
        </ElFormItem>
        <ElFormItem label="分类">
          <ElSelect
            v-model="form.category"
            placeholder="请选择或输入分类"
            clearable
            filterable
            allow-create
            default-first-option
            style="width: 100%"
          >
            <ElOption v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="状态">
          <ElSelect v-model="form.status" style="width: 100%">
            <ElOption label="待审核" value="pending" />
            <ElOption label="已通过" value="approved" />
            <ElOption label="已拒绝" value="rejected" />
          </ElSelect>
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="showDialog = false">取消</ElButton>
        <ElButton type="primary" :loading="dialogLoading" @click="save">
          {{ isEdit ? '更新' : '创建' }}
        </ElButton>
      </template>
    </BaseDialog>
  </div>
</template>

<style scoped>
.page-container {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

.links-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.link-card {
  border-left: 3px solid #909399;
  border-radius: 12px;
  overflow: hidden;
}

.link-card--approved {
  border-left-color: var(--el-color-primary);
}

.link-card--pending {
  border-left-color: #e6a23c;
}

.link-card--rejected {
  border-left-color: #f56c6c;
}

.link-card :deep(.el-card__body) {
  padding: 16px;
}

.dark .link-card {
  background: var(--el-bg-color-overlay);
  --el-card-bg-color: var(--el-bg-color-overlay);
}

.dark .link-card--approved {
  border-left-color: var(--el-color-primary) !important;
}

.dark .link-card--pending {
  border-left-color: #e6a23c !important;
}

.dark .link-card--rejected {
  border-left-color: #f56c6c !important;
}
</style>
