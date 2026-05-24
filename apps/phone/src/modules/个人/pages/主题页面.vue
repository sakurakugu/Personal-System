<script setup lang="ts">
import { 使用主题存储 } from '@/shared/stores/theme'
import { PageSectionShell, ThemeHuePanel, ThemeModePanel } from '@personal-system/ui'

const theme = 使用主题存储()
</script>

<template>
  <section class="page">
    <PageSectionShell
      title="主题设置"
      to="/me/settings"
      :show-back="true"
    />

    <section class="panel-card theme-panel theme-panel--mode">
      <ThemeModePanel
        :model-value="theme.mode"
        :is-dark="theme.isDark"
        :show-follow-system-icon="true"
        :inline-option-content="true"
        @update:model-value="theme.setMode"
      />
    </section>

    <section class="panel-card theme-panel theme-panel--hue">
      <ThemeHuePanel
        :model-value="theme.hue"
        :default-value="theme.defaultHue"
        @update:model-value="theme.setHue"
      />
    </section>
  </section>
</template>

<style scoped>
.theme-panel {
  padding: 0;
}

.theme-panel--mode {
  padding: 10px 6px 8px;
}

.theme-panel--hue {
  padding: 18px 18px 16px;
}

.theme-panel + .theme-panel {
  margin-top: 14px;
}
</style>
