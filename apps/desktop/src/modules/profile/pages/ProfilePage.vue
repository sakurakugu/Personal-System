<script setup lang="ts">
import { User } from '@element-plus/icons-vue'
import { ElCard, ElDescriptions, ElDescriptionsItem, ElIcon, ElTag } from 'element-plus'
import { computed } from 'vue'
import { useAuthStore } from '@personal-system/domain/auth'

const auth = useAuthStore()

const roleLabel = computed(() => {
  if (auth.user?.role === 'super_admin') {
    return '超级管理员'
  }
  if (auth.user?.role === 'admin') {
    return '管理员'
  }
  return '普通用户'
})
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
          <ElTag type="primary" effect="plain">{{ roleLabel }}</ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem label="账户状态">
          <ElTag :type="auth.user?.is_active === false ? 'danger' : 'success'" effect="plain">
            {{ auth.user?.is_active === false ? '已停用' : '正常' }}
          </ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem label="注册时间">
          {{ auth.user?.created_at ? new Date(auth.user.created_at).toLocaleString('zh-CN', { hour12: false }) : '未知' }}
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
