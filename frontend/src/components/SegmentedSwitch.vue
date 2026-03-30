<script setup lang="ts">
import { computed, type Component } from 'vue'

type 分段值类型 = string | number

interface 分段选项 {
  label: string
  value: 分段值类型
  disabled?: boolean
  icon?: Component
  title?: string
}

const props = withDefaults(defineProps<{
  modelValue: 分段值类型
  options: readonly 分段选项[]
  ariaLabel?: string
  fullWidth?: boolean
  activeColor?: string
  activeTextColor?: string
  size?: 'default' | 'small'
}>(), {
  ariaLabel: '分段切换',
  fullWidth: false,
  activeColor: 'var(--el-color-primary)',
  activeTextColor: '#fff',
  size: 'default',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: 分段值类型): void
  (e: 'change', value: 分段值类型): void
}>()

const 组件样式 = computed(() => ({
  '--segmented-active-color': props.activeColor,
  '--segmented-active-text-color': props.activeTextColor,
}))

function 选择选项(value: 分段值类型, disabled?: boolean) {
  if (disabled || value === props.modelValue) {
    return
  }
  emit('update:modelValue', value)
  emit('change', value)
}
</script>

<template>
  <div
    class="segmented-switch"
    :class="{
      'segmented-switch--full': fullWidth,
      'segmented-switch--small': size === 'small',
    }"
    :style="组件样式"
    role="radiogroup"
    :aria-label="ariaLabel"
  >
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      class="segmented-switch__option"
      :class="{
        'is-active': modelValue === option.value,
        'is-disabled': option.disabled,
        'is-icon-only': option.icon && !option.label,
      }"
      :aria-checked="modelValue === option.value"
      :title="option.title || option.label"
      :disabled="option.disabled"
      role="radio"
      @click="选择选项(option.value, option.disabled)"
    >
      <component :is="option.icon" v-if="option.icon" class="segmented-switch__icon" />
      <span v-if="option.label" class="segmented-switch__label">{{ option.label }}</span>
    </button>
  </div>
</template>

<style scoped>
.segmented-switch {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--el-border-color, var(--border-color));
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-fill-color-blank, #fff);
}

.segmented-switch--full {
  display: flex;
  width: 100%;
}

.segmented-switch__option {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border: none;
  border-right: 1px solid var(--el-border-color, var(--border-color));
  background: transparent;
  color: var(--el-text-color-regular, var(--text-secondary));
  font-size: 14px;
  line-height: 1.2;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.segmented-switch--small .segmented-switch__option {
  padding: 6px 12px;
  font-size: 13px;
}

.segmented-switch--full .segmented-switch__option {
  flex: 1;
  min-width: 0;
}

.segmented-switch__option:last-child {
  border-right: none;
}

.segmented-switch__option.is-icon-only {
  min-width: 40px;
  padding-inline: 10px;
}

.segmented-switch__option:hover {
  color: var(--el-color-primary);
  background: var(--el-fill-color-light, #f5f7fa);
}

.segmented-switch__option:focus-visible {
  position: relative;
  z-index: 1;
  outline: 2px solid var(--segmented-active-color);
  outline-offset: -2px;
}

.segmented-switch__option.is-active {
  background: var(--segmented-active-color);
  color: var(--segmented-active-text-color);
}

.segmented-switch__option.is-disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.segmented-switch__icon {
  width: 1em;
  height: 1em;
  flex-shrink: 0;
}

.segmented-switch__label {
  min-width: 0;
}

.segmented-switch__icon + .segmented-switch__label {
  margin-left: 6px;
}

:global(.dark .segmented-switch) {
  background: var(--bg-secondary);
  border-color: var(--border-color);
}

:global(.dark .segmented-switch__option) {
  border-right-color: var(--border-color);
  color: var(--text-secondary);
}

:global(.dark .segmented-switch__option:hover) {
  background: var(--bg-hover);
  color: var(--text-primary);
}

:global(.dark .segmented-switch__option.is-active) {
  color: var(--segmented-active-text-color);
  background: var(--segmented-active-color);
}
</style>
