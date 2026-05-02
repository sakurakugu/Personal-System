<script setup lang="ts">
import ProfileSubpageHeader from '@/modules/profile/components/ProfileSubpageHeader.vue'
import { useThemeStore } from '@/shared/stores/theme'
import { HueSlider } from '@personal-system/ui'

const theme = useThemeStore()
const themeModes = [
  { value: 'system', label: '跟随系统' },
  { value: 'light', label: '浅色' },
  { value: 'dark', label: '深色' },
] as const

function handleThemeModeChange(mode: 'light' | 'dark' | 'system') {
  theme.setMode(mode)
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
        <HueSlider
          :model-value="theme.hue"
          :max="359"
          @update:model-value="theme.setHue"
        />
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
