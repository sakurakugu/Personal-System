<script setup lang="ts">
import { ArrowRightBold } from '@element-plus/icons-vue'
import type { Component } from 'vue'

interface Props {
  title: string
  to: string
  icon: Component
  value?: string
}

withDefaults(defineProps<Props>(), {
  value: '',
})
</script>

<template>
  <RouterLink class="profile-entry-card" :to="to">
    <span class="profile-entry-card__icon">
      <component :is="icon" />
    </span>

    <div class="profile-entry-card__content">
      <div class="profile-entry-card__heading">
        <strong>{{ title }}</strong>
        <span v-if="value" class="profile-entry-card__value">{{ value }}</span>
      </div>
    </div>

    <span class="profile-entry-card__arrow">
      <ArrowRightBold />
    </span>
  </RouterLink>
</template>

<style scoped>
.profile-entry-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  text-decoration: none;
  color: inherit;
}

.profile-entry-card__icon,
.profile-entry-card__arrow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.profile-entry-card__icon {
  color: var(--theme-accent-strong);
}

.profile-entry-card__arrow {
  color: var(--text-tertiary);
}

.profile-entry-card__icon :deep(svg),
.profile-entry-card__arrow :deep(svg) {
  width: 18px;
  height: 18px;
  color: currentColor;
  fill: currentColor;
}

.profile-entry-card__content {
  min-width: 0;
}

.profile-entry-card__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.profile-entry-card__value {
  color: var(--theme-accent-strong);
  font-size: 0.92rem;
  white-space: nowrap;
}

</style>
