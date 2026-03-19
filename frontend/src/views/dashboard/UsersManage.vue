<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  NButton,
  NCard,
  NForm,
  NFormItem,
  NInput,
  NModal,
  NPagination,
  NPopconfirm,
  NSelect,
  NSpace,
  NSpin,
  NSwitch,
  NTag,
  useMessage,
} from 'naive-ui'
import { ElIcon } from 'element-plus'
import { UserFilled } from '@element-plus/icons-vue'
import api from '../../utils/api'
import { useAuthStore } from '../../stores/auth'

interface UserItem {
  id: string
  username: string
  email: string
  role: 'user' | 'admin' | 'super_admin'
  avatar_url: string | null
  bio: string | null
  is_active: boolean
  created_at: string
}

const auth = useAuthStore()
const message = useMessage()
const loading = ref(false)
const users = ref<UserItem[]>([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const keyword = ref('')
const roleFilter = ref('all')
const activeFilter = ref('all')

const showCreate = ref(false)
const creating = ref(false)
const createForm = ref({
  username: '',
  email: '',
  password: '',
  role: 'user',
  is_active: true,
  bio: '',
  avatar_url: '',
})

const showEdit = ref(false)
const editing = ref(false)
const editingUserId = ref('')
const editingUserRole = ref<'user' | 'admin' | 'super_admin'>('user')
const editForm = ref({
  username: '',
  email: '',
  role: 'user',
  is_active: true,
  bio: '',
  avatar_url: '',
})

const showPassword = ref(false)
const resettingPassword = ref(false)
const passwordUserId = ref('')
const passwordForm = ref({ password: '' })

const roleOptions = [
  { label: '普通用户', value: 'user' },
  { label: '管理员', value: 'admin' },
  { label: '超级管理员', value: 'super_admin' },
]
const roleFilterOptions = [{ label: '全部角色', value: 'all' }, ...roleOptions]
const activeFilterOptions = [
  { label: '全部状态', value: 'all' },
  { label: '启用', value: 'active' },
  { label: '禁用', value: 'inactive' },
]

const roleTagType: Record<string, 'default' | 'success' | 'warning' | 'error'> = {
  user: 'default',
  admin: 'warning',
  super_admin: 'error',
}
const roleLabel: Record<string, string> = {
  user: '普通用户',
  admin: '管理员',
  super_admin: '超级管理员',
}

const currentUserId = computed(() => auth.user?.id ?? '')
const editingIsSelf = computed(() => editingUserId.value === currentUserId.value)
const editingIsOtherSuperAdmin = computed(
  () => editingUserRole.value === 'super_admin' && !editingIsSelf.value,
)

function resetCreateForm() {
  createForm.value = {
    username: '',
    email: '',
    password: '',
    role: 'user',
    is_active: true,
    bio: '',
    avatar_url: '',
  }
}

async function fetchUsers(resetPage = false) {
  if (resetPage) page.value = 1
  loading.value = true
  try {
    const params: Record<string, string | number | boolean> = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    if (roleFilter.value !== 'all') params.role = roleFilter.value
    if (activeFilter.value === 'active') params.is_active = true
    if (activeFilter.value === 'inactive') params.is_active = false
    const { data } = await api.get('/users', { params })
    users.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!createForm.value.username.trim() || !createForm.value.email.trim() || !createForm.value.password) {
    message.error('请填写完整信息')
    return
  }
  creating.value = true
  try {
    await api.post('/users', {
      username: createForm.value.username.trim(),
      email: createForm.value.email.trim(),
      password: createForm.value.password,
      role: createForm.value.role,
      is_active: createForm.value.is_active,
      bio: createForm.value.bio.trim() || null,
      avatar_url: createForm.value.avatar_url.trim() || null,
    })
    message.success('用户已创建')
    showCreate.value = false
    resetCreateForm()
    await fetchUsers()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

function openEdit(user: UserItem) {
  editingUserId.value = user.id
  editingUserRole.value = user.role
  editForm.value = {
    username: user.username,
    email: user.email,
    role: user.role,
    is_active: user.is_active,
    bio: user.bio || '',
    avatar_url: user.avatar_url || '',
  }
  showEdit.value = true
}

async function handleEdit() {
  editing.value = true
  try {
    await api.patch(`/users/${editingUserId.value}`, {
      username: editForm.value.username.trim(),
      email: editForm.value.email.trim(),
      role: editForm.value.role,
      is_active: editForm.value.is_active,
      bio: editForm.value.bio.trim() || null,
      avatar_url: editForm.value.avatar_url.trim() || null,
    })
    message.success('用户信息已更新')
    showEdit.value = false
    await fetchUsers()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '更新失败')
  } finally {
    editing.value = false
  }
}

function openPassword(user: UserItem) {
  passwordUserId.value = user.id
  passwordForm.value.password = ''
  showPassword.value = true
}

async function handlePassword() {
  if (!passwordForm.value.password) {
    message.error('请输入新密码')
    return
  }
  resettingPassword.value = true
  try {
    await api.patch(`/users/${passwordUserId.value}/password`, {
      password: passwordForm.value.password,
    })
    message.success('密码已重置')
    showPassword.value = false
  } catch (e: any) {
    message.error(e.response?.data?.detail || '重置失败')
  } finally {
    resettingPassword.value = false
  }
}

async function handleDelete(userId: string) {
  try {
    await api.delete(`/users/${userId}`)
    message.success('用户已删除')
    if (users.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    await fetchUsers()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '删除失败')
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
  <div class="users-page">
    <div class="users-head">
      <h2 class="users-title">
        <ElIcon><UserFilled /></ElIcon>
        <span>用户管理</span>
      </h2>
      <NButton type="primary" @click="showCreate = true">新增用户</NButton>
    </div>

    <NCard size="small" style="margin-bottom: 12px">
      <NSpace wrap>
        <NInput
          v-model:value="keyword"
          placeholder="用户名/邮箱搜索"
          clearable
          style="width: 220px"
          @keydown.enter="fetchUsers(true)"
        />
        <NSelect v-model:value="roleFilter" :options="roleFilterOptions" style="width: 160px" />
        <NSelect v-model:value="activeFilter" :options="activeFilterOptions" style="width: 140px" />
        <NButton @click="fetchUsers(true)">查询</NButton>
      </NSpace>
    </NCard>

    <NSpin :show="loading">
      <NCard v-for="item in users" :key="item.id" size="small" class="user-card" hoverable>
        <div class="user-row">
          <div class="user-main">
            <div class="user-line">
              <strong>{{ item.username }}</strong>
              <NTag :type="roleTagType[item.role]">{{ roleLabel[item.role] }}</NTag>
              <NTag :type="item.is_active ? 'success' : 'default'">{{ item.is_active ? '启用' : '禁用' }}</NTag>
              <NTag v-if="item.id === currentUserId" type="info">当前账号</NTag>
            </div>
            <div class="user-meta">{{ item.email }}</div>
            <div class="user-meta">创建时间：{{ formatDate(item.created_at) }}</div>
          </div>
          <NSpace size="small">
            <NButton size="small" @click="openEdit(item)">编辑</NButton>
            <NButton size="small" @click="openPassword(item)">重置密码</NButton>
            <NPopconfirm @positive-click="handleDelete(item.id)">
              <template #trigger>
                <NButton size="small" type="error" quaternary :disabled="item.id === currentUserId">
                  删除
                </NButton>
              </template>
              确认删除该用户？
            </NPopconfirm>
          </NSpace>
        </div>
      </NCard>
    </NSpin>

    <div class="pager">
      <NPagination
        v-model:page="page"
        v-model:page-size="pageSize"
        :item-count="total"
        :page-sizes="[10, 20, 50]"
        show-size-picker
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </div>

    <NModal v-model:show="showCreate" preset="card" title="新增用户" style="width: 520px; max-width: 96vw">
      <NForm @submit.prevent="handleCreate">
        <NFormItem label="用户名">
          <NInput v-model:value="createForm.username" />
        </NFormItem>
        <NFormItem label="邮箱">
          <NInput v-model:value="createForm.email" />
        </NFormItem>
        <NFormItem label="初始密码">
          <NInput v-model:value="createForm.password" type="password" show-password-on="click" />
        </NFormItem>
        <NFormItem label="角色">
          <NSelect v-model:value="createForm.role" :options="roleOptions" />
        </NFormItem>
        <NFormItem label="启用">
          <NSwitch v-model:value="createForm.is_active" />
        </NFormItem>
        <NFormItem label="头像链接">
          <NInput v-model:value="createForm.avatar_url" />
        </NFormItem>
        <NFormItem label="简介">
          <NInput v-model:value="createForm.bio" type="textarea" />
        </NFormItem>
        <NButton type="primary" block attr-type="submit" :loading="creating">创建</NButton>
      </NForm>
    </NModal>

    <NModal v-model:show="showEdit" preset="card" title="编辑用户" style="width: 520px; max-width: 96vw">
      <NForm @submit.prevent="handleEdit">
        <NFormItem label="用户名">
          <NInput v-model:value="editForm.username" />
        </NFormItem>
        <NFormItem label="邮箱">
          <NInput v-model:value="editForm.email" />
        </NFormItem>
        <NFormItem label="角色">
          <NSelect v-model:value="editForm.role" :options="roleOptions" :disabled="editingIsSelf || editingIsOtherSuperAdmin" />
        </NFormItem>
        <NFormItem label="启用">
          <NSwitch v-model:value="editForm.is_active" :disabled="editingIsSelf || editingIsOtherSuperAdmin" />
        </NFormItem>
        <NFormItem label="头像链接">
          <NInput v-model:value="editForm.avatar_url" />
        </NFormItem>
        <NFormItem label="简介">
          <NInput v-model:value="editForm.bio" type="textarea" />
        </NFormItem>
        <NButton type="primary" block attr-type="submit" :loading="editing">保存</NButton>
      </NForm>
    </NModal>

    <NModal v-model:show="showPassword" preset="card" title="重置密码" style="width: 420px; max-width: 96vw">
      <NForm @submit.prevent="handlePassword">
        <NFormItem label="新密码">
          <NInput v-model:value="passwordForm.password" type="password" show-password-on="click" />
        </NFormItem>
        <NButton type="primary" block attr-type="submit" :loading="resettingPassword">确认重置</NButton>
      </NForm>
    </NModal>
  </div>
</template>

<style scoped>
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

.user-card + .user-card {
  margin-top: 10px;
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

.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
