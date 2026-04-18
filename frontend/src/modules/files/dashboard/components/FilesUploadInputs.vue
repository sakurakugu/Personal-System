<script setup lang="ts">
import type { ComponentPublicInstance } from 'vue'

defineProps<{
  设置文件上传输入框引用: (element: globalThis.Element | ComponentPublicInstance | null) => void
  设置目录上传输入框引用: (element: globalThis.Element | ComponentPublicInstance | null) => void
}>()

const emit = defineEmits<{
  'file-change': [event: globalThis.Event]
  'folder-change': [event: globalThis.Event]
}>()
</script>

<template>
  <input
    :ref="设置文件上传输入框引用"
    type="file"
    multiple
    class="hidden-input"
    @change="emit('file-change', $event)"
  >
  <input
    :ref="设置目录上传输入框引用"
    type="file"
    multiple
    webkitdirectory
    directory
    class="hidden-input"
    @change="emit('folder-change', $event)"
  >
</template>

<style scoped>
.hidden-input {
  display: none;
}
</style>
