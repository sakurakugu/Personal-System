<script setup lang="ts">
import HueSlider from './HueSlider.vue'

const props = withDefaults(defineProps<{
  modelValue: number
  defaultValue: number
  title?: string
  max?: number
  step?: number
}>(), {
  title: '主题色相',
  max: 359,
  step: 5,
})

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

function resetHue() {
  emit('update:modelValue', props.defaultValue)
}
</script>

<template>
  <div class="hue-row">
    <div class="hue-header">
      <div class="hue-title">
        <span>{{ props.title }}</span>
        <button
          class="hue-reset"
          :class="{ 'hue-reset-hidden': props.modelValue === props.defaultValue }"
          type="button"
          @click="resetHue"
        >
          <svg class="hue-reset-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M3.86 10.5a8.25 8.25 0 1 1 2.06 7.15"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <path
              d="M3.75 5.75v4.75h4.75"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </button>
      </div>
      <div class="hue-meta">
        <div class="theme-preview-row">
          <span class="theme-preview theme-preview--primary" />
          <span class="theme-preview theme-preview--soft" />
          <span class="theme-preview theme-preview--card" />
        </div>
        <span class="hue-value">{{ props.modelValue }}</span>
      </div>
    </div>
    <div class="hue-slider-wrapper">
      <HueSlider
        :model-value="props.modelValue"
        :max="props.max"
        :step="props.step"
        @update:model-value="(value) => emit('update:modelValue', value)"
      />
    </div>
  </div>
</template>

<style scoped>
.hue-row {
  padding: 0;
}

.hue-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 12px;
}

.hue-title {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 12px;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary, var(--el-text-color-primary));
}

.hue-title::before {
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

.hue-reset {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  border-radius: 6px;
  color: var(--theme-hue-accent, var(--header-accent, var(--el-color-primary)));
  background: var(--theme-hue-surface, var(--header-accent-surface, color-mix(in srgb, var(--el-color-primary) 12%, white)));
  cursor: pointer;
  transition: opacity 0.2s, background 0.15s, transform 0.15s;
}

.hue-reset:hover {
  background: var(--theme-hue-surface-hover, var(--header-accent-surface-hover, color-mix(in srgb, var(--el-color-primary) 18%, white)));
}

.hue-reset:active {
  transform: scale(0.9);
}

.hue-reset-hidden {
  opacity: 0;
  pointer-events: none;
}

.hue-reset-icon {
  width: 14px;
  height: 14px;
}

.hue-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.theme-preview-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.theme-preview {
  width: 16px;
  height: 16px;
  border-radius: 999px;
  border: 1px solid var(--theme-hue-preview-border, var(--theme-card-border, var(--el-border-color)));
}

.theme-preview--primary {
  background: var(--el-color-primary);
}

.theme-preview--soft {
  background: var(--theme-hue-preview-soft, var(--theme-accent-soft, var(--el-color-primary-light-7)));
}

.theme-preview--card {
  background: var(--theme-hue-preview-card, var(--theme-card-bg, var(--el-bg-color-overlay)));
}

.hue-value {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 28px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 700;
  color: var(--theme-hue-accent, var(--header-accent, var(--el-color-primary)));
  background: var(--theme-hue-surface, var(--header-accent-surface, color-mix(in srgb, var(--el-color-primary) 12%, white)));
}

.hue-slider-wrapper {
  width: 100%;
}

:global(.dark) .hue-title::before {
  background: var(--theme-hue-title-accent-dark, var(--header-accent-bright, var(--el-color-primary-light-5)));
}

:global(.dark) .hue-reset {
  color: var(--theme-hue-accent-dark, var(--header-accent-bright, var(--el-color-primary-light-5)));
  background: var(--theme-hue-surface-dark, var(--header-accent-surface-dark, color-mix(in srgb, var(--el-color-primary-light-5) 18%, #0f172a)));
}

:global(.dark) .hue-reset:hover {
  background: var(--theme-hue-surface-dark-hover, var(--header-accent-surface-dark-hover, color-mix(in srgb, var(--el-color-primary-light-5) 24%, #0f172a)));
}

:global(.dark) .hue-value {
  color: var(--theme-hue-accent-dark, var(--header-accent-bright, var(--el-color-primary-light-5)));
  background: var(--theme-hue-surface-dark, var(--header-accent-surface-dark, color-mix(in srgb, var(--el-color-primary-light-5) 18%, #0f172a)));
}
</style>
