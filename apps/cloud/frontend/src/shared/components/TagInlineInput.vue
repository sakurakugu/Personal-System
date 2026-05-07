<script setup lang="ts">
import { TagInlineInput } from '@personal-system/ui'

const props = withDefaults(defineProps<{
  modelValue: string
  existingTags: string[]
  placeholder?: string
}>(), {
  placeholder: '',
})

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <TagInlineInput
    v-bind="$attrs"
    :model-value="props.modelValue"
    :existing-tags="props.existingTags"
    :placeholder="props.placeholder"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>
