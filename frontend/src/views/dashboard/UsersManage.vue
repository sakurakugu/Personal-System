<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  ElButton,
  ElCard,
  ElDialog,
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
import { UserFilled } from '@element-plus/icons-vue'
import api from '../../utils/api'
import { useAuthStore } from '../../stores/auth'

interface UserItem {
  id: string
  username: string
  nickname: string | null
  email: string
  role: 'user' | 'admin' | 'super_admin'
  avatar_url: string | null
  bio: string | null
  is_active: boolean
  created_at: string
}

const auth = useAuthStore()
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
  nickname: '',
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
  nickname: '',
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
const editingIsSelf = computed(() => editingUserId.value === currentUserId.value)
const editingIsOtherSuperAdmin = computed(
  () => editingUserRole.value === 'super_admin' && !editingIsSelf.value,
)

function resetCreateForm() {
  createForm.value = {
    username: '',
    nickname: '',
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
    ElMessage.error('请填写完整信息')
    return
  }
  creating.value = true
  try {
    await api.post('/users', {
      username: createForm.value.username.trim(),
      nickname: createForm.value.nickname.trim() || null,
      email: createForm.value.email.trim(),
      password: createForm.value.password,
      role: createForm.value.role,
      is_active: createForm.value.is_active,
      bio: createForm.value.bio.trim() || null,
      avatar_url: createForm.value.avatar_url.trim() || null,
    })
    ElMessage.success('用户已创建')
    showCreate.value = false
    resetCreateForm()
    await fetchUsers()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

function openEdit(user: UserItem) {
  editingUserId.value = user.id
  editingUserRole.value = user.role
  editForm.value = {
    username: user.username,
    nickname: user.nickname || '',
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
      nickname: editForm.value.nickname.trim() || null,
      email: editForm.value.email.trim(),
      role: editForm.value.role,
      is_active: editForm.value.is_active,
      bio: editForm.value.bio.trim() || null,
      avatar_url: editForm.value.avatar_url.trim() || null,
    })
    ElMessage.success('用户信息已更新')
    showEdit.value = false
    await fetchUsers()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '更新失败')
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
    ElMessage.error('请输入新密码')
    return
  }
  resettingPassword.value = true
  try {
    await api.patch(`/users/${passwordUserId.value}/password`, {
      password: passwordForm.value.password,
    })
    ElMessage.success('密码已重置')
    showPassword.value = false
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '重置失败')
  } finally {
    resettingPassword.value = false
  }
}

async function handleDelete(userId: string) {
  try {
    await api.delete(`/users/${userId}`)
    ElMessage.success('用户已删除')
    if (users.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    await fetchUsers()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
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
        <ElSelect v-model="roleFilter" style="width: 160px">
          <ElOption v-for="item in roleFilterOptions" :key="item.value" :label="item.label" :value="item.value" />
        </ElSelect>
        <ElSelect v-model="activeFilter" style="width: 140px">
          <ElOption v-for="item in activeFilterOptions" :key="item.value" :label="item.label" :value="item.value" />
        </ElSelect>
        <ElButton @click="fetchUsers(true)">查询</ElButton>
      </ElSpace>
    </ElCard>

    <ElSkeleton :loading="loading" animated>
      <ElCard v-for="item in users" :key="item.id" class="user-card" shadow="hover">
        <div class="user-row">
          <div class="user-main">
            <div class="user-line">
              <strong>{{ item.nickname || item.username }}</strong>
              <ElTag :type="roleTagType[item.role]">{{ roleLabel[item.role] }}</ElTag>
              <ElTag :type="item.is_active ? 'success' : 'info'">{{ item.is_active ? '启用' : '禁用' }}</ElTag>
              <ElTag v-if="item.id === currentUserId" type="primary">当前账号</ElTag>
            </div>
            <div class="user-meta">{{ item.email }}</div>
            <div class="user-meta">创建时间：{{ formatDate(item.created_at) }}</div>
          </div>
          <ElSpace size="small">
            <ElButton size="small" @click="openEdit(item)">编辑</ElButton>
            <ElButton size="small" @click="openPassword(item)">重置密码</ElButton>
            <ElPopconfirm @confirm="handleDelete(item.id)">
              <template #reference>
                <ElButton size="small" type="danger" text :disabled="item.id === currentUserId">
                  删除
                </ElButton>
              </template>
              确认删除该用户？
            </ElPopconfirm>
          </ElSpace>
        </div>
      </ElCard>
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

    <ElDialog :model-value="showCreate" title="新增用户" width="520px" style="max-width: 96vw" @update:model-value="showCreate = $event">
      <ElForm @submit.prevent="handleCreate">
        <ElFormItem label="用户名">
          <ElInput v-model="createForm.username" />
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
    </ElDialog>

    <ElDialog :model-value="showEdit" title="编辑用户" width="520px" style="max-width: 96vw" @update:model-value="showEdit = $event">
      <ElForm @submit.prevent="handleEdit">
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
    </ElDialog>

    <ElDialog :model-value="showPassword" title="重置密码" width="420px" style="max-width: 96vw" @update:model-value="showPassword = $event">
      <ElForm @submit.prevent="handlePassword">
        <ElFormItem label="新密码">
          <ElInput v-model="passwordForm.password" type="password" show-password />
        </ElFormItem>
        <ElButton type="primary" style="width: 100%" native-type="submit" :loading="resettingPassword">确认重置</ElButton>
      </ElForm>
    </ElDialog>
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

.dark .user-meta {
  color: var(--text-tertiary);
}

.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
