<script setup lang="ts">
import type { AppTabDefinition } from '../tab-bar'

const props = defineProps<{
  items: AppTabDefinition[]
}>()
</script>

<template>
  <nav
    class="tabbar"
    :style="{
      gridTemplateColumns: `repeat(${props.items.length}, minmax(0, 1fr))`,
    }"
  >
    <RouterLink
      v-for="tab in props.items"
      :key="tab.to"
      :to="tab.to"
      class="tabbar-link"
      exact-active-class="tabbar-link--active"
    >
      <span class="tabbar-link__icon">
        <component :is="tab.icon" />
      </span>
      <span class="tabbar-link__label">{{ tab.label }}</span>
    </RouterLink>
  </nav>
</template>

<style scoped>
.tabbar {
  flex-shrink: 0;
  z-index: 10;
  display: grid;
  min-height: calc(64px + env(safe-area-inset-bottom));
  padding: 8px 8px calc(8px + env(safe-area-inset-bottom));
  background: var(--theme-tabbar-bg);
  backdrop-filter: blur(16px);
  border-top: 1px solid var(--theme-tabbar-border);
}

.tabbar-link {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  min-height: 48px;
  color: var(--text-tertiary);
  font-size: 12px;
  font-weight: 600;
  line-height: 1.2;
  text-decoration: none;
  transition:
    color 0.2s ease,
    transform 0.2s ease;
}

.tabbar-link__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
}

.tabbar-link__icon :deep(svg) {
  width: 22px;
  height: 22px;
}

.tabbar-link__label {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.tabbar-link--active {
  color: var(--el-color-primary);
}

.tabbar-link:active {
  transform: translateY(1px);
}
</style>
