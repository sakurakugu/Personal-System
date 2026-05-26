<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'
import { ElIcon, ElInput } from 'element-plus'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{
  modelValue: string
  placeholder: string
  inputName: string
  routeFullPath: string
  getRouteSearchValue: () => string
  onSearch: (replace?: boolean) => void | Promise<void>
  shouldReplace: () => boolean
  noDrag?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

type InputInstance = InstanceType<typeof ElInput>
const 默认防抖时间 = 250

const searchInputRef = ref<InputInstance | null>(null)
const 搜索框已激活 = ref(false)
const 搜索词 = computed({
  get: () => props.modelValue,
  set: (value: string) => emit('update:modelValue', value),
})

let 搜索防抖定时器: number | null = null
let 忽略下一次搜索监听 = false

function 获取搜索原生输入框() {
  return searchInputRef.value?.input ?? null
}

function 同步搜索框属性() {
  const input = 获取搜索原生输入框()
  if (!input) return
  input.type = 'search'
  input.name = props.inputName
  input.autocomplete = 'off'
  input.spellcheck = false
  input.readOnly = !搜索框已激活.value
  input.setAttribute('autocapitalize', 'off')
  input.setAttribute('autocorrect', 'off')
  input.setAttribute('enterkeyhint', 'search')
  input.setAttribute('data-form-type', 'other')
}

function 激活搜索框() {
  搜索框已激活.value = true
  同步搜索框属性()
}

function 重置搜索框防自动填充() {
  const input = 获取搜索原生输入框()
  if (!input || document.activeElement === input || 搜索词.value.trim()) return
  搜索框已激活.value = false
  同步搜索框属性()
}

function 清理搜索防抖定时器() {
  if (搜索防抖定时器 !== null) {
    window.clearTimeout(搜索防抖定时器)
    搜索防抖定时器 = null
  }
}

function 同步路由搜索词到输入框() {
  const 路由搜索词 = props.getRouteSearchValue()
  if (搜索词.value === 路由搜索词) return
  忽略下一次搜索监听 = true
  搜索词.value = 路由搜索词
}

function 触发搜索(replace = props.shouldReplace()) {
  清理搜索防抖定时器()
  return props.onSearch(replace)
}

onMounted(() => {
  void nextTick().then(() => {
    同步搜索框属性()
    同步路由搜索词到输入框()
  })
})

onBeforeUnmount(() => {
  清理搜索防抖定时器()
})

watch(
  () => props.getRouteSearchValue(),
  () => {
    同步路由搜索词到输入框()
  },
  { immediate: true },
)

watch(搜索词, (value, oldValue) => {
  if (忽略下一次搜索监听) {
    忽略下一次搜索监听 = false
    return
  }
  if (value.trim() === oldValue.trim()) return
  清理搜索防抖定时器()
  搜索防抖定时器 = window.setTimeout(() => {
    void 触发搜索()
  }, 默认防抖时间)
})

watch(
  () => props.routeFullPath,
  async () => {
    await nextTick()
    同步搜索框属性()
    重置搜索框防自动填充()
  },
)
</script>

<template>
  <div class="topbar-search-input" :class="{ 'topbar-search-input--no-drag': noDrag }" data-form-type="other">
    <input
      class="search-autofill-decoy"
      type="text"
      name="username"
      autocomplete="username"
      tabindex="-1"
      aria-hidden="true"
    >
    <input
      class="search-autofill-decoy"
      type="password"
      name="password"
      autocomplete="current-password"
      tabindex="-1"
      aria-hidden="true"
    >
    <ElInput
      ref="searchInputRef"
      v-model="搜索词"
      type="search"
      clearable
      :placeholder="placeholder"
      :name="inputName"
      autocomplete="off"
      spellcheck="false"
      autocapitalize="off"
      autocorrect="off"
      @focus="激活搜索框"
      @pointerdown.capture="激活搜索框"
      @blur="重置搜索框防自动填充"
      @clear="触发搜索()"
      @keyup.enter="触发搜索()"
    >
      <template #suffix>
        <slot name="suffix">
          <ElIcon class="topbar-search-input__icon" @click="触发搜索()">
            <Search />
          </ElIcon>
        </slot>
      </template>
    </ElInput>
  </div>
</template>

<style scoped>
.topbar-search-input {
  width: var(--topbar-search-width, 260px);
  min-width: var(--topbar-search-min-width, 220px);
  max-width: 100%;
}

.topbar-search-input--no-drag {
  -webkit-app-region: no-drag;
}

.search-autofill-decoy {
  position: absolute;
  top: 0;
  left: 0;
  width: 1px;
  height: 1px;
  padding: 0;
  border: 0;
  opacity: 0;
  pointer-events: none;
  transform: translateY(-200vh);
}

.topbar-search-input :deep(.el-input) {
  width: 100%;
  min-width: 0;
}

.topbar-search-input :deep(.el-input__wrapper) {
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.03);
  box-shadow: none !important;
  border: 1px solid transparent;
  transition: all 0.2s ease-out;
}

.topbar-search-input :deep(.el-input__wrapper:hover) {
  background: rgba(0, 0, 0, 0.05);
}

.topbar-search-input :deep(.el-input__wrapper.is-focus) {
  background: rgba(0, 0, 0, 0.06);
  border-color: color-mix(in srgb, var(--topbar-search-accent, var(--el-color-primary)) 16%, transparent);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
}

.topbar-search-input :deep(input[type='search']::-webkit-search-cancel-button) {
  -webkit-appearance: none;
  appearance: none;
  display: none;
}

.topbar-search-input :deep(input[type='search']::-ms-clear) {
  display: none;
}

.topbar-search-input__icon {
  cursor: pointer;
  color: rgba(0, 0, 0, 0.45);
  transition: color 0.2s;
}

.topbar-search-input__icon:hover {
  color: var(--topbar-search-accent, var(--el-color-primary));
}

:global(.dark) .topbar-search-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05) !important;
  box-shadow: none !important;
  border-color: transparent !important;
}

:global(.dark) .topbar-search-input :deep(.el-input__wrapper:hover) {
  background: rgba(255, 255, 255, 0.08) !important;
}

:global(.dark) .topbar-search-input :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.09) !important;
  border-color: color-mix(in srgb, var(--topbar-search-accent-bright, var(--el-color-primary-light-5)) 24%, transparent) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.22) !important;
}

:global(.dark) .topbar-search-input__icon {
  color: rgba(255, 255, 255, 0.5);
}

:global(.dark) .topbar-search-input__icon:hover {
  color: var(--topbar-search-accent-bright, var(--el-color-primary-light-5));
}
</style>
