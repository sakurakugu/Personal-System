<script setup lang="ts">
import { developerLoginActions } from '@/modules/auth/lib/dev-login'
import { useApiEnvironmentStore } from '@/shared/stores/api-environment'
import { AuthEntryCard } from '@personal-system/module-auth'
</script>

<template>
  <section class="page auth-page">
    <AuthEntryCard
      :developer-login-actions="developerLoginActions"
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
