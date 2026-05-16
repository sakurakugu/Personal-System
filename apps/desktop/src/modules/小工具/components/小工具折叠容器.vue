<script setup lang="ts">
import type { CSSProperties } from 'vue'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = withDefaults(defineProps<{
  visible: boolean
  gap?: number
}>(), {
  gap: 12,
})

const ready = ref(false)
const contentElement = ref<globalThis.HTMLElement | null>(null)
const contentHeight = ref(0)

let contentResizeObserver: globalThis.ResizeObserver | null = null

function 同步内容高度() {
  const element = contentElement.value
  if (!element) {
    contentHeight.value = 0
    return
  }
  const rectHeight = Math.ceil(element.getBoundingClientRect().height)
  const scrollHeight = Math.ceil(element.scrollHeight)
  const offsetHeight = Math.ceil(element.offsetHeight)
  contentHeight.value = Math.max(rectHeight, scrollHeight, offsetHeight)
}

const 容器样式 = computed<CSSProperties>(() => {
  if (!ready.value) {
    return {
      height: props.visible ? 'auto' : '0px',
      pointerEvents: props.visible ? 'auto' : 'none',
    }
  }

  return {
    height: props.visible ? `${contentHeight.value + props.gap}px` : '0px',
    pointerEvents: props.visible ? 'auto' : 'none',
  }
})

onMounted(async () => {
  await nextTick()
  同步内容高度()
  contentResizeObserver = new window.ResizeObserver(() => {
    同步内容高度()
  })
  if (contentElement.value) {
    contentResizeObserver.observe(contentElement.value)
  }
  ready.value = true
})

onBeforeUnmount(() => {
  contentResizeObserver?.disconnect()
  contentResizeObserver = null
})

watch(
  () => props.visible,
  async () => {
    await nextTick()
    同步内容高度()
  },
)
</script>

<template>
  <div
    class="widget-collapse"
    :class="{ 'widget-collapse--ready': ready, 'widget-collapse--visible': visible }"
    :style="容器样式"
    :aria-hidden="!visible"
    :inert="!visible ? true : undefined"
  >
    <div class="widget-collapse__inner" :style="{ paddingTop: `${gap}px` }">
      <div ref="contentElement" class="widget-collapse__content">
        <slot />
      </div>
    </div>
  </div>
</template>

<style>
.widget-collapse {
  overflow: hidden;
}

.widget-collapse--ready {
  transition: height 0.28s cubic-bezier(0.24, 0.8, 0.32, 1);
  will-change: height;
}

.widget-collapse__inner {
  box-sizing: border-box;
}

.widget-collapse__content {
  min-width: 0;
}

.widget-collapse--ready .widget-collapse__content {
  transition: opacity 0.14s ease;
  will-change: opacity;
}

.widget-collapse--ready.widget-collapse--visible .widget-collapse__content {
  opacity: 1;
  transition-delay: 0s;
}

.widget-collapse--ready:not(.widget-collapse--visible) .widget-collapse__content {
  opacity: 0;
  transition-delay: 0.14s;
}
</style>
