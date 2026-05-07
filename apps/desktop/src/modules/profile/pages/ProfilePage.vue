<script setup lang="ts">
import { SwitchButton, User } from '@element-plus/icons-vue'
import { ElButton, ElCard, ElDescriptions, ElDescriptionsItem, ElIcon, ElMessage, ElTag } from 'element-plus'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@personal-system/domain/auth'
import { formatProfileDateTime, getProfileAccountStatusLabel, getProfileRoleDisplay } from '@personal-system/modules/profile'

const auth = useAuthStore()
const router = useRouter()
const loggingOut = ref(false)

async function handleLogout() {
  loggingOut.value = true
  let errorMessage = ''
  try {
    try {
      await auth.logout()
    } catch (error: any) {
      errorMessage = error?.response?.data?.detail || '退出登录失败'
    }
    await router.replace('/login')
    if (errorMessage) {
      ElMessage.error(errorMessage)
    }
  } finally {
    loggingOut.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <h1 class="page-title">
      <ElIcon><User /></ElIcon>
      <span>账户信息</span>
    </h1>

    <ElCard>
      <ElDescriptions :column="2" border>
        <ElDescriptionsItem label="用户名">
          {{ auth.user?.username || '未知' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem label="昵称">
          {{ auth.user?.nickname || '未设置' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem label="邮箱">
          {{ auth.user?.email || '未设置' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem label="角色">
          <ElTag :type="getProfileRoleDisplay(auth.user?.role).badgeType" effect="plain">
            {{ getProfileRoleDisplay(auth.user?.role).label }}
          </ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem label="账户状态">
          <ElTag :type="auth.user?.is_active === false ? 'danger' : 'success'" effect="plain">
            {{ getProfileAccountStatusLabel(auth.user?.is_active) }}
          </ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem label="注册时间">
          {{ formatProfileDateTime(auth.user?.created_at) }}
        </ElDescriptionsItem>
      </ElDescriptions>

      <div class="profile-actions">
        <ElButton type="danger" :icon="SwitchButton" :loading="loggingOut" @click="handleLogout">
          {{ loggingOut ? '退出中' : '退出登录' }}
        </ElButton>
      </div>
    </ElCard>
  </div>
</template>

<style scoped>
.page-container {
  display: grid;
  gap: 20px;
  padding: 28px;
}

.page-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.profile-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
