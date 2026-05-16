<script setup lang="ts">
const props = withDefaults(defineProps<{
  modelValue: number
  min?: number
  max?: number
  step?: number
  ariaLabel?: string
  disabled?: boolean
}>(), {
  min: 0,
  max: 100,
  step: 1,
  ariaLabel: '数值滑动条',
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

function handleInput(event: Event) {
  const target = event.target
  if (!(target instanceof HTMLInputElement)) {
    return
  }
  emit('update:modelValue', Number(target.value))
}
</script>

<template>
  <input
    class="glass-range-slider"
    type="range"
    :min="props.min"
    :max="props.max"
    :step="props.step"
    :value="props.modelValue"
    :aria-label="props.ariaLabel"
    :disabled="props.disabled"
    @input="handleInput"
  >
</template>

<style scoped>
.glass-range-slider {
  --glass-range-track-height: 14px;
  --glass-range-track-border: rgba(148, 163, 184, 0.22);
  --glass-range-track-background: rgba(148, 163, 184, 0.18);
  --glass-range-thumb-size: 18px;
  --glass-range-thumb-offset: -3px;
  --glass-range-thumb-border: rgba(148, 163, 184, 0.45);
  --glass-range-thumb-background: rgba(241, 245, 249, 0.96);
  --glass-range-thumb-background-hover: rgba(226, 232, 240, 0.98);
  --glass-range-thumb-shadow: 0 4px 14px rgba(15, 23, 42, 0.14);
  width: 100%;
  height: var(--glass-range-track-height);
  margin: 0;
  -webkit-appearance: none;
  appearance: none;
  border-radius: 999px;
  background: transparent;
}

.glass-range-slider:hover {
  cursor: pointer;
}

.glass-range-slider:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.glass-range-slider:focus-visible {
  outline: none;
}

.glass-range-slider::-webkit-slider-runnable-track {
  height: var(--glass-range-track-height);
  border: 1px solid var(--glass-range-track-border);
  border-radius: 999px;
  background: var(--glass-range-track-background);
  backdrop-filter: blur(10px) saturate(140%);
  -webkit-backdrop-filter: blur(10px) saturate(140%);
}

.glass-range-slider::-webkit-slider-thumb {
  width: var(--glass-range-thumb-size);
  height: var(--glass-range-thumb-size);
  margin-top: var(--glass-range-thumb-offset);
  -webkit-appearance: none;
  appearance: none;
  border: 1px solid var(--glass-range-thumb-border);
  border-radius: 50%;
  background: var(--glass-range-thumb-background);
  box-shadow: var(--glass-range-thumb-shadow);
}

.glass-range-slider::-webkit-slider-thumb:hover {
  background: var(--glass-range-thumb-background-hover);
}

.glass-range-slider::-moz-range-track {
  height: var(--glass-range-track-height);
  border: 1px solid var(--glass-range-track-border);
  border-radius: 999px;
  background: var(--glass-range-track-background);
}

.glass-range-slider::-moz-range-thumb {
  width: var(--glass-range-thumb-size);
  height: var(--glass-range-thumb-size);
  border: 1px solid var(--glass-range-thumb-border);
  border-radius: 50%;
  background: var(--glass-range-thumb-background);
  box-shadow: var(--glass-range-thumb-shadow);
}

.glass-range-slider::-moz-range-thumb:hover {
  background: var(--glass-range-thumb-background-hover);
}

:global(.dark) .glass-range-slider {
  --glass-range-track-border: rgba(255, 255, 255, 0.14);
  --glass-range-track-background: rgba(255, 255, 255, 0.16);
  --glass-range-thumb-border: rgba(255, 255, 255, 0.34);
  --glass-range-thumb-background: rgba(255, 255, 255, 0.52);
  --glass-range-thumb-background-hover: rgba(255, 255, 255, 0.64);
  --glass-range-thumb-shadow: 0 4px 14px rgba(0, 0, 0, 0.28);
}
</style>
