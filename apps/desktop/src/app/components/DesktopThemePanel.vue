<script setup lang="ts">
import { Moon, Sunny } from '@element-plus/icons-vue'
import { ElSwitch } from 'element-plus'
import { useThemeStore } from '../../shared/stores/theme'

const theme = useThemeStore()

function setLightMode() {
  theme.setMode('light')
}

function setDarkMode() {
  theme.setMode('dark')
}
</script>

<template>
  <div class="theme-dropdown-content">
    <div class="theme-title">主题设置</div>
    <div class="theme-options">
      <button
        class="theme-option"
        :class="{ active: theme.mode === 'light' }"
        type="button"
        @click="setLightMode"
      >
        <Sunny class="option-icon" />
        <span>浅色</span>
      </button>
      <button
        class="theme-option"
        :class="{ active: theme.mode === 'dark' }"
        type="button"
        @click="setDarkMode"
      >
        <Moon class="option-icon" />
        <span>深色</span>
      </button>
    </div>
    <div class="theme-divider" />
    <div class="follow-system-row">
      <span class="follow-system-label">跟随系统</span>
      <ElSwitch
        :model-value="theme.mode === 'system'"
        @update:model-value="(value) => theme.setMode(value ? 'system' : (theme.isDark ? 'dark' : 'light'))"
      />
    </div>
  </div>
</template>

<style scoped>
.theme-dropdown-content {
  min-width: 140px;
  padding: 8px 12px;
}

.theme-title {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  margin-left: 12px;
  font-size: 18px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.9);
}

.theme-title::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -12px;
  width: 4px;
  height: 16px;
  border-radius: 4px;
  background: var(--header-accent-soft);
  transform: translateY(-50%);
}

.theme-options {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.theme-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.theme-option:hover {
  color: var(--el-color-primary);
  border-color: var(--el-color-primary);
}

.theme-option.active {
  color: var(--el-color-primary);
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.option-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
  color: var(--el-color-primary);
}

.theme-option span {
  font-size: 12px;
}

.theme-divider {
  height: 1px;
  margin: 8px 0;
  background: var(--el-border-color);
}

.follow-system-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--el-text-color-primary);
}

.follow-system-label {
  margin-right: auto;
}

.dark .theme-dropdown-content .theme-title {
  color: rgba(255, 255, 255, 0.9) !important;
}

.dark .theme-dropdown-content .theme-title::before {
  background: var(--header-accent-bright) !important;
}

.dark .theme-dropdown-content .theme-option {
  color: #e5e7eb !important;
  border-color: rgba(255, 255, 255, 0.25) !important;
}

.dark .theme-dropdown-content .theme-option:hover {
  color: var(--el-color-primary) !important;
  border-color: var(--el-color-primary) !important;
}

.dark .theme-dropdown-content .theme-option.active {
  color: var(--el-color-primary-light-9) !important;
  border-color: var(--el-color-primary-dark-2) !important;
  background: var(--el-color-primary-dark-2) !important;
}

.dark .theme-dropdown-content .theme-divider {
  background: rgba(255, 255, 255, 0.25) !important;
}

.dark .theme-dropdown-content .follow-system-row {
  color: #e5e7eb !important;
}

.dark .theme-dropdown-content .theme-option span {
  color: inherit !important;
}
</style>
