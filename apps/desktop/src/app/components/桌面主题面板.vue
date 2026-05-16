<script setup lang="ts">
import { ThemeModePanel } from '@personal-system/ui'
import { useThemeStore } from '../../shared/stores/theme'

const theme = useThemeStore()
</script>

<template>
  <ThemeModePanel
    :model-value="theme.mode"
    :is-dark="theme.isDark"
    @update:model-value="theme.setMode"
  />
</template>
