<script setup lang="ts">
import { BaseDialog } from '@personal-system/ui'

const props = defineProps<{
  modelValue: boolean
}>()

defineEmits<{
  'update:modelValue': [value: boolean]
}>()
</script>

<template>
  <BaseDialog v-bind="$attrs" :model-value="props.modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <template v-if="$slots.header" #header>
      <slot name="header" />
    </template>
    <template v-if="$slots.default">
      <slot />
    </template>
    <template v-if="$slots.footer" #footer>
      <slot name="footer" />
    </template>
  </BaseDialog>
</template>
