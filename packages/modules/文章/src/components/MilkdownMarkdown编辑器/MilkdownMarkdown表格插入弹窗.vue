<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

const props = defineProps<{
  visible: boolean
  initialRows: number
  initialCols: number
  maxSize: number
  syntaxPreview: string
}>()

const emit = defineEmits<{
  close: []
  confirm: [payload: { row: number, col: number }]
}>()

const rows = ref(8)
const cols = ref(8)
const rowsInputRef = ref<HTMLInputElement | null>(null)

watch(
  () => props.visible,
  async (visible) => {
    if (!visible) {
      return
    }

    rows.value = props.initialRows
    cols.value = props.initialCols
    await nextTick()
    rowsInputRef.value?.focus()
  },
)

function confirm() {
  emit('confirm', {
    row: rows.value,
    col: cols.value,
  })
}
</script>

<template>
  <div
    v-if="visible"
    class="milkdown-markdown-table-dialog"
    role="dialog"
    aria-modal="true"
    aria-label="插入更多表格"
    @click.self="emit('close')"
  >
    <form class="milkdown-markdown-table-dialog__panel" @submit.prevent="confirm">
      <div class="milkdown-markdown-table-dialog__header">
        <strong>插入更多表格</strong>
        <button
          class="milkdown-markdown-table-dialog__close"
          type="button"
          title="关闭"
          @click="emit('close')"
        >
          关闭
        </button>
      </div>
      <div class="milkdown-markdown-table-dialog__body">
        <div class="milkdown-markdown-table-dialog__fields">
          <label class="milkdown-markdown-table-dialog__field">
            <span>行数</span>
            <input
              ref="rowsInputRef"
              v-model.number="rows"
              class="milkdown-markdown-table-dialog__input"
              type="number"
              min="1"
              :max="maxSize"
              step="1"
            >
          </label>
          <label class="milkdown-markdown-table-dialog__field">
            <span>列数</span>
            <input
              v-model.number="cols"
              class="milkdown-markdown-table-dialog__input"
              type="number"
              min="1"
              :max="maxSize"
              step="1"
            >
          </label>
        </div>
        <div class="milkdown-markdown-table-dialog__preview">
          <span class="milkdown-markdown-table-dialog__preview-title">表格语法</span>
          <pre class="milkdown-markdown-table-dialog__preview-content"><code>{{ syntaxPreview }}</code></pre>
        </div>
      </div>
      <div class="milkdown-markdown-table-dialog__footer">
        <span>最大支持 {{ maxSize }} x {{ maxSize }}</span>
        <div class="milkdown-markdown-table-dialog__actions">
          <button type="button" @click="emit('close')">取消</button>
          <button type="submit" class="is-primary">插入</button>
        </div>
      </div>
    </form>
  </div>
</template>

<style scoped>
.milkdown-markdown-table-dialog {
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

.milkdown-markdown-table-dialog__panel {
  display: flex;
  flex-direction: column;
  width: min(620px, 100%);
  max-height: min(680px, 100%);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-bg-color-overlay);
  color: var(--el-text-color-primary);
  box-shadow: var(--el-box-shadow-dark);
}

.milkdown-markdown-table-dialog__header,
.milkdown-markdown-table-dialog__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  box-sizing: border-box;
  border-bottom: 1px solid var(--el-border-color-light);
}

.milkdown-markdown-table-dialog__footer {
  border-top: 1px solid var(--el-border-color-light);
  border-bottom: none;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.milkdown-markdown-table-dialog__body {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px 14px;
  box-sizing: border-box;
  overflow: auto;
}

.milkdown-markdown-table-dialog__fields,
.milkdown-markdown-table-dialog__actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.milkdown-markdown-table-dialog__field {
  display: flex;
  flex: 1 1 0;
  flex-direction: column;
  gap: 8px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.milkdown-markdown-table-dialog__input {
  min-height: 34px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  outline: none;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  font: inherit;
}

.milkdown-markdown-table-dialog__input:focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-primary) 18%, transparent);
}

.milkdown-markdown-table-dialog__preview {
  display: flex;
  min-height: 0;
  flex-direction: column;
  gap: 8px;
}

.milkdown-markdown-table-dialog__preview-title {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.milkdown-markdown-table-dialog__preview-content {
  max-height: 300px;
  margin: 0;
  padding: 12px;
  overflow: auto;
  border-radius: 6px;
  background: color-mix(in srgb, var(--el-fill-color-light) 72%, var(--el-bg-color));
  color: var(--el-text-color-primary);
  font: 13px/1.7 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
}

.milkdown-markdown-table-dialog__close,
.milkdown-markdown-table-dialog__actions button {
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.milkdown-markdown-table-dialog__actions button.is-primary {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary);
  color: #fff;
}
</style>
