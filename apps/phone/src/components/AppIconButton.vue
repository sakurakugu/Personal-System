<script setup lang="ts">
import { ElButton } from 'element-plus'

interface Props {
  label: string
  disabled?: boolean
  size?: 'md' | 'sm'
}

withDefaults(defineProps<Props>(), {
  disabled: false,
  size: 'md',
})

const emit = defineEmits<{
  click: [event: globalThis.MouseEvent]
}>()
</script>

<template>
  <ElButton
    class="app-icon-button"
    :class="`app-icon-button--${size}`"
    :disabled="disabled"
    :aria-label="label"
    @click="emit('click', $event)"
  >
    <slot />
  </ElButton>
</template>

<style scoped>
.app-icon-button {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  width: 42px;
  height: 42px;
  padding: 0;
  border: 1px solid rgba(180, 83, 9, 0.14);
  border-radius: 14px;
  color: #92400e;
  background: rgba(255, 247, 237, 0.92);
  box-shadow: none;
}

.app-icon-button:hover {
  color: #7c2d12;
  background: rgba(255, 243, 224, 0.96);
}

.app-icon-button:disabled {
  opacity: 0.6;
}

.app-icon-button--sm {
  min-width: 40px;
  width: 40px;
  height: 40px;
}

.app-icon-button :deep(.el-icon),
.app-icon-button :deep(svg) {
  width: 20px;
  height: 20px;
  color: currentColor;
  fill: currentColor;
}

.app-icon-button--sm :deep(.el-icon),
.app-icon-button--sm :deep(svg) {
  width: 18px;
  height: 18px;
}
</style>
