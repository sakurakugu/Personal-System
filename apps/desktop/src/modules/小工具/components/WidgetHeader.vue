<script setup lang="ts">
import type { WidgetUtilityPanel } from '../types'
import { Close } from '@element-plus/icons-vue'
import { Icon } from '@iconify/vue'
import { ElButton } from 'element-plus'

defineProps<{
  activeUtilityPanel: WidgetUtilityPanel
  pinButtonIcon: string
  pinButtonIconClass: Record<string, boolean>
  pinButtonIconShellClass: Record<string, boolean>
  pinButtonTitle: string
  settingWidgetState: boolean
  todoListButtonTitle: string
  todoListExpanded: boolean
  widgetMovable: boolean
  widgetSettingsButtonTitle: string
  widgetShowCloseButton: boolean
}>()

defineEmits<{
  'close-window': []
  'open-main-window': []
  'pin-button-click': []
  'pin-long-press-end': []
  'pin-long-press-start': []
  'toggle-settings-panel': []
  'toggle-todo-list': []
}>()
</script>

<template>
  <header class="widget-header">
    <div class="widget-header-card" :class="{ 'widget-header-card--drag': widgetMovable }">
      <div class="widget-header-card__inner">
        <div class="widget-header-brand widget-no-drag">
          <button
            class="widget-header-brand__icon-button"
            type="button"
            :title="widgetSettingsButtonTitle"
            :class="{ 'widget-header-brand__icon-button--active': activeUtilityPanel === 'settings' }"
            @click="$emit('toggle-settings-panel')"
          >
            <span class="widget-header-brand__icon-shell">
              <Icon icon="mdi:checkbox-marked-circle-auto-outline" class="widget-header-brand__icon" />
            </span>
          </button>
          <button
            class="widget-header-brand__text-button"
            type="button"
            :title="todoListButtonTitle"
            @click="$emit('toggle-todo-list')"
          >
            <span class="widget-header-brand__text" :class="{ 'widget-header-brand__text--active': todoListExpanded }">待办事项</span>
          </button>
        </div>
        <div class="widget-actions widget-no-drag">
          <ElButton
            class="widget-icon-button pin-button"
            plain
            :title="pinButtonTitle"
            :disabled="settingWidgetState"
            @mousedown="$emit('pin-long-press-start')"
            @mouseup="$emit('pin-long-press-end')"
            @mouseleave="$emit('pin-long-press-end')"
            @touchstart.passive="$emit('pin-long-press-start')"
            @touchend="$emit('pin-long-press-end')"
            @touchcancel="$emit('pin-long-press-end')"
            @click="$emit('pin-button-click')"
          >
            <span class="pin-button__icon-shell" :class="pinButtonIconShellClass">
              <Icon :icon="pinButtonIcon" class="pin-button__icon" :class="pinButtonIconClass" />
            </span>
          </ElButton>
          <ElButton class="widget-icon-button widget-action-button" plain title="打开主窗口" @click="$emit('open-main-window')">
            <Icon icon="mdi:application-outline" />
          </ElButton>
          <ElButton v-if="widgetShowCloseButton" class="widget-icon-button" :icon="Close" plain @click="$emit('close-window')" />
        </div>
      </div>
    </div>
  </header>
</template>

<style>
.widget-header {
  display: flex;
  justify-content: stretch;
  align-items: center;
  gap: 16px;
  padding: 0;
}

.widget-header-card {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  width: 100%;
  min-height: 46px;
  padding: 0 12px;
  border-radius: var(--widget-window-radius);
  border: none;
  background: var(--widget-surface-background);
  backdrop-filter: blur(10px);
}

.widget-shell--opaque .widget-header-card {
  backdrop-filter: none;
}

.widget-header-card--drag {
  -webkit-app-region: drag;
}

.widget-header-card__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0;
  width: 100%;
  min-height: 0;
}

.widget-header-brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  height: 34px;
  padding: 0;
  color: var(--desktop-text);
}

.widget-header-brand__icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
}

.widget-header-brand__icon-shell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--desktop-accent) 16%, transparent);
  color: var(--desktop-accent);
  flex-shrink: 0;
  transition: background-color 0.18s ease, transform 0.18s ease;
}

.widget-header-brand__icon-button--active .widget-header-brand__icon-shell {
  background: color-mix(in srgb, var(--desktop-accent) 28%, transparent);
  transform: scale(1.03);
}

.widget-header-brand__icon {
  font-size: 18px;
}

.widget-header-brand__text-button {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  height: 100%;
  padding: 0;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.widget-header-brand__text {
  display: inline-flex;
  align-items: center;
  height: 100%;
  padding: 0 10px;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.04em;
  white-space: nowrap;
  transition: background-color 0.18s ease;
}

.widget-header-brand__text--active {
  background: color-mix(in srgb, var(--desktop-accent) 10%, transparent);
}

.widget-actions {
  display: flex;
  gap: 0;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.widget-actions .el-button {
  border-color: color-mix(in srgb, var(--desktop-accent) 18%, var(--desktop-border));
  background: color-mix(in srgb, var(--desktop-accent) 8%, transparent);
  color: var(--desktop-text);
  border-radius: 8px;
}

.widget-actions .el-button + .el-button {
  margin-left: 5px;
}

.widget-actions .el-button:hover {
  border-color: color-mix(in srgb, var(--desktop-accent) 34%, var(--desktop-border));
  background: color-mix(in srgb, var(--desktop-accent) 14%, transparent);
}

.widget-action-button {
  font-size: 18px;
}

.pin-button {
  overflow: hidden;
}

.pin-button__icon-shell {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
}

.pin-button__icon {
  font-size: 18px;
  transition: transform 0.18s ease;
}

.pin-button__icon--movable {
  transform: rotate(35deg);
}

.pin-button__icon-shell::after {
  content: '';
  position: absolute;
  top: -1px;
  left: 8px;
  width: 1.5px;
  height: 20px;
  border-radius: 999px;
  background: currentcolor;
  opacity: 0;
  transform: rotate(-45deg);
  transform-origin: center;
  transition: opacity 0.18s ease;
  pointer-events: none;
}

.pin-button__icon-shell--unpinned::after {
  opacity: 0.92;
}
</style>
