<script setup lang="ts">
import { ElCard } from 'element-plus'

defineProps<{
  header: string
}>()
</script>

<template>
  <ElCard class="settings-section-card" :header="header" :body-style="{ padding: '16px 20px' }">
    <div class="settings-section-card__list">
      <slot />
    </div>
  </ElCard>
</template>

<style scoped>
.settings-section-card + .settings-section-card {
  margin-top: 16px;
}

.settings-section-card :deep(.el-card__header) {
  padding: 12px 20px;
}

.settings-section-card__list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
