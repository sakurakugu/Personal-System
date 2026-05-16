<script setup lang="ts">
import { ThemeModePanel } from '@personal-system/ui'
import { 使用主题存储 } from '../../../shared/stores/theme'

withDefaults(defineProps<{
  compact?: boolean
}>(), {
  compact: false,
})

const theme = 使用主题存储()
</script>

<template>
  <ThemeModePanel
    :model-value="theme.mode"
    :is-dark="theme.isDark"
    :compact="compact"
    @update:model-value="theme.setMode"
  />
</template>
