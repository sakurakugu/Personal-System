<script setup lang="ts">
defineProps<{
  visible: boolean
  title: string
  content: string
}>()

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <div
    v-if="visible"
    class="milkdown-markdown-syntax-dialog"
    role="dialog"
    aria-modal="true"
    :aria-label="title"
    @click.self="emit('close')"
  >
    <div class="milkdown-markdown-syntax-dialog__panel">
      <div class="milkdown-markdown-syntax-dialog__header">
        <strong>{{ title }}</strong>
        <button
          class="milkdown-markdown-syntax-dialog__close"
          type="button"
          title="关闭"
          @click="emit('close')"
        >
          关闭
        </button>
      </div>
      <pre class="milkdown-markdown-syntax-dialog__content"><code>{{ content }}</code></pre>
    </div>
  </div>
</template>

<style scoped>
.milkdown-markdown-syntax-dialog {
  position: fixed;
  inset: 0;
  z-index: 4100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  box-sizing: border-box;
  background: rgba(15, 23, 42, 0.48);
}

.milkdown-markdown-syntax-dialog__panel {
  display: flex;
  flex-direction: column;
  width: min(720px, 100%);
  max-height: min(680px, 100%);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-bg-color-overlay);
  color: var(--el-text-color-primary);
  box-shadow: var(--el-box-shadow-dark);
}

.milkdown-markdown-syntax-dialog__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  box-sizing: border-box;
  border-bottom: 1px solid var(--el-border-color-light);
}

.milkdown-markdown-syntax-dialog__close {
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.milkdown-markdown-syntax-dialog__content {
  margin: 0;
  padding: 16px;
  overflow: auto;
  background: color-mix(in srgb, var(--el-fill-color-light) 72%, var(--el-bg-color));
  color: var(--el-text-color-primary);
  font: 13px/1.7 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
</style>
