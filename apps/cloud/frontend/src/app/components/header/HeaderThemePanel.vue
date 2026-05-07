<script setup lang="ts">
import { ThemeModePanel } from '@personal-system/ui'
import { useThemeStore } from '../../../shared/stores/theme'

withDefaults(defineProps<{
  compact?: boolean
}>(), {
  compact: false,
})

const theme = useThemeStore()
</script>

<template>
  <ThemeModePanel
    :model-value="theme.mode"
    :is-dark="theme.isDark"
    :compact="compact"
    @update:model-value="theme.setMode"
  />
</template>
