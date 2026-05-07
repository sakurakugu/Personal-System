<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElAvatar, ElButton, ElCard, ElForm, ElFormItem, ElIcon, ElInput, ElMessage, ElSkeleton, ElText } from 'element-plus'
import { User, Warning } from '@element-plus/icons-vue'
import { useAuthStore } from '../../store'
import { useProfileEditor } from '@personal-system/modules/profile'
import { BaseDialog } from '@personal-system/ui'

const auth = useAuthStore()
const loading = ref(true)
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
} = useProfileEditor({
  notifier: {
    error: (message) => ElMessage.error(message),
    success: (message) => ElMessage.success(message),
  },
})

onMounted(async () => {
  try {
    await auth.restoreUserIfNeeded()
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
        <ElForm label-width="100px" @submit.prevent="saveProfile">
          <ElFormItem label="头像" class="avatar-form-item">
            <div class="avatar-input-row">
              <ElAvatar
                v-if="avatarPreviewUrl"
                :src="avatarPreviewUrl"
                :size="64"
                class="avatar-preview"
                :style="{ background: 'var(--theme-accent-gradient)' }"
              >
                {{ (profileForm.nickname || profileForm.username || 'U').charAt(0).toUpperCase() }}
              </ElAvatar>
              <ElAvatar v-else :size="64" class="avatar-preview" :style="{ background: 'var(--theme-accent-gradient)' }">
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
            <ElText v-if="emailInvalid" type="danger" style="margin-top: 6px">邮箱格式不正确</ElText>
          </ElFormItem>
          <ElFormItem label="简介">
            <ElInput v-model="profileForm.bio" type="textarea" />
          </ElFormItem>
          <ElButton type="primary" native-type="submit" :loading="savingProfile" @click="saveProfile">保存资料</ElButton>
        </ElForm>
      </ElCard>
      <ElCard header="修改密码" style="margin-top: 16px">
        <ElForm label-width="100px" @submit.prevent="changePassword">
          <ElFormItem label="当前密码">
            <ElInput v-model="passwordForm.current_password" type="password" show-password />
          </ElFormItem>
          <ElFormItem label="新密码">
            <ElInput v-model="passwordForm.new_password" type="password" show-password />
          </ElFormItem>
          <ElFormItem label="确认新密码">
            <ElInput v-model="passwordForm.confirm_password" type="password" show-password />
          </ElFormItem>
          <ElButton type="primary" native-type="submit" :loading="savingPassword" @click="changePassword">更新密码</ElButton>
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
      <ElForm @submit.prevent="deleteAccount">
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
        <ElButton type="danger" :loading="deletingAccount" @click="deleteAccount">
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
