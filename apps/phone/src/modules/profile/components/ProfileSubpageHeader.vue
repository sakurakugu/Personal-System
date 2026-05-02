<script setup lang="ts">
import AppIconButton from '@/shared/components/AppIconButton.vue'
import { ArrowLeftBold } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

interface Props {
  eyebrow: string
  title: string
  description?: string
  to?: string
}

const props = withDefaults(defineProps<Props>(), {
  description: '',
  to: '/me',
})

const router = useRouter()

function handleBack() {
  void router.push(props.to)
}
</script>

<template>
  <header class="profile-subpage-header">
    <AppIconButton label="返回上一层" @click="handleBack">
      <ArrowLeftBold />
    </AppIconButton>

    <div class="profile-subpage-header__content">
      <p class="eyebrow">{{ eyebrow }}</p>
      <h1 class="page-title">{{ title }}</h1>
      <p v-if="description" class="profile-subpage-header__description">{{ description }}</p>
    </div>
  </header>
</template>

<style scoped>
.profile-subpage-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 18px;
}

.profile-subpage-header__content {
  min-width: 0;
  flex: 1;
}

.profile-subpage-header__description {
  margin: 10px 0 0;
  color: var(--text-tertiary);
}
</style>
