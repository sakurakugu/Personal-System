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
      eyebrow="角色"
      title="角色能力"
      description="角色说明和能力列表单独成页，后续继续扩展权限说明也不会挤回账号页。"
      to="/me/account"
    />

    <section class="panel-card stack">
      <div>
        <span class="info-label">角色说明</span>
        <strong class="section-title">{{ roleProfile.summary }}</strong>
      </div>
      <div class="capability-list">
        <article v-for="item in roleProfile.capabilities" :key="item.title" class="capability-card">
          <strong>{{ item.title }}</strong>
          <p>{{ item.description }}</p>
        </article>
      </div>
      <p v-if="roleProfile.managementNotice" class="panel-meta panel-note">
        {{ roleProfile.managementNotice }}
      </p>
    </section>
  </section>
</template>

<style scoped>
.info-label {
  color: var(--text-tertiary);
}
</style>
