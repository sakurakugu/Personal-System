<script setup lang="ts">
import { ThemeHuePanel } from '@personal-system/ui'
import { 使用主题存储 } from '../../shared/stores/theme'

const theme = 使用主题存储()
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
