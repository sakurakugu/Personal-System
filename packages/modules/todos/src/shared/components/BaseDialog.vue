<script setup lang="ts">
import { ElDialog } from 'element-plus'
import { useAttrs } from 'vue'

defineOptions({
  inheritAttrs: false,
})

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const attrs = useAttrs()
</script>

<template>
  <ElDialog
    v-bind="attrs"
    :model-value="props.modelValue"
    :lock-scroll="false"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <template v-if="$slots.header" #header>
      <slot name="header" />
    </template>
    <template v-if="$slots.default">
      <slot />
    </template>
    <template v-if="$slots.footer" #footer>
      <slot name="footer" />
    </template>
  </ElDialog>
</template>
