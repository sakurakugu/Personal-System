<script setup lang="ts">
import { StarFilled } from '@element-plus/icons-vue'
import { ElIcon } from 'element-plus'
import { computed } from 'vue'
import { 获取评分展示 } from '../rating'

const props = withDefaults(defineProps<{
  rating: number | null
  compact?: boolean
  showText?: boolean
}>(), {
  compact: false,
  showText: false,
})

const 展示 = computed(() => props.rating == null ? null : 获取评分展示(props.rating))
</script>

<template>
  <div
    v-if="展示"
    class="media-rating"
    :class="{ 'media-rating--compact': compact, 'media-rating--special': 展示.type !== 'stars' }"
  >
    <template v-if="展示.type === 'stars'">
      <span
        v-for="(state, index) in 展示.starStates"
        :key="`${rating}-${index}`"
        class="media-rating__star"
        :class="`media-rating__star--${state}`"
        aria-hidden="true"
      >
        <ElIcon class="media-rating__star-icon media-rating__star-icon--base">
          <StarFilled />
        </ElIcon>
        <span
          v-if="state !== 'empty'"
          class="media-rating__star-fill"
          :class="{ 'media-rating__star-fill--half': state === 'half' }"
        >
          <ElIcon class="media-rating__star-icon media-rating__star-icon--fill">
            <StarFilled />
          </ElIcon>
        </span>
      </span>
    </template>
    <span v-else class="media-rating__special-icon" aria-hidden="true">{{ 展示.icon }}</span>
    <span v-if="showText" class="media-rating__text">{{ 展示.label }}</span>
  </div>
</template>

<style scoped>
.media-rating {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-height: 1em;
  line-height: 1;
}

.media-rating--compact {
  gap: 2px;
}

.media-rating__star {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  line-height: 1;
}

.media-rating--compact .media-rating__star {
  font-size: 12px;
}

.media-rating__star-icon {
  display: inline-flex;
}

.media-rating__star-icon--base {
  color: rgba(148, 163, 184, 0.55);
}

.media-rating__star-fill {
  position: absolute;
  inset: 0;
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  overflow: hidden;
}

.media-rating__star-fill--half {
  width: 50%;
}

.media-rating__star-icon--fill {
  color: #f59e0b;
}

.media-rating__special-icon {
  font-size: 14px;
  line-height: 1;
}

.media-rating--compact .media-rating__special-icon {
  font-size: 13px;
}

.media-rating__text {
  color: inherit;
  font-size: 12px;
  line-height: 1;
  white-space: nowrap;
}
</style>
