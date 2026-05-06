<script setup lang="ts">
import { RefreshLeft } from '@element-plus/icons-vue'
import { ElIcon } from 'element-plus'
import { HueSlider } from '@personal-system/ui'
import { useThemeStore } from '../../shared/stores/theme'

const theme = useThemeStore()
const defaultHue = theme.defaultHue

function resetHue() {
  theme.setHue(defaultHue)
}
</script>

<template>
  <div class="palette-settings-panel">
    <div class="hue-row">
      <div class="hue-header">
        <div class="hue-title">
          <span>主题色相</span>
          <button
            class="hue-reset"
            :class="{ 'hue-reset-hidden': theme.hue === defaultHue }"
            type="button"
            @click="resetHue"
          >
            <ElIcon :size="12"><RefreshLeft /></ElIcon>
          </button>
        </div>
        <span class="hue-value">{{ theme.hue }}</span>
      </div>
      <div class="hue-slider-wrapper">
        <HueSlider
          :model-value="theme.hue"
          :step="5"
          @update:model-value="theme.setHue"
        />
      </div>
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
}

.hue-title {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 12px;
  font-size: 18px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.9);
}

.hue-title::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -12px;
  width: 4px;
  height: 16px;
  border-radius: 4px;
  background: var(--header-accent-soft);
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
  color: var(--header-accent);
  background: var(--header-accent-surface);
  cursor: pointer;
  transition: opacity 0.2s, background 0.15s, transform 0.15s;
}

.hue-reset:hover {
  background: var(--header-accent-surface-hover);
}

.hue-reset:active {
  transform: scale(0.9);
}

.hue-reset-hidden {
  opacity: 0;
  pointer-events: none;
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
  color: var(--header-accent);
  background: var(--header-accent-surface);
}

.hue-slider-wrapper {
  width: 100%;
}

.dark .hue-title {
  color: rgba(255, 255, 255, 0.9);
}

.dark .hue-title::before {
  background: var(--header-accent-bright);
}

.dark .hue-reset {
  color: var(--header-accent-bright);
  background: var(--header-accent-surface-dark);
}

.dark .hue-reset:hover {
  background: var(--header-accent-surface-dark-hover);
}

.dark .hue-value {
  color: var(--header-accent-bright);
  background: var(--header-accent-surface-dark);
}
</style>
