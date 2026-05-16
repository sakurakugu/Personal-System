<script setup lang="ts">
import { getPhoneRoleProfile } from '@/modules/认证/lib/role'
import ProfileSubpageHeader from '@/modules/个人/components/个人子页面标题.vue'
import { useAuthStore } from '@personal-system/domain/auth'
import { computed } from 'vue'

const auth = useAuthStore()
const roleProfile = computed(() => getPhoneRoleProfile(auth.user?.role))
</script>

<template>
  <section class="page">
    <ProfileSubpageHeader
      title="基本资料"
      to="/me/account"
    />

    <section class="panel-card">
      <div class="info-row">
        <span class="info-label">用户名</span>
        <strong>{{ auth.user?.username || '-' }}</strong>
      </div>
      <div class="info-row">
        <span class="info-label">昵称</span>
        <strong>{{ auth.user?.nickname || '未设置' }}</strong>
      </div>
      <div class="info-row">
        <span class="info-label">邮箱</span>
        <strong>{{ auth.user?.email || '-' }}</strong>
      </div>
      <div class="info-row">
        <span class="info-label">角色标识</span>
        <strong>{{ auth.user?.role || '-' }}</strong>
      </div>
      <div class="info-row">
        <span class="info-label">角色名称</span>
        <strong>{{ roleProfile.label }}</strong>
      </div>
    </section>
  </section>
</template>

<style scoped>
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.info-row + .info-row {
  margin-top: 16px;
}

.info-label {
  color: var(--text-tertiary);
}

@media (max-width: 480px) {
  .info-row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
