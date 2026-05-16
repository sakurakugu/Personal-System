<script setup lang="ts">
import { 构建授权文章资源URL } from '../media'

const props = defineProps<{
  url: string | null
  alt?: string
  preview?: boolean
}>()

function resolveUrl(url: string | null) {
  return 构建授权文章资源URL(url)
}
</script>

<template>
  <img
    v-if="props.url"
    :src="resolveUrl(props.url)"
    :alt="props.alt || ''"
    :data-fancybox="props.preview ? 'article-cover' : undefined"
    loading="lazy"
    decoding="async"
  >
</template>
