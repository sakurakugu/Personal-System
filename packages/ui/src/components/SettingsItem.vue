<script setup lang="ts">
defineSlots<{
  title?: () => unknown
  actions?: () => unknown
  tip?: () => unknown
  default?: () => unknown
}>()
</script>

<template>
  <div class="settings-item">
    <div class="settings-item__header">
      <div class="settings-item__title">
        <slot name="title" />
      </div>
      <div v-if="$slots.actions" class="settings-item__actions">
        <slot name="actions" />
      </div>
    </div>

    <div v-if="$slots.default" class="settings-item__content">
      <slot />
    </div>

    <div v-if="$slots.tip" class="settings-item__tip">
      <slot name="tip" />
    </div>
  </div>
</template>

<style scoped>
.settings-item {
  display: flex;
  flex-direction: column;
}

.settings-item__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.settings-item__title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.settings-item__actions {
  flex: 0 0 auto;
}

.settings-item__content {
  margin-top: 8px;
}

.settings-item__tip {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.6;
  color: #888;
}
</style>
