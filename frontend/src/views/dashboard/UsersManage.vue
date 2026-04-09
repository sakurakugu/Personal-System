<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import {
  ElButton,
  ElCard,
  ElConfigProvider,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElMessage,
  ElOption,
  ElPagination,
  ElPopconfirm,
  ElSelect,
  ElSkeleton,
  ElSpace,
  ElSwitch,
  ElTag,
} from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { UserFilled } from '@element-plus/icons-vue'
import {
  createUser,
  deleteUser,
  fetchUsers as requestUsers,
  resetUserPassword,
  updateUser,
} from '../../features/admin/api'
import type { UserCreatePayload, UserItem, UserListQuery, UserRole, UserUpdatePayload } from '../../features/admin/types'
import { getApiErrorMessage } from '../../utils/api'
import { useAuthStore } from '../../stores/auth'
import BaseDialog from '../../components/BaseDialog.vue'

const auth = useAuthStore()
const initialLoading = ref(true)
const refreshing = ref(false)
const users = ref<UserItem[]>([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const keyword = ref('')
const roleFilter = ref('all')
const activeFilter = ref('all')

const showCreate = ref(false)
const creating = ref(false)
const createUsernameInputRef = ref<InstanceType<typeof ElInput> | null>(null)
const createForm = ref<UserCreatePayload>({
  username: '',
  nickname: null,
  email: '',
  password: '',
  role: 'user',
  is_active: true,
  bio: null,
  avatar_url: null,
})

const showEdit = ref(false)
const editing = ref(false)
const editingUserId = ref('')
const editingUserRole = ref<UserRole>('user')
const editForm = ref<UserUpdatePayload>({
  username: '',
  nickname: null,
  email: '',
  role: 'user',
  is_active: true,
  bio: null,
  avatar_url: null,
})

const showPassword = ref(false)
const resettingPassword = ref(false)
const passwordUserId = ref('')
const passwordForm = ref({ password: '', confirmPassword: '' })

const allRoleOptions = [
  { label: '普通用户', value: 'user' },
  { label: '管理员', value: 'admin' },
  { label: '超级管理员', value: 'super_admin' },
]
const canManageSuperAdmin = computed(() => auth.isSuperAdmin)
const roleOptions = computed(() =>
  canManageSuperAdmin.value
    ? allRoleOptions
    : allRoleOptions.filter((item) => item.value !== 'super_admin'),
)
const roleFilterOptions = computed(() => [{ label: '全部角色', value: 'all' }, ...roleOptions.value])
const activeFilterOptions = [
  { label: '全部状态', value: 'all' },
  { label: '启用', value: 'active' },
  { label: '禁用', value: 'inactive' },
]

const roleTagType: Record<string, 'info' | 'success' | 'warning' | 'danger'> = {
  user: 'info',
  admin: 'warning',
  super_admin: 'danger',
}
const roleLabel: Record<string, string> = {
  user: '普通用户',
  admin: '管理员',
  super_admin: '超级管理员',
}

const currentUserId = computed(() => auth.user?.id ?? '')
const showSkeleton = computed(() => initialLoading.value && users.value.length === 0)
const editingIsSelf = computed(() => editingUserId.value === currentUserId.value)
const editingIsOtherSuperAdmin = computed(
  () => editingUserRole.value === 'super_admin' && !editingIsSelf.value,
)

function resetCreateForm() {
  createForm.value = {
    username: '',
    nickname: null,
    email: '',
    password: '',
    role: 'user',
    is_active: true,
    bio: null,
    avatar_url: null,
  }
}

function focusCreateUsernameInput() {
  void nextTick(() => {
    createUsernameInputRef.value?.focus()
    createUsernameInputRef.value?.input?.focus()
  })
}

function isOtherSuperAdmin(user: UserItem) {
  return user.role === 'super_admin' && user.id !== currentUserId.value
}

function isDeleteDisabled(user: UserItem) {
  return user.id === currentUserId.value || user.role === 'super_admin'
}

async function fetchUsers(resetPage = false, options: { silent?: boolean } = {}) {
  if (resetPage) page.value = 1
  if (!canManageSuperAdmin.value && roleFilter.value === 'super_admin') {
    roleFilter.value = 'all'
  }
  const silent = options.silent ?? !initialLoading.value
  if (silent) {
    refreshing.value = true
  } else {
    initialLoading.value = true
  }
  try {
    const params: UserListQuery = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    if (roleFilter.value !== 'all') params.role = roleFilter.value
    if (activeFilter.value === 'active') params.is_active = true
    if (activeFilter.value === 'inactive') params.is_active = false
    const data = await requestUsers(params)
    users.value = data.items
    total.value = data.total
  } finally {
    if (silent) {
      refreshing.value = false
    } else {
      initialLoading.value = false
    }
  }
}

async function handleCreate() {
  if (!createForm.value.username.trim() || !createForm.value.email.trim() || !createForm.value.password) {
    ElMessage.error('请填写完整信息')
    return
  }
  creating.value = true
  try {
    await createUser({
      username: createForm.value.username.trim(),
      nickname: createForm.value.nickname?.trim() || null,
      email: createForm.value.email.trim(),
      password: createForm.value.password,
      role: createForm.value.role,
      is_active: createForm.value.is_active,
      bio: createForm.value.bio?.trim() || null,
      avatar_url: createForm.value.avatar_url?.trim() || null,
    })
    ElMessage.success('用户已创建')
    showCreate.value = false
    resetCreateForm()
    await fetchUsers()
  } catch (e: any) {
    ElMessage.error(getApiErrorMessage(e, '创建失败'))
  } finally {
    creating.value = false
  }
}

function openEdit(user: UserItem) {
  editingUserId.value = user.id
  editingUserRole.value = user.role
  editForm.value = {
    username: user.username,
    nickname: user.nickname,
    email: user.email,
    role: user.role,
    is_active: user.is_active,
    bio: user.bio,
    avatar_url: user.avatar_url,
  }
  showEdit.value = true
}

async function handleEdit() {
  editing.value = true
  try {
    await updateUser(editingUserId.value, {
      username: editForm.value.username.trim(),
      nickname: editForm.value.nickname?.trim() || null,
      email: editForm.value.email.trim(),
      role: editForm.value.role,
      is_active: editForm.value.is_active,
      bio: editForm.value.bio?.trim() || null,
      avatar_url: editForm.value.avatar_url?.trim() || null,
    })
    ElMessage.success('用户信息已更新')
    showEdit.value = false
    await fetchUsers()
  } catch (e: any) {
    ElMessage.error(getApiErrorMessage(e, '更新失败'))
  } finally {
    editing.value = false
  }
}

function openPassword(user: UserItem) {
  passwordUserId.value = user.id
  passwordForm.value.password = ''
  passwordForm.value.confirmPassword = ''
  showPassword.value = true
}

async function handlePassword() {
  if (!passwordForm.value.password) {
    ElMessage.error('请输入新密码')
    return
  }
  if (passwordForm.value.password !== passwordForm.value.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  resettingPassword.value = true
  try {
    await resetUserPassword(passwordUserId.value, passwordForm.value.password)
    ElMessage.success('密码已重置')
    showPassword.value = false
  } catch (e: any) {
    ElMessage.error(getApiErrorMessage(e, '重置失败'))
  } finally {
    resettingPassword.value = false
  }
}

async function handleDelete(userId: string) {
  try {
    await deleteUser(userId)
    ElMessage.success('用户已删除')
    if (users.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    await fetchUsers()
  } catch (e: any) {
    ElMessage.error(getApiErrorMessage(e, '删除失败'))
  }
}

function formatDate(value: string) {
  return new Date(value).toLocaleString()
}

function handlePageChange(nextPage: number) {
  page.value = nextPage
  fetchUsers()
}

function handlePageSizeChange(nextSize: number) {
  pageSize.value = nextSize
  fetchUsers(true)
}

onMounted(() => fetchUsers())
</script>

<template>
  <ElConfigProvider :locale="zhCn">
    <div class="users-page">
      <div class="users-head">
        <h2 class="users-title">
          <ElIcon><UserFilled /></ElIcon>
          <span>用户管理</span>
        </h2>
        <ElButton type="primary" @click="showCreate = true">新增用户</ElButton>
      </div>

      <ElCard style="margin-bottom: 12px">
        <ElSpace wrap>
          <ElInput
            v-model="keyword"
            placeholder="昵称/用户名/邮箱搜索"
            clearable
            style="width: 220px"
            @keydown.enter="fetchUsers(true)"
          />
          <ElSelect v-model="roleFilter" style="width: 140px">
            <ElOption v-for="item in roleFilterOptions" :key="item.value" :label="item.label" :value="item.value" />
          </ElSelect>
          <ElSelect v-model="activeFilter" style="width: 120px">
            <ElOption v-for="item in activeFilterOptions" :key="item.value" :label="item.label" :value="item.value" />
          </ElSelect>
          <ElButton @click="fetchUsers(true)">查询</ElButton>
        </ElSpace>
      </ElCard>

      <ElSkeleton :loading="showSkeleton" animated>
        <div v-loading="refreshing" class="user-list">
          <div
            v-for="item in users"
            :key="item.id"
            class="user-item"
            :class="{ 'is-active': item.is_active, 'is-inactive': !item.is_active }"
          >
            <div class="user-row">
              <div class="user-main">
                <div class="user-line">
                  <strong>{{ item.nickname || item.username }}</strong>
                  <ElTag :type="roleTagType[item.role]">{{ roleLabel[item.role] }}</ElTag>
                  <ElTag v-if="item.id === currentUserId" type="primary">当前账号</ElTag>
                </div>
                <div class="user-meta">{{ item.email }}</div>
                <div class="user-meta">创建时间：{{ formatDate(item.created_at) }}</div>
              </div>
              <ElSpace size="small">
                <ElButton size="small" :disabled="isOtherSuperAdmin(item)" @click="openEdit(item)">编辑</ElButton>
                <ElButton size="small" :disabled="isOtherSuperAdmin(item)" @click="openPassword(item)">重置密码</ElButton>
                <ElPopconfirm title="确认删除该用户？" confirm-button-text="确定" cancel-button-text="取消" width="180" @confirm="handleDelete(item.id)">
                  <template #reference>
                    <ElButton size="small" type="danger" text :disabled="isDeleteDisabled(item)">
                      删除
                    </ElButton>
                  </template>
                </ElPopconfirm>
              </ElSpace>
            </div>
          </div>
        </div>
      </ElSkeleton>

      <div class="pager">
        <ElPagination
          :current-page="page"
          :page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @update:current-page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </div>

      <BaseDialog
        :model-value="showCreate"
        title="新增用户"
        width="520px"
        style="max-width: 96vw"
        @update:model-value="showCreate = $event"
        @opened="focusCreateUsernameInput"
      >
        <ElForm label-width="80px" @submit.prevent="handleCreate">
          <ElFormItem label="用户名">
            <ElInput ref="createUsernameInputRef" v-model="createForm.username" />
          </ElFormItem>
          <ElFormItem label="昵称">
            <ElInput v-model="createForm.nickname" />
          </ElFormItem>
          <ElFormItem label="邮箱">
            <ElInput v-model="createForm.email" />
          </ElFormItem>
          <ElFormItem label="初始密码">
            <ElInput v-model="createForm.password" type="password" show-password />
          </ElFormItem>
          <ElFormItem label="角色">
            <ElSelect v-model="createForm.role">
              <ElOption v-for="item in roleOptions" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="启用">
            <ElSwitch v-model="createForm.is_active" />
          </ElFormItem>
          <ElFormItem label="头像链接">
            <ElInput v-model="createForm.avatar_url" />
          </ElFormItem>
          <ElFormItem label="简介">
            <ElInput v-model="createForm.bio" type="textarea" />
          </ElFormItem>
          <ElButton type="primary" style="width: 100%" native-type="submit" :loading="creating">创建</ElButton>
        </ElForm>
      </BaseDialog>

      <BaseDialog :model-value="showEdit" title="编辑用户" width="520px" style="max-width: 96vw" @update:model-value="showEdit = $event">
        <ElForm label-width="80px" @submit.prevent="handleEdit">
          <ElFormItem label="用户名">
            <ElInput v-model="editForm.username" />
          </ElFormItem>
          <ElFormItem label="昵称">
            <ElInput v-model="editForm.nickname" />
          </ElFormItem>
          <ElFormItem label="邮箱">
            <ElInput v-model="editForm.email" />
          </ElFormItem>
          <ElFormItem label="角色">
            <ElSelect v-model="editForm.role" :disabled="editingIsSelf || editingIsOtherSuperAdmin">
              <ElOption v-for="item in roleOptions" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="启用">
            <ElSwitch v-model="editForm.is_active" :disabled="editingIsSelf || editingIsOtherSuperAdmin" />
          </ElFormItem>
          <ElFormItem label="头像链接">
            <ElInput v-model="editForm.avatar_url" />
          </ElFormItem>
          <ElFormItem label="简介">
            <ElInput v-model="editForm.bio" type="textarea" />
          </ElFormItem>
          <ElButton type="primary" style="width: 100%" native-type="submit" :loading="editing">保存</ElButton>
        </ElForm>
      </BaseDialog>

      <BaseDialog :model-value="showPassword" title="重置密码" width="420px" style="max-width: 96vw" @update:model-value="showPassword = $event">
        <ElForm label-width="100px" @submit.prevent="handlePassword">
          <ElFormItem label="新密码">
            <ElInput v-model="passwordForm.password" type="password" show-password />
          </ElFormItem>
          <ElFormItem label="确认密码">
            <ElInput v-model="passwordForm.confirmPassword" type="password" show-password />
          </ElFormItem>
          <ElButton type="primary" style="width: 100%" native-type="submit" :loading="resettingPassword">确认重置</ElButton>
        </ElForm>
      </BaseDialog>
    </div>
  </ElConfigProvider>
</template>

<style scoped>
.users-page {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

.users-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 12px;
}

.users-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.user-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-item {
  background: white;
  border-radius: 12px;
  padding: 16px;
  border-left: 3px solid #909399;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.2s ease;
}

.user-item.is-active {
  border-left-color: #18a058;
}

.user-item:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.dark .user-item {
  background: var(--el-bg-color-overlay);
  border-left-color: #909399;
}

.dark .user-item.is-active {
  border-left-color: #18a058;
}

.dark .el-button--danger.is-text {
  color: #f56c6c;
}

.dark .el-button--danger.is-text:hover {
  color: #ff8a8a;
  background: rgba(245, 108, 108, 0.1);
}

.dark .el-button--danger.is-text:disabled {
  color: rgba(245, 108, 108, 0.4);
}

.user-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.user-main {
  min-width: 260px;
}

.user-line {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.user-meta {
  color: #888;
  font-size: 13px;
  margin-top: 4px;
}

.dark .user-meta {
  color: var(--text-tertiary);
}

.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  padding: 6px 14px 8px;
}

.pager :deep(.el-pagination__total) {
  color: var(--text-primary, #333333);
}

.pager :deep(.el-pagination__sizes) {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
}

.pager :deep(.el-pagination__sizes .el-select) {
  display: inline-flex;
  align-items: center;
  width: 100px !important;
  min-width: 100px;
  flex-shrink: 0;
}

.pager :deep(.el-pagination__sizes .el-select__wrapper) {
  width: 100%;
  min-width: 80px;
  justify-content: center;
}

.pager :deep(.el-pagination__sizes .el-input__wrapper) {
  display: inline-flex;
  align-items: center;
  width: 100%;
}

.pager :deep(.el-pagination__sizes .el-select__selection) {
  justify-content: center;
}

.pager :deep(.el-pagination__sizes .el-select__selected-item),
.pager :deep(.el-pagination__sizes .el-select__placeholder) {
  width: 100%;
  text-align: center;
  justify-content: center;
}
</style>
