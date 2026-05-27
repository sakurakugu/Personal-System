<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onBeforeUnmount, ref } from 'vue'

interface Props {
  text: string
  成功提示?: string
  失败提示?: string
  无障碍标签?: string
  成功态时长?: number
}

const props = withDefaults(defineProps<Props>(), {
  成功提示: '已复制',
  失败提示: '复制失败',
  无障碍标签: '复制内容',
  成功态时长: 1500,
})

const 已复制 = ref(false)
let 重置定时器: number | null = null

function 清理定时器() {
  if (重置定时器 !== null) {
    window.clearTimeout(重置定时器)
    重置定时器 = null
  }
}

async function 执行复制() {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(props.text)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = props.text
      textarea.style.position = 'fixed'
      textarea.style.left = '-9999px'
      textarea.style.top = '0'
      document.body.appendChild(textarea)
      textarea.focus()
      textarea.select()
      const successful = document.execCommand('copy')
      document.body.removeChild(textarea)
      if (!successful) throw new Error('execCommand copy failed')
    }

    清理定时器()
    已复制.value = true
    重置定时器 = window.setTimeout(() => {
      已复制.value = false
      重置定时器 = null
    }, props.成功态时长)
    ElMessage.success(props.成功提示)
  } catch (error) {
    console.error('[复制按钮] 复制失败', error)
    ElMessage.error(props.失败提示)
  }
}

onBeforeUnmount(() => {
  清理定时器()
})
</script>

<template>
  <button
    type="button"
    :aria-label="无障碍标签"
    @click="执行复制"
  >
    <slot :已复制="已复制">
      <svg :class="['copy-icon', { hidden: 已复制 }]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
      <svg :class="['copy-icon', 'copy-success', { hidden: !已复制 }]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
      </svg>
    </slot>
  </button>
</template>

<style scoped>
.copy-icon {
  width: 0.875rem;
  height: 0.875rem;
}

.copy-success {
  color: #22c55e;
}

.hidden {
  display: none;
}
</style>
