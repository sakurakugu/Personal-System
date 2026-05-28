<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch, type Component } from 'vue'

type 分段值类型 = string | number

interface 分段选项 {
  label: string
  value: 分段值类型
  disabled?: boolean
  icon?: Component
  title?: string
}

const props = withDefaults(defineProps<{
  modelValue: 分段值类型
  options: readonly 分段选项[]
  ariaLabel?: string
  fullWidth?: boolean
  activeColor?: string
  activeTextColor?: string
  borderColor?: string
  size?: 'default' | 'small'
}>(), {
  ariaLabel: '分段切换',
  fullWidth: false,
  activeColor: 'var(--el-color-primary)',
  activeTextColor: '#fff',
  borderColor: 'color-mix(in srgb, var(--segmented-active-color) 24%, transparent)',
  size: 'default',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: 分段值类型): void
  (e: 'change', value: 分段值类型): void
}>()

const 根节点引用 = ref<HTMLElement | null>(null)
const 需要均分选项 = ref(false)
const 原始内容宽度 = ref(0)
let 尺寸观察器: ResizeObserver | null = null

const 组件样式 = computed(() => ({
  '--segmented-active-color': props.activeColor,
  '--segmented-active-text-color': props.activeTextColor,
  '--segmented-border-color': props.borderColor,
}))

function 更新均分状态() {
  if (props.fullWidth) {
    需要均分选项.value = true
    return
  }
  const 根节点 = 根节点引用.value
  if (!根节点 || 原始内容宽度.value <= 0) {
    需要均分选项.value = false
    return
  }
  需要均分选项.value = 根节点.clientWidth > 原始内容宽度.value + 1
}

async function 重新测量内容宽度() {
  const 根节点 = 根节点引用.value
  if (!根节点) {
    原始内容宽度.value = 0
    需要均分选项.value = false
    return
  }
  const 当前均分状态 = 需要均分选项.value
  if (当前均分状态) {
    需要均分选项.value = false
    await nextTick()
  }
  const 选项节点列表 = Array.from(根节点.querySelectorAll<HTMLElement>('.segmented-switch__option'))
  原始内容宽度.value = 选项节点列表.reduce((总宽度, 节点) => 总宽度 + 节点.getBoundingClientRect().width, 0)
  更新均分状态()
}

function 选择选项(value: 分段值类型, disabled?: boolean) {
  if (disabled || value === props.modelValue) {
    return
  }
  emit('update:modelValue', value)
  emit('change', value)
}

onMounted(() => {
  void 重新测量内容宽度()
  if (typeof ResizeObserver === 'undefined') {
    return
  }
  尺寸观察器 = new ResizeObserver(() => {
    更新均分状态()
  })
  if (根节点引用.value) {
    尺寸观察器.observe(根节点引用.value)
  }
})

onBeforeUnmount(() => {
  尺寸观察器?.disconnect()
})

watch(
  () => [props.options, props.fullWidth, props.size],
  () => {
    void 重新测量内容宽度()
  },
  { deep: true },
)
</script>

<template>
  <div
    ref="根节点引用"
    class="segmented-switch"
    :class="{
      'segmented-switch--full': fullWidth,
      'segmented-switch--distributed': 需要均分选项,
      'segmented-switch--small': size === 'small',
    }"
    :style="组件样式"
    role="radiogroup"
    :aria-label="ariaLabel"
  >
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      class="segmented-switch__option"
      :class="{
        'is-active': modelValue === option.value,
        'is-disabled': option.disabled,
        'is-icon-only': option.icon && !option.label,
      }"
      :aria-checked="modelValue === option.value"
      :title="option.title || option.label"
      :disabled="option.disabled"
      role="radio"
      @click="选择选项(option.value, option.disabled)"
    >
      <component :is="option.icon" v-if="option.icon" class="segmented-switch__icon" />
      <span v-if="option.label" class="segmented-switch__label">{{ option.label }}</span>
    </button>
  </div>
</template>

<style scoped>
.segmented-switch {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  max-width: 100%;
  border: 1px solid var(--segmented-border-color, var(--el-border-color, var(--border-color)));
  border-radius: 8px;
  background: var(--el-fill-color-blank, #fff);
}

.segmented-switch:not(.segmented-switch--full) {
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
}

.segmented-switch:not(.segmented-switch--full)::-webkit-scrollbar {
  display: none;
}

.segmented-switch--full {
  display: flex;
  width: 100%;
  overflow: hidden;
}

.segmented-switch__option {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  flex-shrink: 0;
  padding: 8px 16px;
  border: none;
  border-right: 1px solid var(--segmented-border-color, var(--el-border-color, var(--border-color)));
  background: transparent;
  color: var(--el-text-color-regular, var(--text-secondary));
  font-size: 14px;
  line-height: 1.2;
  white-space: nowrap;
  text-align: center;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.segmented-switch--small .segmented-switch__option {
  padding: 6px 12px;
  font-size: 13px;
}

.segmented-switch--full .segmented-switch__option,
.segmented-switch--distributed .segmented-switch__option {
  flex: 1;
  min-width: 0;
}

.segmented-switch__option:last-child {
  border-right: none;
}

.segmented-switch__option.is-icon-only {
  min-width: 40px;
  padding-inline: 10px;
}

.segmented-switch__option:hover {
  color: var(--el-color-primary);
  background: var(--el-fill-color-light, #f5f7fa);
}

.segmented-switch__option:focus-visible {
  position: relative;
  z-index: 1;
  outline: 2px solid var(--segmented-active-color);
  outline-offset: -2px;
}

.segmented-switch__option.is-active {
  background: var(--segmented-active-color);
  color: var(--segmented-active-text-color);
}

.segmented-switch__option.is-disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.segmented-switch__icon {
  width: 1em;
  height: 1em;
  flex-shrink: 0;
}

.segmented-switch__label {
  display: block;
  min-width: 0;
  white-space: nowrap;
}

.segmented-switch__icon + .segmented-switch__label {
  margin-left: 6px;
}

:global(.dark .segmented-switch) {
  background: var(--bg-secondary);
  border-color: var(--segmented-border-color, var(--border-color));
}

:global(.dark .segmented-switch__option) {
  border-right-color: var(--segmented-border-color, var(--border-color));
  color: var(--text-secondary);
}

:global(.dark .segmented-switch__option:hover) {
  background: var(--bg-hover);
  color: var(--text-primary);
}

:global(.dark .segmented-switch__option.is-active) {
  color: var(--segmented-active-text-color);
  background: var(--segmented-active-color);
}
</style>
