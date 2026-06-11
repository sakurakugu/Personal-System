<script setup lang="ts">
import fullEmojiMap from 'markdown-it-emoji/lib/data/full.mjs'
import lightEmojiMap from 'markdown-it-emoji/lib/data/light.mjs'
import emojiShortcutsMap from 'markdown-it-emoji/lib/data/shortcuts.mjs'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import MilkdownMarkdown工具栏 from './MilkdownMarkdown工具栏/MilkdownMarkdown工具栏.vue'
import type {
  ToolbarItem,
  ToolbarOverflowMenuEntry,
} from './MilkdownMarkdown工具栏/MilkdownMarkdown工具栏类型'
import { 使用MilkdownMarkdown工具栏折叠 } from './MilkdownMarkdown工具栏/使用MilkdownMarkdown工具栏折叠'
import { 使用MilkdownMarkdown工具栏菜单 } from './MilkdownMarkdown工具栏/使用MilkdownMarkdown工具栏菜单'
import { 创建MilkdownMarkdown工具栏项 } from './MilkdownMarkdown工具栏/创建MilkdownMarkdown工具栏项'
import {
  buildCursorStatusFromOffsets,
  buildCursorStatusFromText,
  buildEditorStats,
} from './MilkdownMarkdown编辑器/Markdown编辑器统计'
import {
  buildCodeSyntaxSnippet,
  buildGithubAlertSyntaxSnippet,
} from './MilkdownMarkdown编辑器/Markdown自定义语法片段'
import MilkdownMarkdownEmoji选择弹窗 from './MilkdownMarkdown编辑器/MilkdownMarkdownEmoji选择弹窗.vue'
import MilkdownMarkdownGithub卡片弹窗 from './MilkdownMarkdown编辑器/MilkdownMarkdownGithub卡片弹窗.vue'
import {
  getMilkdownMarkdownFullscreenRoot,
  toggleMilkdownMarkdownPageFullscreen,
  toggleMilkdownMarkdownScreenFullscreen,
} from './MilkdownMarkdown编辑器/MilkdownMarkdown全屏'
import MilkdownMarkdown图片裁剪弹窗 from './MilkdownMarkdown编辑器/MilkdownMarkdown图片裁剪弹窗.vue'
import {
  buildTableMarkdown,
  normalizeCustomTableSize,
  更多表格最大行列,
  表格基础语法说明,
  表格行列选项,
} from './MilkdownMarkdown编辑器/MilkdownMarkdown工具栏动作辅助'
import MilkdownMarkdown编辑器底部状态栏 from './MilkdownMarkdown编辑器/MilkdownMarkdown编辑器底部状态栏.vue'
import type {
  MilkdownMarkdownImageUploader,
  MilkdownMarkdown编辑器实例,
} from './MilkdownMarkdown编辑器/MilkdownMarkdown编辑器类型'
import MilkdownMarkdown表格插入弹窗 from './MilkdownMarkdown编辑器/MilkdownMarkdown表格插入弹窗.vue'
import {
  GitHub卡片语法名称,
} from './MilkdownMarkdown编辑器/MilkdownMarkdown语法常量'
import MilkdownMarkdown语法说明弹窗 from './MilkdownMarkdown编辑器/MilkdownMarkdown语法说明弹窗.vue'
import { 使用Markdown常用表情 } from './MilkdownMarkdown编辑器/使用Markdown常用表情'
import { 使用MilkdownMarkdown图片上传 } from './MilkdownMarkdown编辑器/使用MilkdownMarkdown图片上传'
import { 使用MilkdownMarkdown工具栏动作 } from './MilkdownMarkdown编辑器/使用MilkdownMarkdown工具栏动作'
import { 使用MilkdownMarkdown源码模式 } from './MilkdownMarkdown编辑器/使用MilkdownMarkdown源码模式'
import { 使用MilkdownMarkdown滚动定位 } from './MilkdownMarkdown编辑器/使用MilkdownMarkdown滚动定位'
import { 使用MilkdownMarkdown编辑器核心 } from './MilkdownMarkdown编辑器/使用MilkdownMarkdown编辑器核心'

export type {
  MilkdownMarkdownImagePayload,
  MilkdownMarkdownImageUploader,
  MilkdownMarkdown编辑器实例
} from './MilkdownMarkdown编辑器/MilkdownMarkdown编辑器类型'

const props = withDefaults(defineProps<{
  modelValue: string
  placeholder?: string
  theme?: 'light' | 'dark'
  uploadImages?: MilkdownMarkdownImageUploader
  formatContent?: () => void | Promise<unknown>
  fullscreenRootSelector?: string
  scrollSync?: boolean
  showScrollSync?: boolean
  previewEnabled?: boolean
  previewLayoutMode?: 'split' | 'full'
  previewType?: 'preview' | 'html' | 'mindmap'
  showPreviewToggle?: boolean
  outlineVisible?: boolean
  showOutlineToggle?: boolean
}>(), {
  placeholder: '在此编写 Markdown 内容...',
  theme: 'light',
  uploadImages: undefined,
  formatContent: undefined,
  fullscreenRootSelector: '',
  scrollSync: true,
  showScrollSync: false,
  previewEnabled: false,
  previewLayoutMode: 'split',
  previewType: 'preview',
  showPreviewToggle: false,
  outlineVisible: false,
  showOutlineToggle: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  ready: []
  loadingChange: [value: boolean]
  uploadError: [error: unknown]
  modeChange: [sourceMode: boolean]
  'update:scrollSync': [value: boolean]
  'update:previewEnabled': [value: boolean]
  'update:previewLayoutMode': [value: 'split' | 'full']
  'update:previewType': [value: 'preview' | 'html' | 'mindmap']
  'update:outlineVisible': [value: boolean]
}>()

const rootRef = ref<HTMLDivElement | null>(null)
const toolbarRef = ref<InstanceType<typeof MilkdownMarkdown工具栏> | null>(null)
const contentRef = ref<HTMLDivElement | null>(null)
const sourceTextareaRef = ref<HTMLTextAreaElement | null>(null)
const hoveredTableRows = ref(3)
const hoveredTableCols = ref(3)
const tableDialogVisible = ref(false)
const tableDialogInitialRows = ref(8)
const tableDialogInitialCols = ref(8)
const emojiPickerMode = ref<'emoji' | 'kaomoji'>('emoji')
const emojiDialogVisible = ref(false)
const isSourceMode = ref(false)
const sourceContent = ref('')
const lastMarkdown = ref(props.modelValue)
const fileInputRef = ref<HTMLInputElement | null>(null)
const cropFileInputRef = ref<HTMLInputElement | null>(null)
const syntaxDialogVisible = ref(false)
const syntaxDialogTitle = ref('')
const syntaxDialogContent = ref('')
const githubCardDialogVisible = ref(false)
const cursorStatus = ref({
  line: 1,
  selectedWords: 0,
  selectedCharacters: 0,
})

const 全量Emoji选项 = Object.entries(fullEmojiMap).map(([shortcode, emoji]) => ({
  shortcode,
  emoji,
}))
const 轻量Emoji选项 = Object.entries(lightEmojiMap).map(([shortcode, emoji]) => ({
  shortcode,
  emoji,
}))
const 颜文字选项 = Object.entries(emojiShortcutsMap)
  .flatMap(([shortcode, shortcuts]) => shortcuts.map((shortcut) => ({
    shortcode,
    shortcut,
    emoji: fullEmojiMap[shortcode] ?? '',
  })))
const {
  常用Emoji选项,
  常用颜文字选项,
  初始化常用表情记录,
  记录常用Emoji,
  记录常用颜文字,
} = 使用Markdown常用表情()
const {
  editor,
  loading,
  createEditor,
  destroyEditor,
  getMarkdown,
  setMarkdown,
  formatMarkdown,
  insertMarkdown,
  getEditorView,
  redoEdit,
  undoEdit,
  toggleHighlight,
} = 使用MilkdownMarkdown编辑器核心({
  rootRef,
  sourceTextareaRef,
  isSourceMode,
  sourceContent,
  lastMarkdown,
  getModelValue: () => props.modelValue,
  updateCursorStatus,
  emitModelValue: (value) => emit('update:modelValue', value),
  emitReady: () => emit('ready'),
  emitLoadingChange: (value) => emit('loadingChange', value),
})
const {
  isUploading,
  imageCropDialogVisible,
  imageCropPreviewUrl,
  imageCropNaturalSize,
  imageCropRect,
  openImagePicker,
  handleFileInputChange,
  insertImageLink,
  openCropImagePicker,
  handleCropFileInputChange,
  releaseImageCropPreviewUrl,
  closeImageCropDialog,
  resetImageCropRect,
  confirmImageCropUpload,
  handleEditorPaste,
  handleEditorDrop,
} = 使用MilkdownMarkdown图片上传({
  fileInputRef,
  cropFileInputRef,
  获取上传图片函数: () => props.uploadImages,
  插入Markdown: (markdown) => insertMarkdown(markdown),
  聚焦编辑器: () => focus(),
  报告上传错误: (error) => emit('uploadError', error),
})
const {
  getScrollElement,
  getScrollRatio,
  setScrollRatio,
  scrollToHeading,
  记录模式切换前滚动位置,
  restoreScrollAfterModeSwitch,
} = 使用MilkdownMarkdown滚动定位({
  contentRef,
  isSourceMode,
  sourceTextareaRef,
  sourceContent,
  getEditorView,
  updateCursorStatus,
})
const {
  handleSourceInput,
  handleSourceKeydown,
  toggleSourceStrong,
  updateSourceSelectionStatus,
} = 使用MilkdownMarkdown源码模式({
  sourceTextareaRef,
  sourceContent,
  lastMarkdown,
  insertMarkdown,
  updateCursorStatus,
  emitModelValue: (value) => emit('update:modelValue', value),
})
const { runToolbarAction } = 使用MilkdownMarkdown工具栏动作({
  editor,
  isSourceMode,
  lastMarkdown,
  getMarkdown,
  insertMarkdown,
  undoEdit,
  redoEdit,
  toggleHighlight,
  toggleSourceStrong,
  toggleSourceMode,
  focus,
  openImagePicker,
  insertImageLink,
  openCropImagePicker,
  formatContent: () => props.formatContent?.(),
  getPreviewLayoutMode: () => props.previewLayoutMode,
  getPreviewType: () => props.previewType,
  getScrollSync: () => props.scrollSync,
  getPreviewEnabled: () => props.previewEnabled,
  getOutlineVisible: () => props.outlineVisible,
  emitModelValue: (value) => emit('update:modelValue', value),
  emitScrollSync: (value) => emit('update:scrollSync', value),
  emitPreviewEnabled: (value) => emit('update:previewEnabled', value),
  emitPreviewLayoutMode: (value) => emit('update:previewLayoutMode', value),
  emitPreviewType: (value) => emit('update:previewType', value),
  emitOutlineVisible: (value) => emit('update:outlineVisible', value),
  togglePageFullscreen,
  toggleScreenFullscreen,
  openGithubCardDialog,
  openCustomMarkdownSyntaxDialog,
})

const toolbarItems = 创建MilkdownMarkdown工具栏项({
  isUploading: () => isUploading.value,
  isSourceMode: () => isSourceMode.value,
  hasFormatContent: () => Boolean(props.formatContent),
  showScrollSync: () => props.showScrollSync,
  scrollSync: () => props.scrollSync,
  previewEnabled: () => props.previewEnabled,
  previewLayoutMode: () => props.previewLayoutMode,
  previewType: () => props.previewType,
  showPreviewToggle: () => props.showPreviewToggle,
  outlineVisible: () => props.outlineVisible,
  showOutlineToggle: () => props.showOutlineToggle,
})
const {
  toolbarOverflowCount,
  工具栏更多键,
  工具栏公式索引,
  工具栏折叠候选索引,
  shouldShowToolbarItem,
  shouldShowToolbarSeparator,
  初始化工具栏折叠监听,
  清理工具栏折叠监听,
  调度工具栏折叠更新,
} = 使用MilkdownMarkdown工具栏折叠({
  toolbarItems,
  getToolbarElement: 获取工具栏滚动元素,
  getRootElement: () => rootRef.value,
})
const {
  activeDropdownKey,
  activeDropdownStyle,
  activeOverflowSubmenuKey,
  toggleToolbarDropdown,
  openToolbarDropdown,
  toggleToolbarMoreDropdown,
  openToolbarMoreDropdown,
  handleToolbarOverflowMenuClick,
  openToolbarOverflowSubmenu,
  handleToolbarOverflowSubmenuClick,
  closeToolbarDropdown,
  handleDocumentPointerDown,
} = 使用MilkdownMarkdown工具栏菜单({
  moreKey: 工具栏更多键,
  getToolbarItemKey,
  runAction: runToolbarAction,
})
const 溢出工具栏菜单项 = computed<ToolbarOverflowMenuEntry[]>(() => {
  const entries: ToolbarOverflowMenuEntry[] = []
  const overflowIndexes = 工具栏折叠候选索引.value.slice(0, toolbarOverflowCount.value).reverse()

  for (const itemIndex of overflowIndexes) {
    const item = toolbarItems[itemIndex]
    if (!item) {
      continue
    }

    const icon = getToolbarIcon(item)
    if (!item.action) {
      continue
    }

    entries.push({
      kind: 'option',
      key: `${itemIndex}-${item.action}-${item.payload ?? item.label}`,
      label: item.label,
      title: getToolbarTitle(item),
      action: item.action,
      payload: item.payload,
      icon,
      disabled: item.disabled,
      children: item.dropdown?.map((option, optionIndex) => ({
        ...option,
        key: `${itemIndex}-${option.kind ?? 'option'}-${optionIndex}-${option.label}`,
      })),
    })
  }

  return entries
})
const currentMarkdown = computed(() => (isSourceMode.value ? sourceContent.value : lastMarkdown.value))
const editorStats = computed(() => buildEditorStats(currentMarkdown.value))
const editorModeLabel = computed(() => (isSourceMode.value ? '源码' : '所见即所得'))
const rootClass = computed(() => ({
  'milkdown-markdown-editor--dark': props.theme === 'dark',
  'milkdown-markdown-editor--source': isSourceMode.value,
  'milkdown-markdown-editor--uploading': isUploading.value,
}))
function getToolbarIcon(item: ToolbarItem) {
  return item.dynamicIcon?.() ?? item.icon
}

function getToolbarTitle(item: ToolbarItem) {
  return item.dynamicTitle?.() ?? item.title
}

function 获取工具栏滚动元素(): HTMLDivElement | null {
  return toolbarRef.value?.getScrollElement() ?? null
}

onMounted(async () => {
  初始化常用表情记录()
  document.addEventListener('pointerdown', handleDocumentPointerDown, true)
  await nextTick()
  初始化工具栏折叠监听()
  调度工具栏折叠更新()
  await createEditor()
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown, true)
  清理工具栏折叠监听()
  releaseImageCropPreviewUrl()
  destroyEditor()
})

watch(
  () => props.modelValue,
  (value) => {
    if (value === lastMarkdown.value) {
      return
    }

    lastMarkdown.value = value
    if (isSourceMode.value) {
      sourceContent.value = value
      return
    }

    setMarkdown(value)
  },
)

watch(isSourceMode, async (sourceMode) => {
  if (sourceMode) {
    sourceContent.value = getMarkdown()
    await nextTick()
    restoreScrollAfterModeSwitch()
    updateCursorStatus()
    聚焦源码输入框且保留滚动()
    emit('modeChange', sourceMode)
    return
  }

  setMarkdown(sourceContent.value)
  await nextTick()
  restoreScrollAfterModeSwitch()
  updateCursorStatus()
  聚焦可视编辑器且保留滚动()
  emit('modeChange', sourceMode)
})

watch(
  () => [
    props.showScrollSync,
    props.formatContent,
    props.showPreviewToggle,
    props.previewEnabled,
    props.previewLayoutMode,
    props.previewType,
    props.showOutlineToggle,
    props.outlineVisible,
  ] as const,
  () => 调度工具栏折叠更新(),
)

function focus() {
  if (isSourceMode.value) {
    聚焦源码输入框且保留滚动()
    return
  }

  聚焦可视编辑器且保留滚动()
}

function 聚焦源码输入框且保留滚动() {
  sourceTextareaRef.value?.focus({ preventScroll: true })
}

function 聚焦可视编辑器且保留滚动() {
  getEditorView()?.dom.focus({ preventScroll: true })
}

function updateCursorStatus() {
  if (isSourceMode.value) {
    const textarea = sourceTextareaRef.value
    const selectionStart = textarea?.selectionStart ?? 0
    const selectionEnd = textarea?.selectionEnd ?? selectionStart
    cursorStatus.value = buildCursorStatusFromOffsets(sourceContent.value, selectionStart, selectionEnd)
    return
  }

  const view = getEditorView()
  if (!view) {
    cursorStatus.value = buildCursorStatusFromOffsets(lastMarkdown.value, 0, 0)
    return
  }

  const { state } = view
  const beforeCursor = state.doc.textBetween(0, state.selection.from, '\n', '\n')
  const selectedText = state.doc.textBetween(state.selection.from, state.selection.to, '\n', '\n')
  cursorStatus.value = buildCursorStatusFromText(beforeCursor, selectedText)
}

function getToolbarItemKey(item: ToolbarItem, index: number): string {
  return `${item.type ?? 'button'}-${item.action ?? index}`
}

function toggleSourceMode() {
  记录模式切换前滚动位置()
  isSourceMode.value = !isSourceMode.value
}

function openCustomMarkdownSyntaxDialog(type: 'github-alert-syntax' | 'code-syntax') {
  syntaxDialogTitle.value = type === 'github-alert-syntax' ? 'GitHub 风格提示块语法' : '增强代码块语法'
  syntaxDialogContent.value = type === 'github-alert-syntax'
    ? buildGithubAlertSyntaxSnippet()
    : buildCodeSyntaxSnippet()
  syntaxDialogVisible.value = true
}

function closeSyntaxDialog() {
  syntaxDialogVisible.value = false
}

function insertEmojiShortcode(shortcode: string) {
  记录常用Emoji(shortcode)
  insertMarkdown(`:${shortcode}:`)
  closeEmojiDialog()
  closeToolbarDropdown()
  focus()
}

function insertKaomoji(value: string) {
  记录常用颜文字(value)
  insertMarkdown(value)
  closeToolbarDropdown()
  focus()
}

function openEmojiDialog() {
  emojiDialogVisible.value = true
  closeToolbarDropdown()
}

function closeEmojiDialog() {
  emojiDialogVisible.value = false
}

function openTableDialog() {
  tableDialogInitialRows.value = Math.max(8, hoveredTableRows.value)
  tableDialogInitialCols.value = Math.max(8, hoveredTableCols.value)
  tableDialogVisible.value = true
  closeToolbarDropdown()
}

function closeTableDialog() {
  tableDialogVisible.value = false
}

function confirmTableDialogInsert(payload: { row: number, col: number }) {
  const row = normalizeCustomTableSize(payload.row, 8)
  const col = normalizeCustomTableSize(payload.col, 8)
  tableDialogInitialRows.value = row
  tableDialogInitialCols.value = col
  insertMarkdown(buildTableMarkdown({ row, col }))
  closeTableDialog()
  focus()
}

function openGithubCardDialog() {
  githubCardDialogVisible.value = true
}

function closeGithubCardDialog() {
  githubCardDialogVisible.value = false
}

function confirmGithubCardInsert(repo: string) {
  insertMarkdown(`\n::${GitHub卡片语法名称}{repo="${repo}"}\n`)
  closeGithubCardDialog()
}

function getFullscreenRoot(): HTMLElement | null {
  return getMilkdownMarkdownFullscreenRoot(rootRef, props.fullscreenRootSelector)
}

function togglePageFullscreen() {
  toggleMilkdownMarkdownPageFullscreen(getFullscreenRoot())
}

async function toggleScreenFullscreen() {
  await toggleMilkdownMarkdownScreenFullscreen(getFullscreenRoot())
}

defineExpose<MilkdownMarkdown编辑器实例>({
  getMarkdown,
  setMarkdown,
  formatMarkdown,
  insertMarkdown,
  getEditorView,
  getScrollElement,
  getScrollRatio,
  setScrollRatio,
  scrollToHeading,
  redo: redoEdit,
  focus,
})
</script>

<template>
  <div
    class="milkdown-markdown-editor"
    :class="rootClass"
    @paste="handleEditorPaste"
    @drop="handleEditorDrop"
  >
    <MilkdownMarkdown工具栏
      ref="toolbarRef"
      v-model:hovered-table-rows="hoveredTableRows"
      v-model:hovered-table-cols="hoveredTableCols"
      v-model:emoji-picker-mode="emojiPickerMode"
      :dark="props.theme === 'dark'"
      :items="toolbarItems"
      :overflow-items="溢出工具栏菜单项"
      :active-dropdown-key="activeDropdownKey"
      :active-dropdown-style="activeDropdownStyle"
      :active-overflow-submenu-key="activeOverflowSubmenuKey"
      :toolbar-overflow-count="toolbarOverflowCount"
      :formula-index="工具栏公式索引"
      :more-key="工具栏更多键"
      :table-size-options="表格行列选项"
      :common-emoji-options="常用Emoji选项"
      :light-emoji-options="轻量Emoji选项"
      :common-kaomoji-options="常用颜文字选项"
      :kaomoji-options="颜文字选项"
      :get-item-key="getToolbarItemKey"
      :get-icon="getToolbarIcon"
      :get-title="getToolbarTitle"
      :should-show-item="shouldShowToolbarItem"
      :should-show-separator="shouldShowToolbarSeparator"
      @toggle-dropdown="toggleToolbarDropdown"
      @open-dropdown="openToolbarDropdown"
      @toggle-more-dropdown="toggleToolbarMoreDropdown"
      @open-more-dropdown="openToolbarMoreDropdown"
      @open-overflow-submenu="openToolbarOverflowSubmenu"
      @overflow-menu-click="handleToolbarOverflowMenuClick"
      @overflow-submenu-click="handleToolbarOverflowSubmenuClick"
      @run-action="runToolbarAction"
      @close-dropdown="closeToolbarDropdown"
      @open-table-dialog="openTableDialog"
      @insert-emoji-shortcode="insertEmojiShortcode"
      @insert-kaomoji="insertKaomoji"
      @open-emoji-dialog="openEmojiDialog"
    >
      <input
        ref="fileInputRef"
        class="milkdown-markdown-editor__file-input"
        type="file"
        accept="image/*"
        multiple
        @change="handleFileInputChange"
      >
      <input
        ref="cropFileInputRef"
        class="milkdown-markdown-editor__file-input"
        type="file"
        accept="image/*"
        @change="handleCropFileInputChange"
      >
    </MilkdownMarkdown工具栏>

    <div ref="contentRef" class="milkdown-markdown-editor__content">
      <div class="milkdown-markdown-editor__after-toolbar">
        <slot name="after-toolbar" />
        <slot name="content-header" />
      </div>
      <div
        v-show="!isSourceMode"
        ref="rootRef"
        class="milkdown-markdown-editor__milkdown"
        :data-placeholder="placeholder"
      />
      <textarea
        v-show="isSourceMode"
        ref="sourceTextareaRef"
        v-model="sourceContent"
        class="milkdown-markdown-editor__source"
        :placeholder="placeholder"
        @input="handleSourceInput"
        @keydown="handleSourceKeydown"
        @click="updateSourceSelectionStatus"
        @keyup="updateSourceSelectionStatus"
        @select="updateSourceSelectionStatus"
      />
      <div v-if="loading" class="milkdown-markdown-editor__loading">
        正在加载编辑器...
      </div>
    </div>

    <MilkdownMarkdown编辑器底部状态栏
      :mode-label="editorModeLabel"
      :uploading="isUploading"
      :cursor-status="cursorStatus"
      :stats="editorStats"
    />

    <MilkdownMarkdown图片裁剪弹窗
      v-model:rect="imageCropRect"
      :visible="imageCropDialogVisible"
      :preview-url="imageCropPreviewUrl"
      :natural-size="imageCropNaturalSize"
      :uploading="isUploading"
      @close="closeImageCropDialog"
      @reset="resetImageCropRect"
      @confirm="confirmImageCropUpload"
    />

    <MilkdownMarkdown语法说明弹窗
      :visible="syntaxDialogVisible"
      :title="syntaxDialogTitle"
      :content="syntaxDialogContent"
      @close="closeSyntaxDialog"
    />

    <MilkdownMarkdown表格插入弹窗
      :visible="tableDialogVisible"
      :initial-rows="tableDialogInitialRows"
      :initial-cols="tableDialogInitialCols"
      :max-size="更多表格最大行列"
      :syntax-preview="表格基础语法说明"
      @close="closeTableDialog"
      @confirm="confirmTableDialogInsert"
    />

    <MilkdownMarkdownEmoji选择弹窗
      :visible="emojiDialogVisible"
      :options="全量Emoji选项"
      @close="closeEmojiDialog"
      @select="insertEmojiShortcode"
    />

    <MilkdownMarkdownGithub卡片弹窗
      :visible="githubCardDialogVisible"
      @close="closeGithubCardDialog"
      @confirm="confirmGithubCardInsert"
    />
  </div>
</template>

<style scoped src="../styles/milkdown-markdown-editor-content.css"></style>

<style scoped>
.milkdown-markdown-editor {
  --milkdown-markdown-toolbar-height: 37px;
  --milkdown-markdown-primary: var(--primary, var(--el-color-primary));
  --milkdown-markdown-text-primary: var(--text-primary, var(--el-text-color-primary));
  --milkdown-markdown-text-secondary: var(--text-secondary, var(--el-text-color-secondary));
  --milkdown-markdown-text-tertiary: var(--text-tertiary, var(--el-text-color-placeholder));
  --milkdown-markdown-card-bg: var(--bg-card, var(--el-bg-color-overlay));
  --milkdown-markdown-soft-bg: color-mix(
    in srgb,
    var(--bg-secondary, var(--el-fill-color-light)) 72%,
    var(--milkdown-markdown-card-bg)
  );
  --milkdown-markdown-hover-bg: var(--bg-hover, color-mix(in srgb, var(--el-color-primary) 8%, transparent));
  --milkdown-markdown-border: var(--border-color, var(--el-border-color));
  --milkdown-markdown-inline-code-bg: color-mix(
    in srgb,
    var(--bg-secondary, var(--el-fill-color-light)) 72%,
    transparent
  );
  --milkdown-markdown-inline-code-text: color-mix(
    in srgb,
    var(--milkdown-markdown-text-secondary) 76%,
    var(--milkdown-markdown-text-primary)
  );
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 720px;
  min-height: 360px;
  overflow: hidden;
  border-radius: 12px;
  background: var(--milkdown-markdown-editor-bg, var(--el-bg-color-overlay));
  background-color: var(--milkdown-markdown-editor-bg-color, var(--el-bg-color-overlay));
  color: var(--milkdown-markdown-text-primary);
}

.milkdown-markdown-editor__file-input {
  display: none;
}

.milkdown-markdown-editor__after-toolbar {
  flex: 0 0 auto;
  min-height: 0;
}

.milkdown-markdown-editor__after-toolbar:empty {
  display: none;
}

.milkdown-markdown-editor__content {
  position: relative;
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  background: var(--milkdown-markdown-editor-content-bg, transparent);
  background-color: var(--milkdown-markdown-editor-content-bg-color, transparent);
}

.milkdown-markdown-editor__milkdown,
.milkdown-markdown-editor__source {
  width: 100%;
  flex: 1 0 auto;
  min-height: 100%;
  box-sizing: border-box;
}

.milkdown-markdown-editor__source {
  display: block;
  border: none;
  padding: 20px 24px;
  resize: none;
  outline: none;
  overflow: hidden;
  background: transparent;
  color: var(--milkdown-markdown-text-primary);
  caret-color: var(--milkdown-markdown-text-primary);
  font: 14px/1.7 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
}

.milkdown-markdown-editor__source::placeholder {
  color: var(--milkdown-markdown-text-tertiary);
}

.milkdown-markdown-editor__loading {
  position: absolute;
  inset: 0;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  background: color-mix(
    in srgb,
    var(--milkdown-markdown-editor-bg, var(--el-bg-color-overlay)) 86%,
    transparent
  );
  backdrop-filter: blur(3px);
}

.milkdown-markdown-editor--dark {
  --milkdown-markdown-text-primary: var(--text-primary, #f3f4f6);
  --milkdown-markdown-text-secondary: var(--text-secondary, #d1d5db);
  --milkdown-markdown-text-tertiary: var(--text-tertiary, #9ca3af);
  --milkdown-markdown-card-bg: var(--bg-card, var(--el-bg-color-overlay));
  --milkdown-markdown-soft-bg: color-mix(
    in srgb,
    var(--bg-secondary, var(--el-fill-color-light)) 82%,
    var(--milkdown-markdown-card-bg)
  );
  --milkdown-markdown-inline-code-bg: color-mix(
    in srgb,
    var(--bg-secondary, var(--el-fill-color-light)) 80%,
    transparent
  );
  --milkdown-markdown-inline-code-text: color-mix(
    in srgb,
    var(--milkdown-markdown-text-secondary) 76%,
    var(--milkdown-markdown-text-primary)
  );
  --milkdown-markdown-border: var(--border-color, var(--el-border-color));
  background: var(--milkdown-markdown-editor-bg, var(--el-bg-color-overlay));
  background-color: var(--milkdown-markdown-editor-bg-color, var(--el-bg-color-overlay));
}

.milkdown-markdown-editor--page-fullscreen {
  position: fixed;
  inset: 0;
  z-index: 3000;
  width: 100vw !important;
  height: 100dvh !important;
  min-height: 0;
  border-radius: 0;
  border: none;
  box-shadow: none;
}

@media (max-width: 768px) {
  .milkdown-markdown-editor {
    height: 560px;
  }

  .milkdown-markdown-editor__source {
    padding: 16px;
  }

}
</style>
