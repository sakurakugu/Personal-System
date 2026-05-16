<script setup lang="ts">
const props = withDefaults(defineProps<{
  modelValue: number
  min?: number
  max?: number
  step?: number
  ariaLabel?: string
}>(), {
  min: 0,
  max: 360,
  step: 1,
  ariaLabel: '主题色相',
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
  <div class="hue-slider-wrapper">
    <div class="hue-slider-track" aria-hidden="true" />
    <input
      class="hue-slider-input"
      type="range"
      :min="props.min"
      :max="props.max"
      :step="props.step"
      :value="props.modelValue"
      :aria-label="props.ariaLabel"
      @input="handleInput"
    >
  </div>
</template>

<style scoped>
.hue-slider-wrapper {
  --slider-edge-gap: 3px;
  --slider-thumb-width: 8px;
  position: relative;
  width: 100%;
  height: 24px;
  border-radius: 4px;
}

.hue-slider-track {
  position: absolute;
  inset: 0;
  border-radius: 4px;
  background: var(--color-selection-bar);
  pointer-events: none;
}

.hue-slider-input {
  position: absolute;
  top: 0;
  right: calc(var(--slider-thumb-width) / 2);
  bottom: 0;
  left: calc(var(--slider-edge-gap) + (var(--slider-thumb-width) / 2));
  width: auto;
  height: 100%;
  margin: 0;
  -webkit-appearance: none;
  appearance: none;
  border-radius: 4px;
  background: transparent;
  outline: none;
  cursor: pointer;
}

.hue-slider-input::-webkit-slider-runnable-track {
  height: 100%;
  background: transparent;
  border: none;
}

.hue-slider-input::-webkit-slider-thumb {
  width: var(--slider-thumb-width);
  height: 16px;
  margin-top: 4px;
  -webkit-appearance: none;
  appearance: none;
  border: none;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: none;
}

.hue-slider-input::-webkit-slider-thumb:hover {
  background: rgba(255, 255, 255, 0.85);
}

.hue-slider-input::-webkit-slider-thumb:active {
  background: rgba(255, 255, 255, 0.6);
}

.hue-slider-input::-moz-range-track,
.hue-slider-input::-moz-range-progress {
  height: 100%;
  background: transparent;
  border: none;
}

.hue-slider-input::-moz-range-thumb {
  width: var(--slider-thumb-width);
  height: 16px;
  border: none;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: none;
}

.hue-slider-input::-moz-range-thumb:hover {
  background: rgba(255, 255, 255, 0.85);
}

.hue-slider-input::-moz-range-thumb:active {
  background: rgba(255, 255, 255, 0.6);
}

</style>
