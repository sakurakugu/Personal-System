<script setup lang="ts">
import { User } from '@element-plus/icons-vue'
import { ElCard, ElDescriptions, ElDescriptionsItem, ElIcon, ElTag } from 'element-plus'
import { useAuthStore } from '@personal-system/domain/auth'
import { formatProfileDateTime, getProfileAccountStatusLabel, getProfileRoleDisplay } from '@personal-system/modules/profile'

const auth = useAuthStore()
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
</style>
