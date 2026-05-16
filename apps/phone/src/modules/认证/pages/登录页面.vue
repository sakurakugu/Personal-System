<script setup lang="ts">
import { 开发者登录操作 } from '@/modules/认证/lib/dev-login'
import { 使用API环境存储 } from '@/shared/stores/api-environment'
import { AuthEntryCard } from '@personal-system/module-auth'
</script>

<template>
  <section class="page auth-page">
    <AuthEntryCard
      :developer-login-actions="开发者登录操作"
      settings-panel-class="stack"
      :使用-api-环境-存储="使用API环境存储"
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
