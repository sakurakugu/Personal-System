<script setup lang="ts">
defineProps<{
  visible: boolean
  options: Array<{
    shortcode: string
    emoji: string
  }>
}>()

const emit = defineEmits<{
  close: []
  select: [shortcode: string]
}>()
</script>

<template>
  <div
    v-if="visible"
    class="milkdown-markdown-emoji-dialog"
    role="dialog"
    aria-modal="true"
    aria-label="选择全部 Emoji"
    @click.self="emit('close')"
  >
    <div class="milkdown-markdown-emoji-dialog__panel">
      <div class="milkdown-markdown-emoji-dialog__header">
        <strong>选择全部 Emoji</strong>
        <button
          class="milkdown-markdown-emoji-dialog__close"
          type="button"
          title="关闭"
          @click="emit('close')"
        >
          关闭
        </button>
      </div>
      <div class="milkdown-markdown-emoji-dialog__grid">
        <button
          v-for="option in options"
          :key="`full-${option.shortcode}`"
          class="milkdown-markdown-emoji-dialog__item"
          type="button"
          :title="`:${option.shortcode}:`"
          @click="emit('select', option.shortcode)"
        >
          <span class="milkdown-markdown-emoji-dialog__symbol">{{ option.emoji }}</span>
          <span class="milkdown-markdown-emoji-dialog__shortcode">:{{ option.shortcode }}:</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.milkdown-markdown-emoji-dialog {
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

.milkdown-markdown-emoji-dialog__panel {
  display: flex;
  flex-direction: column;
  width: min(760px, 100%);
  max-height: min(680px, 100%);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-bg-color-overlay);
  color: var(--el-text-color-primary);
  box-shadow: var(--el-box-shadow-dark);
}

.milkdown-markdown-emoji-dialog__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  box-sizing: border-box;
  border-bottom: 1px solid var(--el-border-color-light);
}

.milkdown-markdown-emoji-dialog__close {
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.milkdown-markdown-emoji-dialog__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(108px, 1fr));
  gap: 6px;
  padding: 12px;
  overflow: auto;
  scrollbar-width: thin;
}

.milkdown-markdown-emoji-dialog__item {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  min-height: 34px;
  padding: 0 8px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.milkdown-markdown-emoji-dialog__item:hover,
.milkdown-markdown-emoji-dialog__item:focus-visible {
  outline: none;
  background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
  color: var(--el-color-primary);
}

.milkdown-markdown-emoji-dialog__shortcode {
  min-width: 0;
  overflow: hidden;
  font: 12px/1.2 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
