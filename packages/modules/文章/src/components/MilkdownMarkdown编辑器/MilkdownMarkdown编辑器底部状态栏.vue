<script setup lang="ts">
interface 光标状态 {
  line: number
  selectedWords: number
  selectedCharacters: number
}

interface 编辑器统计 {
  lines: number
  words: number
  characters: number
}

defineProps<{
  modeLabel: string
  uploading: boolean
  cursorStatus: 光标状态
  stats: 编辑器统计
}>()
</script>

<template>
  <div class="milkdown-markdown-editor__footer">
    <div class="milkdown-markdown-editor__footer-left">
      <span class="milkdown-markdown-editor__footer-item">{{ modeLabel }}</span>
      <span v-if="uploading" class="milkdown-markdown-editor__footer-uploading">图片上传中...</span>
    </div>
    <div class="milkdown-markdown-editor__footer-right">
      <span class="milkdown-markdown-editor__footer-item">当前行 {{ cursorStatus.line }}</span>
      <span
        v-if="cursorStatus.selectedCharacters > 0"
        class="milkdown-markdown-editor__footer-item"
      >
        已选择 {{ cursorStatus.selectedWords }} 字 / {{ cursorStatus.selectedCharacters }} 字符
      </span>
      <span class="milkdown-markdown-editor__footer-item">共 {{ stats.lines }} 行</span>
      <span class="milkdown-markdown-editor__footer-item">{{ stats.words }} 字</span>
      <span class="milkdown-markdown-editor__footer-item">{{ stats.characters }} 字符</span>
    </div>
  </div>
</template>

<style scoped>
.milkdown-markdown-editor__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 24px;
  padding: 0 10px;
  box-sizing: border-box;
  border-top: 1px solid color-mix(in srgb, var(--el-border-color) 72%, transparent);
  background: var(--milkdown-markdown-editor-toolbar-bg, var(--el-bg-color-overlay));
  background-color: var(--milkdown-markdown-editor-toolbar-bg-color, var(--el-bg-color-overlay));
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1;
}

.milkdown-markdown-editor__footer-left,
.milkdown-markdown-editor__footer-right {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.milkdown-markdown-editor__footer-right {
  justify-content: flex-end;
  flex-wrap: wrap;
}

.milkdown-markdown-editor__footer-item {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  white-space: nowrap;
}

.milkdown-markdown-editor__footer-uploading {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  color: var(--el-color-primary);
  white-space: nowrap;
}

@media (max-width: 768px) {
  .milkdown-markdown-editor__footer {
    align-items: flex-start;
    flex-direction: column;
    gap: 0;
    padding: 2px 10px;
  }

  .milkdown-markdown-editor__footer-right {
    justify-content: flex-start;
  }
}
</style>
