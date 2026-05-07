<script setup lang="ts">
import { computed } from 'vue'
import { Icon } from '@iconify/vue'
import { ElSwitch } from 'element-plus'
import type { ThemeMode } from '@personal-system/theme'

const props = withDefaults(defineProps<{
  modelValue: ThemeMode
  isDark: boolean
  title?: string
  compact?: boolean
  showFollowSystemIcon?: boolean
  inlineOptionContent?: boolean
}>(), {
  title: '主题设置',
  compact: false,
  showFollowSystemIcon: false,
  inlineOptionContent: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: ThemeMode]
}>()

const themeModes = [
  { value: 'light', label: '浅色', icon: 'material-symbols:wb-sunny-outline-rounded' },
  { value: 'dark', label: '深色', icon: 'material-symbols:dark-mode-outline-rounded' },
] as const

const followSystem = computed(() => props.modelValue === 'system')

function setMode(mode: ThemeMode) {
  emit('update:modelValue', mode)
}

function handleFollowSystemChange(value: string | number | boolean) {
  if (value === true) {
    emit('update:modelValue', 'system')
    return
  }
  emit('update:modelValue', props.isDark ? 'dark' : 'light')
}
</script>

<template>
  <div class="theme-mode-panel" :class="{ 'theme-mode-panel--compact': props.compact }">
    <div class="theme-title">{{ props.title }}</div>
    <div class="theme-options">
      <button
        v-for="item in themeModes"
        :key="item.value"
        class="theme-option"
        :class="{
          active: props.modelValue === item.value,
          'theme-option--inline': props.inlineOptionContent,
        }"
        type="button"
        @click="setMode(item.value)"
      >
        <Icon :icon="item.icon" class="option-icon" />
        <span>{{ item.label }}</span>
      </button>
    </div>
    <div class="theme-divider" />
    <div class="follow-system-row">
      <Icon
        v-if="props.showFollowSystemIcon"
        icon="material-symbols:brightness-auto-outline-rounded"
        class="row-icon"
      />
      <span class="follow-system-label">跟随系统</span>
      <ElSwitch
        :model-value="followSystem"
        @update:model-value="handleFollowSystemChange"
      />
    </div>
  </div>
</template>

<style scoped>
.theme-mode-panel {
  padding: 8px 12px;
  min-width: 140px;
}

.theme-mode-panel--compact {
  padding: 0;
}

.theme-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  margin-left: 12px;
  position: relative;
  font-size: 18px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.9);
}

.theme-title::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -12px;
  width: 4px;
  height: 16px;
  border-radius: 4px;
  background: var(--theme-hue-title-accent, var(--header-accent-soft, var(--el-color-primary-light-3)));
  transform: translateY(-50%);
}

.theme-options {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.theme-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px;
  border: 1px solid var(--theme-card-border, var(--el-border-color));
  border-radius: 6px;
  background: transparent;
  color: var(--el-text-color-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.theme-option:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

.theme-option.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.option-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
  color: var(--el-color-primary);
}

.theme-option span {
  font-size: 12px;
}

.theme-option--inline {
  flex-direction: row;
  gap: 6px;
}

.theme-divider {
  height: 1px;
  margin: 8px 0;
  background: var(--theme-card-border, var(--el-border-color));
}

.follow-system-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--el-text-color-primary);
}

.row-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
  color: var(--el-color-primary);
}

.follow-system-label {
  margin-right: auto;
}

.theme-mode-panel--compact .theme-option {
  flex-direction: row;
  gap: 6px;
  min-height: 36px;
}

.theme-mode-panel--compact .follow-system-row {
  padding-left: 12px;
}

:global(.dark) .theme-title {
  color: rgba(255, 255, 255, 0.9);
}

:global(.dark) .theme-title::before {
  background: var(--theme-hue-title-accent-dark, var(--header-accent-bright, var(--el-color-primary-light-5)));
}

:global(.dark) .theme-option {
  border-color: rgba(255, 255, 255, 0.25);
  color: #e5e7eb;
}

:global(.dark) .theme-option:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

:global(.dark) .theme-option.active {
  border-color: var(--el-color-primary-dark-2);
  background: var(--el-color-primary-dark-2);
  color: var(--el-color-primary-light-9);
}

:global(.dark) .theme-divider {
  background: rgba(255, 255, 255, 0.25);
}

:global(.dark) .follow-system-row {
  color: #e5e7eb;
}

:global(.dark) .theme-option span {
  color: inherit;
}
</style>
