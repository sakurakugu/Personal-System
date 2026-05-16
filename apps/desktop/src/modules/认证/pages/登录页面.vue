<script setup lang="ts">
import { 开发者登录操作 } from '@/modules/认证/lib/dev-login'
import { useApiEnvironmentStore } from '@/shared/stores/api-environment'
import { AuthEntryCard } from '@personal-system/module-auth'
</script>

<template>
  <section class="page auth-page">
    <AuthEntryCard
      :developer-login-actions="开发者登录操作"
      :use-api-environment-store="useApiEnvironmentStore"
    />
  </section>
</template>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  min-height: 100dvh;
  padding: 24px;
}
</style>
