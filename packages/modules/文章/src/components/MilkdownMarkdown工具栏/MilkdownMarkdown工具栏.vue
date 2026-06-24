<script setup lang="ts">
import { ChevronRight, MoreHorizontal } from 'lucide-vue-next'
import type { Component } from 'vue'
import { ref } from 'vue'
import type {
  ToolbarAction,
  ToolbarItem,
  ToolbarOverflowMenuEntry,
  ToolbarOverflowMenuOption,
  ToolbarOverflowSubmenuEntry,
} from './MilkdownMarkdown工具栏类型'

type 工具栏载荷 = string | number | undefined
type 表情模式 = 'emoji' | 'kaomoji'

interface Emoji选项 {
  shortcode: string
  emoji: string
}

interface 颜文字选项 {
  shortcode: string
  shortcut: string
  emoji: string
}

const props = defineProps<{
  dark: boolean
  items: ToolbarItem[]
  overflowItems: ToolbarOverflowMenuEntry[]
  activeDropdownKey: string
  activeDropdownStyle: Record<string, string>
  activeOverflowSubmenuKey: string
  toolbarOverflowCount: number
  formulaIndex: number
  moreKey: string
  hoveredTableRows: number
  hoveredTableCols: number
  tableSizeOptions: number[]
  emojiPickerMode: 表情模式
  commonEmojiOptions: Emoji选项[]
  lightEmojiOptions: Emoji选项[]
  commonKaomojiOptions: 颜文字选项[]
  kaomojiOptions: 颜文字选项[]
  getItemKey: (item: ToolbarItem, index: number) => string
  getIcon: (item: ToolbarItem) => Component | undefined
  getTitle: (item: ToolbarItem) => string
  shouldShowItem: (item: ToolbarItem, index: number) => boolean
  shouldShowSeparator: (index: number) => boolean
}>()

const emit = defineEmits<{
  'update:hoveredTableRows': [value: number]
  'update:hoveredTableCols': [value: number]
  'update:emojiPickerMode': [value: 表情模式]
  toggleDropdown: [item: ToolbarItem, index: number, event: MouseEvent]
  openDropdown: [item: ToolbarItem, index: number, event: FocusEvent]
  toggleMoreDropdown: [event: MouseEvent]
  openMoreDropdown: [event: FocusEvent]
  openOverflowSubmenu: [entry: ToolbarOverflowMenuOption]
  overflowMenuClick: [entry: ToolbarOverflowMenuOption]
  overflowSubmenuClick: [entry: ToolbarOverflowSubmenuEntry]
  runAction: [action: ToolbarAction, payload?: 工具栏载荷]
  closeDropdown: []
  openTableDialog: []
  insertEmojiShortcode: [shortcode: string]
  insertKaomoji: [value: string]
  openEmojiDialog: []
}>()

const toolbarScrollRef = ref<HTMLDivElement | null>(null)

function 设置表格悬停(row: number, col: number) {
  emit('update:hoveredTableRows', row)
  emit('update:hoveredTableCols', col)
}

function 执行动作并关闭(action: ToolbarAction, payload?: 工具栏载荷) {
  emit('runAction', action, payload)
  emit('closeDropdown')
}

defineExpose({
  getScrollElement: () => toolbarScrollRef.value,
})
</script>

<template>
  <div
    class="milkdown-markdown-editor__toolbar"
    :class="{ 'milkdown-markdown-editor__toolbar--dark': dark }"
  >
    <div ref="toolbarScrollRef" class="milkdown-markdown-editor__toolbar-scroll">
      <template v-for="(item, itemIndex) in items" :key="getItemKey(item, itemIndex)">
        <span
          v-if="item.type === 'separator'"
          v-show="shouldShowSeparator(itemIndex)"
          class="milkdown-markdown-editor__toolbar-separator"
          :data-toolbar-index="itemIndex"
          aria-hidden="true"
        />
        <span
          v-else-if="item.type === 'spacer'"
          v-show="shouldShowItem(item, itemIndex)"
          class="milkdown-markdown-editor__toolbar-spacer"
          :data-toolbar-index="itemIndex"
          aria-hidden="true"
        />
        <div
          v-else-if="item.type === 'dropdown'"
          v-show="shouldShowItem(item, itemIndex)"
          class="milkdown-markdown-editor__toolbar-dropdown"
          :data-toolbar-index="itemIndex"
          @focusin="emit('openDropdown', item, itemIndex, $event)"
        >
          <button
            class="milkdown-markdown-editor__toolbar-button"
            type="button"
            :class="{ 'is-active': item.active?.() }"
            :title="getTitle(item)"
            :aria-label="getTitle(item)"
            :aria-pressed="item.active?.()"
            :disabled="item.disabled?.()"
            @click="emit('toggleDropdown', item, itemIndex, $event)"
          >
            <component
              :is="getIcon(item)"
              v-if="getIcon(item)"
              class="milkdown-markdown-editor__toolbar-icon"
              aria-hidden="true"
            />
          </button>
          <div
            v-if="activeDropdownKey === getItemKey(item, itemIndex)"
            class="milkdown-markdown-editor__toolbar-menu"
            :class="{
              'milkdown-markdown-editor__toolbar-menu--table': item.action === 'table',
              'milkdown-markdown-editor__toolbar-menu--emoji': item.action === 'emojiShortcode',
            }"
            :style="activeDropdownStyle"
          >
            <template v-if="item.action === 'table'">
              <div class="milkdown-markdown-editor__table-size-label">
                {{ hoveredTableRows }} x {{ hoveredTableCols }}
              </div>
              <div class="milkdown-markdown-editor__table-size-grid">
                <div
                  v-for="row in tableSizeOptions"
                  :key="`row-${row}`"
                  class="milkdown-markdown-editor__table-size-row"
                >
                  <button
                    v-for="col in tableSizeOptions"
                    :key="`${row}-${col}`"
                    class="milkdown-markdown-editor__table-size-cell"
                    type="button"
                    :title="`${row} x ${col}`"
                    :class="{
                      'is-active': row <= hoveredTableRows && col <= hoveredTableCols,
                    }"
                    @mouseenter="设置表格悬停(row, col)"
                    @focus="设置表格悬停(row, col)"
                    @click="执行动作并关闭('table', `${row}x${col}`)"
                  />
                </div>
              </div>
              <button
                class="milkdown-markdown-editor__toolbar-menu-item milkdown-markdown-editor__table-more-button"
                type="button"
                title="插入更多表格"
                @click="emit('openTableDialog')"
              >
                更多表格
              </button>
            </template>
            <template v-else-if="item.action === 'emojiShortcode'">
              <template v-if="emojiPickerMode === 'emoji' && commonEmojiOptions.length > 0">
                <div class="milkdown-markdown-editor__emoji-section-title">
                  常用 Emoji
                </div>
                <div class="milkdown-markdown-editor__emoji-common-grid">
                  <button
                    v-for="option in commonEmojiOptions"
                    :key="`common-${option.shortcode}`"
                    class="milkdown-markdown-editor__emoji-button"
                    type="button"
                    :title="`:${option.shortcode}:`"
                    @click="emit('insertEmojiShortcode', option.shortcode)"
                  >
                    <span class="milkdown-markdown-editor__emoji-symbol">{{ option.emoji }}</span>
                  </button>
                </div>
                <div class="milkdown-markdown-editor__emoji-divider" />
              </template>
              <template v-else-if="emojiPickerMode === 'kaomoji' && commonKaomojiOptions.length > 0">
                <div class="milkdown-markdown-editor__emoji-section-title">
                  常用颜文字
                </div>
                <div class="milkdown-markdown-editor__kaomoji-common-grid">
                  <button
                    v-for="option in commonKaomojiOptions"
                    :key="`common-kaomoji-${option.shortcut}`"
                    class="milkdown-markdown-editor__kaomoji-button"
                    type="button"
                    :title="option.shortcode ? `${option.shortcut} -> :${option.shortcode}:` : option.shortcut"
                    @click="emit('insertKaomoji', option.shortcut)"
                  >
                    {{ option.shortcut }}
                  </button>
                </div>
                <div class="milkdown-markdown-editor__emoji-divider" />
              </template>
              <div
                v-if="emojiPickerMode === 'emoji'"
                class="milkdown-markdown-editor__emoji-scroll-grid"
              >
                <button
                  v-for="option in lightEmojiOptions"
                  :key="`light-${option.shortcode}`"
                  class="milkdown-markdown-editor__emoji-button"
                  type="button"
                  :title="`:${option.shortcode}:`"
                  @click="emit('insertEmojiShortcode', option.shortcode)"
                >
                  <span class="milkdown-markdown-editor__emoji-symbol">{{ option.emoji }}</span>
                </button>
              </div>
              <div
                v-else
                class="milkdown-markdown-editor__kaomoji-scroll-list"
              >
                <button
                  v-for="option in kaomojiOptions"
                  :key="`kaomoji-${option.shortcode}-${option.shortcut}`"
                  class="milkdown-markdown-editor__kaomoji-row"
                  type="button"
                  :title="option.shortcode ? `${option.shortcut} -> :${option.shortcode}:` : option.shortcut"
                  @click="emit('insertKaomoji', option.shortcut)"
                >
                  <span>{{ option.shortcut }}</span>
                  <span v-if="option.emoji" class="milkdown-markdown-editor__kaomoji-emoji">{{ option.emoji }}</span>
                </button>
              </div>
              <div class="milkdown-markdown-editor__emoji-footer">
                <button
                  class="milkdown-markdown-editor__emoji-footer-button"
                  type="button"
                  :class="{ 'is-active': emojiPickerMode === 'emoji' }"
                  @click="emit('update:emojiPickerMode', 'emoji')"
                >
                  Emoji
                </button>
                <button
                  class="milkdown-markdown-editor__emoji-footer-button"
                  type="button"
                  :class="{ 'is-active': emojiPickerMode === 'kaomoji' }"
                  @click="emit('update:emojiPickerMode', 'kaomoji')"
                >
                  颜文字
                </button>
                <button
                  class="milkdown-markdown-editor__emoji-footer-button"
                  type="button"
                  @click="emit('openEmojiDialog')"
                >
                  更多
                </button>
              </div>
            </template>
            <template v-else>
              <template v-for="option in item.dropdown" :key="`${option.kind ?? 'option'}-${option.label}-${option.kind === 'option' ? option.payload ?? option.action : ''}`">
                <div
                  v-if="option.kind === 'divider'"
                  class="milkdown-markdown-editor__toolbar-menu-divider"
                >
                  {{ option.label }}
                </div>
                <button
                  v-else
                  class="milkdown-markdown-editor__toolbar-menu-item"
                  type="button"
                  :title="option.title"
                  @click="执行动作并关闭(option.action, option.payload)"
                >
                  {{ option.label }}
                </button>
              </template>
            </template>
          </div>
        </div>
        <button
          v-else
          v-show="shouldShowItem(item, itemIndex)"
          class="milkdown-markdown-editor__toolbar-button"
          type="button"
          :data-toolbar-index="itemIndex"
          :class="{ 'is-active': item.active?.() }"
          :title="getTitle(item)"
          :aria-label="getTitle(item)"
          :aria-pressed="item.active?.()"
          :disabled="item.disabled?.()"
          @click="item.action && emit('runAction', item.action, item.payload)"
        >
          <component
            :is="getIcon(item)"
            v-if="getIcon(item)"
            class="milkdown-markdown-editor__toolbar-icon"
            aria-hidden="true"
          />
          <span
            v-else
            class="milkdown-markdown-editor__toolbar-text"
            :class="`milkdown-markdown-editor__toolbar-text--${item.action}`"
          >
            {{ item.label }}
          </span>
        </button>
        <div
          v-if="itemIndex === formulaIndex && toolbarOverflowCount > 0"
          class="milkdown-markdown-editor__toolbar-dropdown"
          data-toolbar-more
          @focusin="emit('openMoreDropdown', $event)"
        >
          <button
            class="milkdown-markdown-editor__toolbar-button"
            type="button"
            title="更多"
            aria-label="更多"
            :aria-expanded="activeDropdownKey === moreKey"
            @click="emit('toggleMoreDropdown', $event)"
          >
            <MoreHorizontal
              class="milkdown-markdown-editor__toolbar-icon"
              aria-hidden="true"
            />
          </button>
          <div
            v-if="activeDropdownKey === moreKey"
            class="milkdown-markdown-editor__toolbar-menu milkdown-markdown-editor__toolbar-menu--more"
            :style="activeDropdownStyle"
          >
            <template v-for="entry in overflowItems" :key="entry.key">
              <div
                v-if="entry.kind === 'divider'"
                class="milkdown-markdown-editor__toolbar-menu-divider"
              >
                {{ entry.label }}
              </div>
              <div
                v-else
                class="milkdown-markdown-editor__toolbar-menu-submenu"
                :class="{ 'is-open': activeOverflowSubmenuKey === entry.key }"
                @mouseenter="emit('openOverflowSubmenu', entry)"
                @focusin="emit('openOverflowSubmenu', entry)"
              >
                <button
                  class="milkdown-markdown-editor__toolbar-menu-item milkdown-markdown-editor__toolbar-menu-item--with-icon"
                  type="button"
                  :title="entry.title"
                  :disabled="entry.disabled?.()"
                  :aria-haspopup="entry.children?.length ? 'menu' : undefined"
                  :aria-expanded="entry.children?.length ? activeOverflowSubmenuKey === entry.key : undefined"
                  @click="emit('overflowMenuClick', entry)"
                >
                  <component
                    :is="entry.icon"
                    v-if="entry.icon"
                    class="milkdown-markdown-editor__toolbar-menu-icon"
                    aria-hidden="true"
                  />
                  <span
                    v-else
                    class="milkdown-markdown-editor__toolbar-menu-icon milkdown-markdown-editor__toolbar-menu-icon--empty"
                    aria-hidden="true"
                  />
                  <span class="milkdown-markdown-editor__toolbar-menu-text">{{ entry.label }}</span>
                  <ChevronRight
                    v-if="entry.children?.length"
                    class="milkdown-markdown-editor__toolbar-menu-arrow"
                    aria-hidden="true"
                  />
                </button>
                <div
                  v-if="entry.children?.length && activeOverflowSubmenuKey === entry.key"
                  class="milkdown-markdown-editor__toolbar-submenu"
                >
                  <template v-for="childEntry in entry.children" :key="childEntry.key">
                    <div
                      v-if="childEntry.kind === 'divider'"
                      class="milkdown-markdown-editor__toolbar-menu-divider"
                    >
                      {{ childEntry.label }}
                    </div>
                    <button
                      v-else
                      class="milkdown-markdown-editor__toolbar-menu-item"
                      type="button"
                      :title="childEntry.title"
                      @click="emit('overflowSubmenuClick', childEntry)"
                    >
                      {{ childEntry.label }}
                    </button>
                  </template>
                </div>
              </div>
            </template>
          </div>
        </div>
      </template>
    </div>
    <slot />
  </div>
</template>

<style scoped>
.milkdown-markdown-editor__toolbar {
  display: flex;
  align-items: center;
  flex: 0 0 var(--milkdown-markdown-toolbar-height);
  height: var(--milkdown-markdown-toolbar-height);
  min-height: var(--milkdown-markdown-toolbar-height);
  max-height: var(--milkdown-markdown-toolbar-height);
  padding: 4px 8px;
  box-sizing: border-box;
  border-bottom: 1px solid color-mix(in srgb, var(--el-border-color) 82%, transparent);
  background: var(--milkdown-markdown-editor-toolbar-bg, var(--el-bg-color-overlay));
  background-color: var(--milkdown-markdown-editor-toolbar-bg-color, var(--el-bg-color-overlay));
  overflow: visible;
}

.milkdown-markdown-editor__toolbar-scroll {
  display: flex;
  align-items: center;
  width: 100%;
  height: 28px;
  min-width: 0;
  flex-wrap: nowrap;
  overflow-x: hidden;
  overflow-y: visible;
}

.milkdown-markdown-editor__toolbar-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--el-text-color-primary);
  font-size: 13px;
  line-height: 1;
  cursor: pointer;
  flex: 0 0 auto;
  transition:
    background-color 0.16s ease,
    color 0.16s ease;
}

.milkdown-markdown-editor__toolbar-button:hover {
  background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
  color: var(--el-color-primary);
}

.milkdown-markdown-editor__toolbar-button.is-active {
  background: color-mix(in srgb, var(--el-color-primary) 14%, transparent);
  color: var(--el-color-primary);
}

.milkdown-markdown-editor__toolbar-button:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--el-color-primary) 40%, transparent);
  outline-offset: 1px;
}

.milkdown-markdown-editor__toolbar-button:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.milkdown-markdown-editor__toolbar-icon {
  width: 16px;
  height: 16px;
  stroke-width: 2;
}

.milkdown-markdown-editor__toolbar-text {
  font-weight: 700;
  font-family: Arial, Helvetica, sans-serif;
}

.milkdown-markdown-editor__toolbar-text--emphasis {
  font-style: italic;
}

.milkdown-markdown-editor__toolbar-text--strikethrough {
  text-decoration: line-through;
}

.milkdown-markdown-editor__toolbar-separator {
  display: inline-block;
  flex: 0 0 auto;
  width: 1px;
  height: 18px;
  margin: 0 6px;
  background: color-mix(in srgb, var(--el-border-color) 76%, transparent);
}

.milkdown-markdown-editor__toolbar-spacer {
  flex: 1 1 auto;
  min-width: 12px;
}

.milkdown-markdown-editor__toolbar-dropdown {
  position: relative;
  display: inline-flex;
  align-items: center;
  flex: 0 0 auto;
  height: 28px;
}

.milkdown-markdown-editor__toolbar-menu {
  position: fixed;
  z-index: 4000;
  min-width: 116px;
  padding: 6px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  background: var(--el-bg-color-overlay);
  box-shadow: var(--el-box-shadow-light);
}

.milkdown-markdown-editor__toolbar-menu--table {
  width: max-content;
  min-width: 0;
}

.milkdown-markdown-editor__toolbar-menu--emoji {
  width: 240px;
}

.milkdown-markdown-editor__toolbar-menu--more {
  min-width: 148px;
}

.milkdown-markdown-editor__toolbar-menu-divider {
  display: flex;
  align-items: center;
  min-height: 24px;
  padding: 6px 10px 2px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
}

.milkdown-markdown-editor__toolbar-menu-divider:not(:first-child) {
  margin-top: 4px;
  border-top: 1px solid color-mix(in srgb, var(--el-border-color) 70%, transparent);
}

.milkdown-markdown-editor__toolbar-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-height: 28px;
  padding: 0 10px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--el-text-color-primary);
  font-size: 13px;
  text-align: left;
  white-space: nowrap;
  cursor: pointer;
}

.milkdown-markdown-editor__toolbar-menu-item--with-icon {
  min-width: 136px;
}

.milkdown-markdown-editor__toolbar-menu-submenu {
  position: relative;
}

.milkdown-markdown-editor__toolbar-menu-icon {
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
  stroke-width: 2;
}

.milkdown-markdown-editor__toolbar-menu-icon--empty {
  display: inline-block;
}

.milkdown-markdown-editor__toolbar-menu-text {
  min-width: 0;
  flex: 1 1 auto;
  overflow: hidden;
  text-overflow: ellipsis;
}

.milkdown-markdown-editor__toolbar-menu-arrow {
  width: 14px;
  height: 14px;
  flex: 0 0 auto;
  color: var(--el-text-color-secondary);
  stroke-width: 2;
}

.milkdown-markdown-editor__toolbar-submenu {
  position: absolute;
  top: 0;
  left: calc(100% + 4px);
  z-index: 4001;
  min-width: 132px;
  padding: 6px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  background: var(--el-bg-color-overlay);
  box-shadow: var(--el-box-shadow-light);
}

.milkdown-markdown-editor__toolbar-menu-item:hover,
.milkdown-markdown-editor__toolbar-menu-submenu.is-open > .milkdown-markdown-editor__toolbar-menu-item,
.milkdown-markdown-editor__toolbar-menu-item:focus-visible {
  outline: none;
  background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
  color: var(--el-color-primary);
}

.milkdown-markdown-editor__toolbar-menu-item:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.milkdown-markdown-editor__table-size-label {
  margin-bottom: 6px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.4;
  text-align: center;
}

.milkdown-markdown-editor__table-size-grid {
  display: grid;
  gap: 3px;
}

.milkdown-markdown-editor__table-size-row {
  display: grid;
  grid-template-columns: repeat(6, 16px);
  gap: 3px;
  padding: 0;
  border: none;
  background: transparent;
}

.milkdown-markdown-editor__table-size-cell {
  width: 16px;
  height: 16px;
  box-sizing: border-box;
  border: 1px solid var(--el-border-color);
  border-radius: 2px;
  background: var(--el-bg-color);
  cursor: pointer;
}

.milkdown-markdown-editor__table-size-cell.is-active {
  border-color: var(--el-color-primary);
  background: color-mix(in srgb, var(--el-color-primary) 18%, var(--el-bg-color));
}

.milkdown-markdown-editor__table-more-button {
  position: relative;
  justify-content: center;
  margin-top: 6px;
  padding-top: 5px;
  background: transparent;
  text-align: center;
}

.milkdown-markdown-editor__table-more-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  border-top: 1px solid color-mix(in srgb, var(--el-border-color) 70%, transparent);
}

.milkdown-markdown-editor__table-more-button::after {
  content: '';
  position: absolute;
  inset: 5px 0 0;
  z-index: -1;
  border-radius: 4px;
  background: color-mix(in srgb, var(--el-color-primary) 5%, transparent);
}

.milkdown-markdown-editor__table-more-button:hover,
.milkdown-markdown-editor__table-more-button:focus-visible {
  background: transparent;
}

.milkdown-markdown-editor__table-more-button:hover::after,
.milkdown-markdown-editor__table-more-button:focus-visible::after {
  background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
}

.milkdown-markdown-editor__emoji-section-title {
  display: flex;
  align-items: center;
  min-height: 22px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-weight: 600;
}

.milkdown-markdown-editor__emoji-common-grid,
.milkdown-markdown-editor__emoji-scroll-grid {
  display: grid;
  grid-template-columns: repeat(8, 24px);
  gap: 3px;
}

.milkdown-markdown-editor__emoji-scroll-grid {
  max-height: 150px;
  overflow: auto;
  padding-right: 2px;
  scrollbar-width: thin;
}

.milkdown-markdown-editor__emoji-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.milkdown-markdown-editor__emoji-button:hover,
.milkdown-markdown-editor__emoji-button:focus-visible,
.milkdown-markdown-editor__kaomoji-button:hover,
.milkdown-markdown-editor__kaomoji-button:focus-visible,
.milkdown-markdown-editor__kaomoji-row:hover,
.milkdown-markdown-editor__kaomoji-row:focus-visible {
  outline: none;
  background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
  color: var(--el-color-primary);
}

.milkdown-markdown-editor__emoji-symbol {
  font-size: 18px;
  line-height: 1;
}

.milkdown-markdown-editor__kaomoji-common-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 4px;
}

.milkdown-markdown-editor__kaomoji-button,
.milkdown-markdown-editor__kaomoji-row {
  min-height: 26px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--el-text-color-primary);
  font: 13px/1.2 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  cursor: pointer;
}

.milkdown-markdown-editor__kaomoji-button {
  padding: 0 7px;
  text-align: center;
}

.milkdown-markdown-editor__kaomoji-scroll-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 2px;
  max-height: 150px;
  overflow: auto;
  padding-right: 2px;
  scrollbar-width: thin;
}

.milkdown-markdown-editor__kaomoji-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  width: 100%;
  padding: 0 8px;
  text-align: left;
}

.milkdown-markdown-editor__kaomoji-emoji {
  flex: 0 0 auto;
  font-size: 16px;
}

.milkdown-markdown-editor__emoji-divider {
  margin: 6px 0;
  border-top: 1px solid color-mix(in srgb, var(--el-border-color) 70%, transparent);
}

.milkdown-markdown-editor__emoji-footer {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 4px;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid color-mix(in srgb, var(--el-border-color) 70%, transparent);
}

.milkdown-markdown-editor__emoji-footer-button {
  min-height: 26px;
  padding: 0 6px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  font-size: 12px;
  cursor: pointer;
}

.milkdown-markdown-editor__emoji-footer-button:hover,
.milkdown-markdown-editor__emoji-footer-button:focus-visible,
.milkdown-markdown-editor__emoji-footer-button.is-active {
  border-color: var(--el-color-primary);
  outline: none;
  color: var(--el-color-primary);
}

.milkdown-markdown-editor__toolbar--dark .milkdown-markdown-editor__toolbar-button {
  color: #fff;
}

.milkdown-markdown-editor__toolbar--dark .milkdown-markdown-editor__toolbar-icon {
  color: #fff;
  stroke: currentColor;
}

@media (max-width: 768px) {
  .milkdown-markdown-editor__toolbar {
    align-items: stretch;
  }
}
</style>
