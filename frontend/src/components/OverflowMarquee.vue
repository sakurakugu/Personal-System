<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

defineOptions({
  inheritAttrs: false,
})

const props = withDefaults(defineProps<{
  text: string
  tag?: string
  gap?: number
  speed?: number
}>(), {
  tag: 'span',
  gap: 32,
  speed: 40,
})

const containerRef = ref<globalThis.HTMLElement | null>(null)
const contentRef = ref<globalThis.HTMLElement | null>(null)
const isOverflowing = ref(false)
const distance = ref(0)
let resizeObserver: globalThis.ResizeObserver | null = null

const animationDuration = computed(() => {
  if (!isOverflowing.value || distance.value <= 0) {
    return '0s'
  }
  const duration = Math.max(6, distance.value / props.speed)
  return `${duration}s`
})

const marqueeStyle = computed(() => ({
  '--overflow-marquee-gap': `${props.gap}px`,
  '--overflow-marquee-distance': `${distance.value}px`,
  '--overflow-marquee-duration': animationDuration.value,
}))

function updateOverflowState() {
  const container = containerRef.value
  const content = contentRef.value
  if (!container || !content) {
    isOverflowing.value = false
    distance.value = 0
    return
  }

  const nextOverflow = content.scrollWidth > container.clientWidth + 1
  isOverflowing.value = nextOverflow
  distance.value = nextOverflow ? content.scrollWidth + props.gap : 0
}

async function syncOverflowState() {
  await nextTick()
  globalThis.requestAnimationFrame(() => {
    updateOverflowState()
  })
}

onMounted(() => {
  void syncOverflowState()

  resizeObserver = new globalThis.ResizeObserver(() => {
    updateOverflowState()
  })

  if (containerRef.value) {
    resizeObserver.observe(containerRef.value)
  }

  if (contentRef.value) {
    resizeObserver.observe(contentRef.value)
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
})

watch(() => props.text, () => {
  void syncOverflowState()
})
</script>

<template>
  <component
    :is="tag"
    v-bind="$attrs"
    ref="containerRef"
    class="overflow-marquee"
    :class="{ 'is-overflowing': isOverflowing }"
    :style="marqueeStyle"
  >
    <span class="overflow-marquee__track">
      <span ref="contentRef" class="overflow-marquee__text">{{ text }}</span>
      <template v-if="isOverflowing">
        <span class="overflow-marquee__gap" aria-hidden="true" />
        <span class="overflow-marquee__text overflow-marquee__text--clone" aria-hidden="true">{{ text }}</span>
      </template>
    </span>
  </component>
</template>

<style scoped>
.overflow-marquee {
  display: block;
  min-width: 0;
  overflow: hidden;
}

.overflow-marquee__track {
  display: inline-flex;
  align-items: center;
  min-width: 100%;
  white-space: nowrap;
}

.overflow-marquee.is-overflowing .overflow-marquee__track {
  width: max-content;
  animation: overflow-marquee-scroll var(--overflow-marquee-duration) linear infinite;
}

.overflow-marquee__text {
  flex: 0 0 auto;
  min-width: 0;
}

.overflow-marquee__gap {
  flex: 0 0 var(--overflow-marquee-gap);
  width: var(--overflow-marquee-gap);
}

@keyframes overflow-marquee-scroll {
  from {
    transform: translateX(0);
  }

  to {
    transform: translateX(calc(var(--overflow-marquee-distance) * -1));
  }
}
</style>
