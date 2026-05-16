<script setup lang="ts">
import { developerLoginActions } from '@/modules/认证/lib/dev-login'
import { useApiEnvironmentStore } from '@/shared/stores/api-environment'
import { AuthEntryCard } from '@personal-system/module-auth'
</script>

<template>
  <section class="page auth-page">
    <AuthEntryCard
      :developer-login-actions="developerLoginActions"
      settings-panel-class="stack"
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
  padding-top: 24px;
  padding-bottom: 24px;
}
</style>
