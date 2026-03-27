<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElAvatar, ElButton, ElCard, ElForm, ElFormItem, ElIcon, ElInput, ElMessage, ElSkeleton, ElText } from 'element-plus'
import { User, Warning } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import BaseDialog from '../../components/BaseDialog.vue'

const auth = useAuthStore()
const loading = ref(true)
const savingProfile = ref(false)
const savingPassword = ref(false)
const deletingAccount = ref(false)
const deleteDialogVisible = ref(false)

const profileForm = ref({
  username: '',
  nickname: '',
  email: '',
  avatar_url: '',
  bio: '',
})

const passwordForm = ref({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

const deleteAccountForm = ref({
  password: '',
})

// 是否可以注销账户（超级管理员不能注销自己）
const canDeleteAccount = computed(() => !auth.isSuperAdmin)

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const emailInvalid = computed(() => {
  const value = profileForm.value.email.trim()
  return !!value && (!emailRegex.test(value) || value.includes('+'))
})
const avatarPreviewUrl = computed(() => profileForm.value.avatar_url.trim() || null)

function syncFormFromUser() {
  profileForm.value = {
    username: auth.user?.username || '',
    nickname: auth.user?.nickname || '',
    email: auth.user?.email || '',
    avatar_url: auth.user?.avatar_url || '',
    bio: auth.user?.bio || '',
  }
}

async function handleSaveProfile() {
  if (!profileForm.value.username.trim() || !profileForm.value.email.trim()) {
    ElMessage.error('用户名和邮箱不能为空')
    return
  }
  if (emailInvalid.value) {
    ElMessage.error('邮箱格式不正确，且不能包含加号')
    return
  }
  savingProfile.value = true
  try {
    await auth.updateProfile({
      username: profileForm.value.username.trim(),
      nickname: profileForm.value.nickname.trim() || null,
      email: profileForm.value.email.trim(),
      avatar_url: profileForm.value.avatar_url.trim() || null,
      bio: profileForm.value.bio.trim() || null,
    })
    syncFormFromUser()
    ElMessage.success('个人资料已更新')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    savingProfile.value = false
  }
}

async function handleChangePassword() {
  if (!passwordForm.value.current_password || !passwordForm.value.new_password || !passwordForm.value.confirm_password) {
    ElMessage.error('请填写完整密码信息')
    return
  }
  if (passwordForm.value.new_password.length < 6) {
    ElMessage.error('新密码至少 6 位')
    return
  }
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    ElMessage.error('两次输入的新密码不一致')
    return
  }
  savingPassword.value = true
  try {
    await auth.changePassword(passwordForm.value.current_password, passwordForm.value.new_password)
    passwordForm.value = { current_password: '', new_password: '', confirm_password: '' }
    ElMessage.success('密码修改成功')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '修改密码失败')
  } finally {
    savingPassword.value = false
  }
}

function openDeleteDialog() {
  deleteAccountForm.value = { password: '' }
  deleteDialogVisible.value = true
}

async function handleDeleteAccount() {
  if (!deleteAccountForm.value.password) {
    ElMessage.error('请输入密码')
    return
  }
  deletingAccount.value = true
  try {
    await auth.deleteAccount(deleteAccountForm.value.password)
    deleteDialogVisible.value = false
    ElMessage.success('账户已注销')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '注销账户失败')
  } finally {
    deletingAccount.value = false
  }
}

onMounted(async () => {
  try {
    if (!auth.user) {
      await auth.fetchUser()
    }
    syncFormFromUser()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page-container">
    <h2 style="display: inline-flex; align-items: center; gap: 8px; margin-bottom: 24px">
      <ElIcon><User /></ElIcon>
      <span>个人资料</span>
    </h2>
    <ElSkeleton :loading="loading" animated>
      <ElCard header="基础信息">
        <ElForm label-width="100px" @submit.prevent="handleSaveProfile">
          <ElFormItem label="头像" class="avatar-form-item">
            <div class="avatar-input-row">
              <ElAvatar
                v-if="avatarPreviewUrl"
                :src="avatarPreviewUrl"
                :size="64"
                class="avatar-preview"
                :style="{ backgroundColor: '#18a058' }"
              >
                {{ (profileForm.nickname || profileForm.username || 'U').charAt(0).toUpperCase() }}
              </ElAvatar>
              <ElAvatar v-else :size="64" class="avatar-preview" :style="{ backgroundColor: '#18a058' }">
                {{ (profileForm.nickname || profileForm.username || 'U').charAt(0).toUpperCase() }}
              </ElAvatar>
              <ElInput v-model="profileForm.avatar_url" class="avatar-input" placeholder="请输入头像链接" />
            </div>
          </ElFormItem>
          <ElFormItem label="用户名">
            <ElInput v-model="profileForm.username" />
          </ElFormItem>
          <ElFormItem label="昵称">
            <ElInput v-model="profileForm.nickname" />
          </ElFormItem>
          <ElFormItem label="邮箱">
            <ElInput v-model="profileForm.email" />
            <ElText v-if="emailInvalid" type="danger" style="margin-top: 6px">邮箱格式不正确，且不能包含加号</ElText>
          </ElFormItem>
          <ElFormItem label="简介">
            <ElInput v-model="profileForm.bio" type="textarea" />
          </ElFormItem>
          <ElButton type="primary" native-type="submit" :loading="savingProfile">保存资料</ElButton>
        </ElForm>
      </ElCard>
      <ElCard header="修改密码" style="margin-top: 16px">
        <ElForm label-width="100px" @submit.prevent="handleChangePassword">
          <ElFormItem label="当前密码">
            <ElInput v-model="passwordForm.current_password" type="password" show-password />
          </ElFormItem>
          <ElFormItem label="新密码">
            <ElInput v-model="passwordForm.new_password" type="password" show-password />
          </ElFormItem>
          <ElFormItem label="确认新密码">
            <ElInput v-model="passwordForm.confirm_password" type="password" show-password />
          </ElFormItem>
          <ElButton type="primary" native-type="submit" :loading="savingPassword">更新密码</ElButton>
        </ElForm>
      </ElCard>

      <ElCard v-if="canDeleteAccount" header="危险区域" style="margin-top: 16px">
        <div style="display: flex; align-items: center; justify-content: space-between">
          <div>
            <div style="font-weight: 500; margin-bottom: 4px">注销账户</div>
            <ElText type="info">注销后，您的所有数据将被永久删除，无法恢复</ElText>
          </div>
          <ElButton type="danger" @click="openDeleteDialog">注销账户</ElButton>
        </div>
      </ElCard>
    </ElSkeleton>

    <!-- 注销账户确认对话框 -->
    <BaseDialog
      v-model="deleteDialogVisible"
      title="确认注销账户"
      width="400px"
      :close-on-click-modal="false"
    >
      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px">
        <ElIcon color="#f56c6c" :size="24"><Warning /></ElIcon>
        <span>此操作不可恢复，请谨慎操作</span>
      </div>
      <ElForm @submit.prevent="handleDeleteAccount">
        <ElFormItem>
          <ElInput
            v-model="deleteAccountForm.password"
            type="password"
            placeholder="请输入当前密码确认"
            show-password
          />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="deleteDialogVisible = false">取消</ElButton>
        <ElButton type="danger" :loading="deletingAccount" @click="handleDeleteAccount">
          确认注销
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

:deep(.el-card) {
  border-radius: 12px;
}

.avatar-form-item :deep(.el-form-item__label) {
  display: inline-flex;
  align-items: center;
  min-height: 64px;
}

.avatar-input-row {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.avatar-preview {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  line-height: 1;
  text-align: center;
}

.avatar-input {
  flex: 1;
  min-width: 0;
}
</style>
