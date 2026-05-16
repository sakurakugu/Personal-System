<script setup lang="ts">
import { 获取手机角色配置 } from '@/modules/认证/lib/role'
import ProfileEntryCard from '@/modules/个人/components/个人入口卡片.vue'
import ProfileSubpageHeader from '@/modules/个人/components/个人子页面标题.vue'
import { Document, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@personal-system/domain/auth'
import { 获取个人资料账户状态标签, 获取个人资料显示名称 } from '@personal-system/module-profile'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()
const loading = ref(false)

const roleProfile = computed(() => 获取手机角色配置(auth.user?.role))
const displayName = computed(() => 获取个人资料显示名称(auth.user))
const accountStatus = computed(() => 获取个人资料账户状态标签(auth.user?.is_active))

async function handleLogout() {
  loading.value = true
  try {
    try {
      await auth.登出()
    } catch {
      // 后端不可达时也要允许本地退出并返回首页
    }
    await router.replace('/')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="page">
    <ProfileSubpageHeader
      title="账号中心"
    />

    <div class="stack">
      <section class="panel-card">
        <div class="info-row">
          <span class="info-label">当前账号</span>
          <strong>{{ displayName }}</strong>
        </div>
        <div class="info-row">
          <span class="info-label">账户状态</span>
          <strong>{{ accountStatus }}</strong>
        </div>
        <div class="info-row">
          <span class="info-label">当前角色</span>
          <strong>{{ roleProfile.label }}</strong>
        </div>
      </section>

      <div class="stack">
        <ProfileEntryCard
          title="基本资料"
          description="查看用户名、昵称、邮箱和角色字段，不和能力说明混在一页"
          to="/me/account/details"
          :icon="User"
          :value="auth.user?.username || '-'"
        />

        <ProfileEntryCard
          title="角色能力"
          description="查看当前角色说明、权限能力和管理提示"
          to="/me/account/role"
          :icon="Document"
          :value="roleProfile.label"
        />
      </div>

      <button class="primary-button primary-button--danger" type="button" :disabled="loading" @click="handleLogout">
        {{ loading ? '退出中…' : '退出登录' }}
      </button>
    </div>
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
