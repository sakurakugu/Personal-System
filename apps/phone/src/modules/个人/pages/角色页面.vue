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
      title="角色能力"
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
