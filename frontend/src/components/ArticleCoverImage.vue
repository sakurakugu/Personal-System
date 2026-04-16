<script setup lang="ts">
import { buildAuthorizedArticleAssetUrl } from '../utils/articleMedia'

const props = defineProps<{
  url: string | null
  alt?: string
  preview?: boolean
}>()

function resolveUrl(url: string | null) {
  return buildAuthorizedArticleAssetUrl(url)
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
