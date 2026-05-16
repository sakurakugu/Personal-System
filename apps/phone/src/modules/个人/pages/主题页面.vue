<script setup lang="ts">
import ProfileSubpageHeader from '@/modules/个人/components/ProfileSubpageHeader.vue'
import { useThemeStore } from '@/shared/stores/theme'
import { ThemeHuePanel, ThemeModePanel } from '@personal-system/ui'

const theme = useThemeStore()
</script>

<template>
  <section class="page">
    <ProfileSubpageHeader
      title="主题设置"
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
