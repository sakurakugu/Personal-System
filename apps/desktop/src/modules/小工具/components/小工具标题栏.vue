<script setup lang="ts">
import type { WidgetUtilityPanel } from '../types'
import { Close } from '@element-plus/icons-vue'
import { Icon } from '@iconify/vue'
import WidgetButton from './小工具按钮.vue'

defineProps<{
  activeUtilityPanel: WidgetUtilityPanel
  pinButtonIcon: string
  pinButtonIconClass: Record<string, boolean>
  pinButtonIconShellClass: Record<string, boolean>
  pinButtonTitle: string
  settingWidgetState: boolean
  todoListButtonTitle: string
  todoListExpanded: boolean
  widgetAlwaysOnTop: boolean
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
          <WidgetButton
            class="widget-header-brand__icon-button"
            :title="widgetSettingsButtonTitle"
            :active="activeUtilityPanel === 'settings'"
            @click="$emit('toggle-settings-panel')"
          >
            <template #icon>
              <span class="widget-header-brand__icon-shell">
                <Icon icon="mdi:checkbox-marked-circle-auto-outline" class="widget-header-brand__icon" />
              </span>
            </template>
          </WidgetButton>
          <WidgetButton
            class="widget-header-brand__text-button"
            variant="text"
            :title="todoListButtonTitle"
            :active="todoListExpanded"
            @click="$emit('toggle-todo-list')"
          >
            待办事项
          </WidgetButton>
        </div>
        <div class="widget-actions widget-no-drag">
          <WidgetButton
            class="pin-button"
            :title="pinButtonTitle"
            :active="widgetAlwaysOnTop || widgetMovable"
            :disabled="settingWidgetState"
            @mousedown="$emit('pin-long-press-start')"
            @mouseup="$emit('pin-long-press-end')"
            @mouseleave="$emit('pin-long-press-end')"
            @touchstart.passive="$emit('pin-long-press-start')"
            @touchend="$emit('pin-long-press-end')"
            @touchcancel="$emit('pin-long-press-end')"
            @click="$emit('pin-button-click')"
          >
            <template #icon>
              <span class="pin-button__icon-shell" :class="pinButtonIconShellClass">
                <Icon :icon="pinButtonIcon" class="pin-button__icon" :class="pinButtonIconClass" />
              </span>
            </template>
          </WidgetButton>
          <WidgetButton title="打开主窗口" @click="$emit('open-main-window')">
            <template #icon>
              <Icon icon="mdi:application-outline" />
            </template>
          </WidgetButton>
          <WidgetButton v-if="widgetShowCloseButton" title="关闭小工具" @click="$emit('close-window')">
            <template #icon>
              <Close />
            </template>
          </WidgetButton>
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

.widget-header-brand__icon-shell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.widget-header-brand__icon {
  font-size: 18px;
}

.widget-header-brand__text-button {
  min-width: 0;
}

.widget-actions {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  justify-content: flex-end;
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

.pin-button__icon-shell:has(.pin-button__icon--movable)::after {
  top: -3px;
  left: 10px;
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
