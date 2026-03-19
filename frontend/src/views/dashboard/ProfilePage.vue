<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElIcon } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import { NAvatar, NButton, NCard, NForm, NFormItem, NInput, NSpin, NText, useMessage } from 'naive-ui'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const message = useMessage()
const loading = ref(true)
const savingProfile = ref(false)
const savingPassword = ref(false)

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
    message.error('用户名和邮箱不能为空')
    return
  }
  if (emailInvalid.value) {
    message.error('邮箱格式不正确，且不能包含加号')
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
    message.success('个人资料已更新')
  } catch (e: any) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    savingProfile.value = false
  }
}

async function handleChangePassword() {
  if (!passwordForm.value.current_password || !passwordForm.value.new_password || !passwordForm.value.confirm_password) {
    message.error('请填写完整密码信息')
    return
  }
  if (passwordForm.value.new_password.length < 6) {
    message.error('新密码至少 6 位')
    return
  }
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    message.error('两次输入的新密码不一致')
    return
  }
  savingPassword.value = true
  try {
    await auth.changePassword(passwordForm.value.current_password, passwordForm.value.new_password)
    passwordForm.value = { current_password: '', new_password: '', confirm_password: '' }
    message.success('密码修改成功')
  } catch (e: any) {
    message.error(e.response?.data?.detail || '修改密码失败')
  } finally {
    savingPassword.value = false
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
  <div>
    <h2 style="display: inline-flex; align-items: center; gap: 8px; margin-bottom: 24px">
      <ElIcon><User /></ElIcon>
      <span>个人资料</span>
    </h2>
    <NSpin :show="loading">
      <NCard title="基础信息">
        <NForm @submit.prevent="handleSaveProfile">
          <NFormItem label="用户名">
            <NInput v-model:value="profileForm.username" />
          </NFormItem>
          <NFormItem label="昵称">
            <NInput v-model:value="profileForm.nickname" />
          </NFormItem>
          <NFormItem label="邮箱">
            <NInput v-model:value="profileForm.email" />
            <NText v-if="emailInvalid" type="error" style="margin-top: 6px">邮箱格式不正确，且不能包含加号</NText>
          </NFormItem>
          <NFormItem label="头像链接">
            <NInput v-model:value="profileForm.avatar_url" />
            <div style="margin-top: 10px; display: flex; align-items: center; gap: 8px">
              <NAvatar
                v-if="avatarPreviewUrl"
                round
                :src="avatarPreviewUrl"
                :style="{ backgroundColor: '#18a058' }"
              >
                {{ (profileForm.nickname || profileForm.username || 'U').charAt(0).toUpperCase() }}
              </NAvatar>
              <NText depth="3">{{ avatarPreviewUrl ? '头像预览' : '未设置头像' }}</NText>
            </div>
          </NFormItem>
          <NFormItem label="简介">
            <NInput v-model:value="profileForm.bio" type="textarea" />
          </NFormItem>
          <NButton type="primary" attr-type="submit" :loading="savingProfile">保存资料</NButton>
        </NForm>
      </NCard>
      <NCard title="修改密码" style="margin-top: 16px">
        <NForm @submit.prevent="handleChangePassword">
          <NFormItem label="当前密码">
            <NInput v-model:value="passwordForm.current_password" type="password" show-password-on="click" />
          </NFormItem>
          <NFormItem label="新密码">
            <NInput v-model:value="passwordForm.new_password" type="password" show-password-on="click" />
          </NFormItem>
          <NFormItem label="确认新密码">
            <NInput v-model:value="passwordForm.confirm_password" type="password" show-password-on="click" />
          </NFormItem>
          <NButton type="primary" attr-type="submit" :loading="savingPassword">更新密码</NButton>
        </NForm>
      </NCard>
    </NSpin>
  </div>
</template>
