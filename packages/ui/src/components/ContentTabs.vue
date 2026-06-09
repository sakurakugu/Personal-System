<script lang="ts">
export interface ContentTabItem {
  label: string
  value: string
  count?: number | string
  disabled?: boolean
  title?: string
}
</script>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = withDefaults(defineProps<{
  modelValue: string
  items: readonly ContentTabItem[]
  ariaLabel?: string
  showCount?: boolean
}>(), {
  ariaLabel: '标签页',
  showCount: true,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  change: [value: string]
}>()

const 滚动容器 = ref<globalThis.HTMLElement | null>(null)
const 正在拖动 = ref(false)
const 阻止点击 = ref(false)
const 起始横坐标 = ref(0)
const 起始滚动位置 = ref(0)
const 按钮元素 = new Map<string, globalThis.HTMLButtonElement>()
const 指示器样式 = ref({
  width: '0px',
  transform: 'translateX(0px)',
})

function 设置按钮引用(value: string, element: globalThis.Element | null) {
  if (element instanceof globalThis.HTMLButtonElement) {
    按钮元素.set(value, element)
    return
  }
  按钮元素.delete(value)
}

function 更新指示器位置() {
  const activeButton = 按钮元素.get(props.modelValue)
  if (!activeButton) {
    指示器样式.value = {
      width: '0px',
      transform: 'translateX(0px)',
    }
    return
  }
  指示器样式.value = {
    width: `${activeButton.offsetWidth}px`,
    transform: `translateX(${activeButton.offsetLeft}px)`,
  }
}

function 选择标签(value: string, event?: globalThis.MouseEvent) {
  if (阻止点击.value) {
    event?.preventDefault()
    event?.stopPropagation()
    阻止点击.value = false
    return
  }
  if (value === props.modelValue) {
    return
  }
  emit('update:modelValue', value)
  emit('change', value)
}

function 开始拖动(event: globalThis.MouseEvent) {
  if (event.button !== 0 && event.button !== 1) {
    return
  }
  const container = 滚动容器.value
  if (!container) {
    return
  }
  正在拖动.value = false
  起始横坐标.value = event.clientX
  起始滚动位置.value = container.scrollLeft
  container.classList.add('content-tabs-scroll--dragging')
  window.addEventListener('mousemove', 拖动)
  window.addEventListener('mouseup', 结束拖动)
  if (event.button === 1) {
    event.preventDefault()
  }
}

function 拖动(event: globalThis.MouseEvent) {
  const container = 滚动容器.value
  if (!container) {
    return
  }
  const 位移 = event.clientX - 起始横坐标.value
  if (Math.abs(位移) > 4) {
    正在拖动.value = true
  }
  container.scrollLeft = 起始滚动位置.value - 位移
  if (正在拖动.value) {
    event.preventDefault()
  }
}

function 结束拖动() {
  const container = 滚动容器.value
  if (container) {
    container.classList.remove('content-tabs-scroll--dragging')
  }
  window.removeEventListener('mousemove', 拖动)
  window.removeEventListener('mouseup', 结束拖动)
  if (正在拖动.value) {
    阻止点击.value = true
    window.setTimeout(() => {
      阻止点击.value = false
    }, 0)
  }
}

function 处理滚轮(event: globalThis.WheelEvent) {
  const container = 滚动容器.value
  if (!container) {
    return
  }
  const 横向位移 = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY
  if (横向位移 === 0) {
    return
  }
  const 已滚到最左侧 = container.scrollLeft <= 0
  const 已滚到最右侧 = container.scrollLeft + container.clientWidth >= container.scrollWidth - 1
  if ((横向位移 < 0 && 已滚到最左侧) || (横向位移 > 0 && 已滚到最右侧)) {
    return
  }
  event.preventDefault()
  container.scrollLeft += 横向位移
}

watch(
  () => [props.modelValue, props.items] as const,
  () => {
    void nextTick(更新指示器位置)
  },
  { flush: 'post' },
)

onMounted(() => {
  void nextTick(更新指示器位置)
  window.addEventListener('resize', 更新指示器位置)
})

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', 拖动)
  window.removeEventListener('mouseup', 结束拖动)
  window.removeEventListener('resize', 更新指示器位置)
})
</script>

<template>
  <div
    ref="滚动容器"
    class="content-tabs-scroll"
    :aria-label="props.ariaLabel"
    @mousedown="开始拖动"
    @wheel="处理滚轮"
  >
    <div class="content-tabs">
      <span class="content-tabs__indicator" :style="指示器样式" aria-hidden="true" />
      <button
        v-for="item in props.items"
        :key="item.value"
        :ref="(element) => 设置按钮引用(item.value, element as globalThis.Element | null)"
        type="button"
        class="content-tab"
        :class="{ 'content-tab--active': props.modelValue === item.value }"
        :disabled="item.disabled"
        :title="item.title || item.label"
        @click="选择标签(item.value, $event)"
      >
        <span>{{ item.label }}</span>
        <span v-if="props.showCount && item.count !== undefined" class="content-tab__count">{{ item.count }}</span>
      </button>
    </div>
  </div>
</template>

<style>
@import '../styles/content-tabs.css';
</style>
