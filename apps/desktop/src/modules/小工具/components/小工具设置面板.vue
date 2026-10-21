<script setup lang="ts">
import { RefreshLeft } from '@element-plus/icons-vue'
import { GlassRangeSlider, ThemeHuePanel } from '@personal-system/ui'
import { ElSwitch } from 'element-plus'
import { computed } from 'vue'
import WidgetButton from './小工具按钮.vue'

const props = defineProps<{
  authenticated: boolean
  defaultThemeHue: number
  defaultWidgetSurfaceOpacity: number
  themeHue: number
  userName: string
  widgetShowCloseButton: boolean
  widgetSurfaceOpacity: number
}>()

defineEmits<{
  'open-web-console': []
  'reset-widget-surface-opacity': []
  'update:theme-hue': [value: number]
  'update:widget-show-close-button': [value: boolean]
  'update:widget-surface-opacity': [value: number]
}>()

const 账号状态文案 = computed(() => (props.authenticated ? '已登录' : '未登录（只读）'))

function emitWidgetShowCloseButton(value: string | number | boolean) {
  if (typeof value === 'boolean') {
    return value
  }
  return Boolean(value)
}
</script>

<template>
  <section class="widget-panel widget-no-drag">
    <div class="panel-header panel-header--static">
      <div class="panel-header__left">
        <h3 class="panel-header__title">卡片设置</h3>
      </div>
    </div>

    <div class="panel-body panel-body--settings">
      <div class="setting-section">
        <div class="setting-item setting-item--account">
          <div class="setting-item__header">
            <strong>账号</strong>
            <span>{{ 账号状态文案 }}</span>
          </div>
          <WidgetButton
            v-if="!authenticated"
            class="setting-item__account-button"
            variant="secondary"
            title="打开网页登录"
            @click="$emit('open-web-console')"
          >
            打开网页登录
          </WidgetButton>
          <p v-else-if="userName" class="setting-item__account-name">{{ userName }}</p>
        </div>
      </div>

      <div class="settings-divider" role="separator" />

      <div class="setting-section">
        <div class="setting-item setting-item--switch">
          <div class="setting-item__header">
            <strong>显示顶部关闭按钮</strong>
            <span>{{ widgetShowCloseButton ? '开启' : '关闭' }}</span>
          </div>
          <ElSwitch
            :model-value="widgetShowCloseButton"
            @update:model-value="(value) => $emit('update:widget-show-close-button', emitWidgetShowCloseButton(value))"
          />
        </div>
      </div>

      <div class="settings-divider" role="separator" />

      <div class="setting-section setting-section--plain">
        <div class="setting-item__header setting-item__header--rich">
          <div class="setting-item__title">
            <span>背景透明度</span>
            <WidgetButton
              class="setting-reset"
              size="sm"
              title="重置背景透明度"
              :class="{ 'setting-reset--hidden': widgetSurfaceOpacity === defaultWidgetSurfaceOpacity }"
              @click="$emit('reset-widget-surface-opacity')"
            >
              <template #icon>
                <RefreshLeft />
              </template>
            </WidgetButton>
          </div>
          <div class="setting-item__meta">
            <span class="setting-item__value">{{ widgetSurfaceOpacity }}%</span>
          </div>
        </div>
        <GlassRangeSlider
          class="setting-item--slider"
          :model-value="widgetSurfaceOpacity"
          :min="50"
          :max="100"
          :step="1"
          aria-label="卡片背景透明度"
          @update:model-value="(value) => $emit('update:widget-surface-opacity', value)"
        />
      </div>

      <div class="settings-divider" role="separator" />

      <div class="setting-section">
        <ThemeHuePanel
          :model-value="themeHue"
          :default-value="defaultThemeHue"
          @update:model-value="(value) => $emit('update:theme-hue', value)"
        />
      </div>
    </div>
  </section>
</template>

<style>
.setting-section {
  display: grid;
  gap: 14px;
}

.setting-section--plain {
  gap: 14px;
  padding: 2px 2px 0;
}

.setting-item {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: var(--widget-window-radius);
  background: color-mix(in srgb, var(--desktop-accent) 18%, transparent);
}

.setting-item--switch {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
}

.setting-item--account {
  gap: 10px;
  padding: 14px 16px;
}

.setting-item__account-button {
  justify-self: start;
}

.setting-item__account-name {
  margin: 0;
  color: var(--desktop-text-muted);
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.widget-shell--dark .setting-item__account-name {
  color: rgba(255, 255, 255, 0.72);
}

.setting-item__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--desktop-text);
}

.setting-item__header--rich {
  align-items: flex-start;
}

.setting-item__title {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 12px;
  font-size: 18px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.9);
}

.setting-item__title::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -12px;
  width: 4px;
  height: 16px;
  border-radius: 4px;
  background: var(--desktop-accent);
  transform: translateY(-50%);
}

.setting-reset {
  transition: opacity 0.2s;
}

.setting-reset--hidden {
  opacity: 0;
  pointer-events: none;
}

.setting-item__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.setting-item__value {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  height: 30px;
  padding: 0 10px;
  border-radius: 6px;
  color: var(--desktop-accent);
  font-size: 15px;
  font-weight: 700;
  background: color-mix(in srgb, var(--desktop-accent) 16%, white);
}

.setting-item__header strong {
  font-size: 16px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.88);
}

.setting-item__header > span {
  color: rgba(0, 0, 0, 0.7);
  font-size: 14px;
}

.widget-shell--dark .setting-item__title {
  color: rgba(255, 255, 255, 0.92);
}

.widget-shell--dark .setting-item__header strong {
  color: rgba(255, 255, 255, 0.9);
}

.widget-shell--dark .setting-item__header > span {
  color: rgba(255, 255, 255, 0.72);
}

.setting-item--slider .glass-range-slider {
  width: 100%;
}
</style>
