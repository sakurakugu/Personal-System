<script setup lang="ts">
import ProfileSubpageHeader from '@/modules/profile/components/ProfileSubpageHeader.vue'
import { getPhoneRoleProfile } from '@/modules/auth/lib/role'
import { useAuthStore } from '@personal-system/domain/auth'
import { computed } from 'vue'

const auth = useAuthStore()
const roleProfile = computed(() => getPhoneRoleProfile(auth.user?.role))
</script>

<template>
  <section class="page">
    <ProfileSubpageHeader
      eyebrow="资料"
      title="基本资料"
      description="基础账号字段独立放在这一层，避免账号中心页再次变成信息堆场。"
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
