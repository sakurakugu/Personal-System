<script setup lang="ts">
import ProfileSubpageHeader from '@/modules/profile/components/ProfileSubpageHeader.vue'
import { useThemeStore } from '@/shared/stores/theme'

const theme = useThemeStore()
const themeModes = [
  { value: 'system', label: '跟随系统' },
  { value: 'light', label: '浅色' },
  { value: 'dark', label: '深色' },
] as const

function handleThemeModeChange(mode: 'light' | 'dark' | 'system') {
  theme.setMode(mode)
}

function handleHueChange(event: globalThis.Event) {
  const target = event.target
  if (!(target instanceof globalThis.HTMLInputElement)) {
    return
  }
  theme.setHue(Number(target.value))
}
</script>

<template>
  <section class="page">
    <ProfileSubpageHeader
      eyebrow="主题"
      title="主题设置"
      description="外观设置独立成页，后续再扩展字体、卡片密度或动效时不会继续塞回总览页。"
    />

    <section class="panel-card stack">
      <div>
        <span class="info-label">主题模式</span>
        <strong class="section-title">{{ theme.modeLabel }}</strong>
      </div>
      <div class="theme-mode-list">
        <button
          v-for="item in themeModes"
          :key="item.value"
          class="chip-button"
          :class="{ 'chip-button--active': theme.mode === item.value }"
          type="button"
          @click="handleThemeModeChange(item.value)"
        >
          {{ item.label }}
        </button>
      </div>
      <label class="theme-slider-field">
        <span class="info-label">主题主色</span>
        <div class="theme-slider-wrapper">
          <div class="theme-slider-track" aria-hidden="true" />
          <input
            class="theme-slider"
            type="range"
            min="0"
            max="359"
            :value="theme.hue"
            @input="handleHueChange"
          >
        </div>
      </label>
      <div class="theme-preview-row">
        <span class="theme-preview theme-preview--primary" />
        <span class="theme-preview theme-preview--soft" />
        <span class="theme-preview theme-preview--card" />
        <span class="panel-meta">当前 Hue：{{ theme.hue }}</span>
      </div>
    </section>
  </section>
</template>

<style scoped>
.info-label {
  color: var(--text-tertiary);
}

.theme-mode-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.theme-slider-field {
  display: grid;
  gap: 10px;
}

.theme-slider-wrapper {
  --slider-edge-gap: 5px;
  --slider-edge-color: oklch(0.8 0.1 0);
  position: relative;
  width: 100%;
  height: 24px;
  border-radius: 4px;
}

.theme-slider-track {
  position: absolute;
  inset: 0;
  border-radius: 4px;
  background:
    linear-gradient(var(--slider-edge-color), var(--slider-edge-color)) left center / var(--slider-edge-gap) 100% no-repeat,
    var(--color-selection-bar) center / calc(100% - (var(--slider-edge-gap) * 2)) 100% no-repeat,
    linear-gradient(var(--slider-edge-color), var(--slider-edge-color)) right center / var(--slider-edge-gap) 100% no-repeat;
  pointer-events: none;
}

.theme-slider {
  position: absolute;
  top: 0;
  right: var(--slider-edge-gap);
  bottom: 0;
  left: var(--slider-edge-gap);
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

.theme-slider::-webkit-slider-runnable-track {
  height: 100%;
  background: transparent;
  border: none;
}

.theme-slider::-webkit-slider-thumb {
  width: 8px;
  height: 16px;
  margin-top: 4px;
  -webkit-appearance: none;
  appearance: none;
  border: none;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: none;
}

.theme-slider::-webkit-slider-thumb:hover {
  background: rgba(255, 255, 255, 0.85);
}

.theme-slider::-webkit-slider-thumb:active {
  background: rgba(255, 255, 255, 0.6);
}

.theme-slider::-moz-range-track,
.theme-slider::-moz-range-progress {
  height: 100%;
  background: transparent;
  border: none;
}

.theme-slider::-moz-range-thumb {
  width: 8px;
  height: 16px;
  border: none;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: none;
}

.theme-slider::-moz-range-thumb:hover {
  background: rgba(255, 255, 255, 0.85);
}

.theme-slider::-moz-range-thumb:active {
  background: rgba(255, 255, 255, 0.6);
}

.dark .theme-slider-wrapper {
  --slider-edge-color: oklch(0.7 0.1 0);
}

.theme-preview-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.theme-preview {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  border: 1px solid var(--theme-card-border);
}

.theme-preview--primary {
  background: var(--el-color-primary);
}

.theme-preview--soft {
  background: var(--theme-accent-soft);
}

.theme-preview--card {
  background: var(--theme-card-bg);
}
</style>
