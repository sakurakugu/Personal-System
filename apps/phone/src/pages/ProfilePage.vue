<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@personal-system/domain/auth'

const auth = useAuthStore()
const router = useRouter()
const loading = ref(false)

async function handleLogout() {
  loading.value = true
  try {
    await auth.logout()
    await router.replace('/login')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">我的</p>
        <h1 class="page-title">账号信息</h1>
      </div>
    </header>

    <div class="stack">
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
          <span class="info-label">角色</span>
          <strong>{{ auth.userRole }}</strong>
        </div>
      </section>

      <button class="primary-button primary-button--danger" type="button" :disabled="loading" @click="handleLogout">
        {{ loading ? '退出中…' : '退出登录' }}
      </button>
    </div>
  </section>
</template>
