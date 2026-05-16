<script setup lang="ts">
import { ThemeHuePanel } from '@personal-system/ui'
import { useThemeStore } from '../../shared/stores/theme'

const theme = useThemeStore()
</script>

<template>
  <div class="palette-settings-panel">
    <ThemeHuePanel
      :model-value="theme.hue"
      :default-value="theme.defaultHue"
      @update:model-value="theme.setHue"
    />
  </div>
</template>
