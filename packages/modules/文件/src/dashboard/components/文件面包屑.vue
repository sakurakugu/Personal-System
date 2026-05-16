<script setup lang="ts">
import {
  ElBreadcrumb,
  ElBreadcrumbItem,
} from 'element-plus'
import type { FileBreadcrumbItem } from '../../types'

defineProps<{
  导航栏列表: FileBreadcrumbItem[]
  禁止拖放节点键列表: string[]
}>()

const emit = defineEmits<{
  navigate: [item: FileBreadcrumbItem]
  drop: [payload: { folderId: string | null; dragEvent: globalThis.DragEvent }]
}>()
</script>

<template>
  <ElBreadcrumb separator="/">
    <ElBreadcrumbItem v-for="item in 导航栏列表" :key="item.id ?? 'root'">
      <button
        type="button"
        class="breadcrumb-button"
        @click="emit('navigate', item)"
        @dragover.prevent
        @drop="item.id && 禁止拖放节点键列表.includes(item.id) ? null : emit('drop', { folderId: item.id, dragEvent: $event })"
      >
        {{ item.name }}
      </button>
    </ElBreadcrumbItem>
  </ElBreadcrumb>
</template>
