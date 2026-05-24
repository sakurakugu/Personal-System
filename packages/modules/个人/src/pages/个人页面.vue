<script setup lang="ts">
import { SwitchButton, User, Warning } from '@element-plus/icons-vue'
import { 使用认证存储 } from '@personal-system/domain/auth'
import { BaseDialog, PageSectionShell, UniversalAvatar } from '@personal-system/ui'
import {
  ElButton,
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElMessage,
  ElSkeleton,
  ElTag,
  ElText,
} from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { type RouteLocationRaw, useRouter } from 'vue-router'
import { 格式化个人资料日期时间, 获取个人资料账户状态标签, 获取个人资料角色显示 } from '../display'
import { 使用个人资料编辑器 } from '../使用个人资料编辑器'

interface ProfilePageProps {
  onSessionEnded?: () => void | Promise<void>
  sessionEndRedirect?: RouteLocationRaw
}

const props = withDefaults(defineProps<ProfilePageProps>(), {
  onSessionEnded: undefined,
  sessionEndRedirect: () => ({ path: '/' }),
})

const router = useRouter()
const auth = 使用认证存储()
const loading = ref(true)
const loggingOut = ref(false)
const roleDisplay = computed(() => 获取个人资料角色显示(auth.user?.role))
const accountStatus = computed(() => 获取个人资料账户状态标签(auth.user?.is_active))
const {
  avatarPreviewUrl,
  canDeleteAccount,
  changePassword,
  deleteAccount,
  deleteAccountForm,
  deleteDialogVisible,
  deletingAccount,
  emailInvalid,
  openDeleteDialog,
  passwordForm,
  profileForm,
  saveProfile,
  savingPassword,
  savingProfile,
  syncFormFromUser,
} = 使用个人资料编辑器({
  notifier: {
    error: (message) => ElMessage.error(message),
    success: (message) => ElMessage.success(message),
  },
})

onMounted(async () => {
  try {
    await auth.需要时恢复用户()
    syncFormFromUser()
  } finally {
    loading.value = false
  }
})

async function finishSessionFlow() {
  await props.onSessionEnded?.()
  await router.replace(props.sessionEndRedirect)
}

async function handleLogout() {
  loggingOut.value = true
  let errorMessage = ''
  try {
    try {
      await auth.登出()
    } catch (error: any) {
      errorMessage = error?.response?.data?.detail || '退出登录失败'
    }
    await finishSessionFlow()
    if (errorMessage) {
      ElMessage.error(errorMessage)
    }
  } finally {
    loggingOut.value = false
  }
}

async function handleChangePassword() {
  const succeeded = await changePassword()
  if (succeeded) {
    await finishSessionFlow()
  }
}

async function handleDeleteAccount() {
  const succeeded = await deleteAccount()
  if (succeeded) {
    await finishSessionFlow()
  }
}
</script>

<template>
  <div class="page-container">
    <PageSectionShell title="个人资料" :icon="User" title-tag="h2">
      <ElSkeleton :loading="loading" animated>
        <ElCard header="基础信息">
          <div class="avatar-block">
            <UniversalAvatar
              :src="avatarPreviewUrl"
              :text="(profileForm.nickname || profileForm.username || 'U').charAt(0)"
              :size="72"
              alt="头像预览"
              class="avatar-preview"
              background="var(--theme-accent-gradient)"
            />
            <div class="avatar-block__content">
              <div class="avatar-block__title">头像</div>
              <ElInput v-model="profileForm.avatar_url" placeholder="请输入头像链接" />
            </div>
          </div>

          <ElForm label-width="100px" class="profile-form" @submit.prevent="saveProfile">
            <ElFormItem label="用户名">
              <ElInput v-model="profileForm.username" />
            </ElFormItem>
            <ElFormItem label="昵称">
              <ElInput v-model="profileForm.nickname" />
            </ElFormItem>
            <ElFormItem label="邮箱">
              <ElInput v-model="profileForm.email" />
              <ElText v-if="emailInvalid" type="danger" class="field-tip">邮箱格式不正确</ElText>
            </ElFormItem>
            <ElFormItem label="简介">
              <ElInput v-model="profileForm.bio" type="textarea" :rows="4" />
            </ElFormItem>
            <div class="form-actions">
              <ElButton type="primary" native-type="submit" :loading="savingProfile">保存资料</ElButton>
            </div>
          </ElForm>
        </ElCard>

        <ElCard header="安全设置" class="section-card">
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
            <div class="form-actions">
              <ElButton type="primary" native-type="submit" :loading="savingPassword">
                更新密码
              </ElButton>
            </div>
          </ElForm>
        </ElCard>

        <ElCard v-if="canDeleteAccount" header="危险区域" class="section-card">
          <div class="danger-row">
            <div>
              <div class="danger-title">注销账户</div>
              <ElText type="info">注销后，您的所有数据将被永久删除，无法恢复</ElText>
            </div>
            <ElButton type="danger" @click="openDeleteDialog">注销账户</ElButton>
          </div>
        </ElCard>

        <ElCard header="账户信息" class="section-card">
          <ElDescriptions :column="1" border class="account-overview">
            <ElDescriptionsItem label="角色">
              <ElTag :type="roleDisplay.badgeType" effect="plain">
                {{ roleDisplay.label }}
              </ElTag>
            </ElDescriptionsItem>
            <ElDescriptionsItem label="账户状态">
              <ElTag :type="auth.user?.is_active === false ? 'danger' : 'success'" effect="plain">
                {{ accountStatus }}
              </ElTag>
            </ElDescriptionsItem>
            <ElDescriptionsItem label="注册时间">
              {{ 格式化个人资料日期时间(auth.user?.created_at) }}
            </ElDescriptionsItem>
          </ElDescriptions>
          <div class="account-actions">
            <ElButton plain :icon="SwitchButton" :loading="loggingOut" @click="handleLogout">
              {{ loggingOut ? '退出中' : '退出登录' }}
            </ElButton>
          </div>
        </ElCard>
      </ElSkeleton>
    </PageSectionShell>

    <BaseDialog
      v-model="deleteDialogVisible"
      title="确认注销账户"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="delete-dialog-tip">
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

.section-card {
  margin-top: 16px;
}

.avatar-block {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
  margin-bottom: 24px;
}

.avatar-block__content {
  display: grid;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.avatar-block__title {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.avatar-preview {
  flex-shrink: 0;
}

.profile-form {
  width: 100%;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}

.field-tip {
  margin-top: 6px;
}

.account-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.danger-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.danger-title {
  margin-bottom: 4px;
  font-weight: 500;
}

.delete-dialog-tip {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

:deep(.el-card) {
  border-radius: 12px;
}

@media (max-width: 900px) {
  .account-overview {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .page-container {
    padding: 16px;
  }

  .avatar-block {
    align-items: stretch;
    flex-direction: column;
  }

  .profile-form {
    max-width: none;
  }

  .account-actions,
  .danger-row {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
