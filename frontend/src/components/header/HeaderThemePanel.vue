<script setup lang="ts">
import { Moon, Sunny } from '@element-plus/icons-vue'
import { ElIcon, ElSwitch } from 'element-plus'
import { useThemeStore } from '../../stores/theme'

withDefaults(defineProps<{
  compact?: boolean
}>(), {
  compact: false,
})

const theme = useThemeStore()

function setLightMode() {
  theme.isDark = false
  theme.setFollowSystem(false)
}

function setDarkMode() {
  theme.isDark = true
  theme.setFollowSystem(false)
}
</script>

<template>
  <div class="theme-dropdown-content" :class="{ 'theme-dropdown-content--compact': compact }">
    <div class="theme-title">主题设置</div>
    <div class="theme-options">
      <div
        class="theme-option"
        :class="{ active: !theme.followSystem && !theme.isDark }"
        @click="setLightMode"
      >
        <ElIcon><Sunny /></ElIcon>
        <span>浅色</span>
      </div>
      <div
        class="theme-option"
        :class="{ active: !theme.followSystem && theme.isDark }"
        @click="setDarkMode"
      >
        <ElIcon><Moon /></ElIcon>
        <span>深色</span>
      </div>
    </div>
    <div class="theme-divider" />
    <div class="follow-system-row">
      <span>跟随系统</span>
      <ElSwitch
        :model-value="theme.followSystem"
        @update:model-value="theme.setFollowSystem"
      />
    </div>
  </div>
</template>

<style scoped>
.theme-dropdown-content {
  padding: 8px 12px;
  min-width: 140px;
}

.theme-dropdown-content--compact {
  padding: 0;
}

.theme-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.9);
  position: relative;
  margin-left: 12px;
  margin-bottom: 12px;
}

.theme-title::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 16px;
  border-radius: 4px;
  background: var(--header-accent-soft);
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
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid var(--el-border-color);
  transition: all 0.2s;
}

.theme-option:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

.theme-option.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.theme-option .el-icon {
  font-size: 18px;
}

.theme-option span {
  font-size: 12px;
}

.theme-divider {
  height: 1px;
  background: var(--el-border-color);
  margin: 8px 0;
}

.follow-system-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: var(--el-text-color-primary);
}

:global(.dark) .theme-dropdown-content {
  background: transparent !important;
}

:global(.dark) .theme-title {
  color: rgba(255, 255, 255, 0.9) !important;
}

:global(.dark) .theme-title::before {
  background: var(--header-accent-bright) !important;
}

:global(.dark) .theme-option {
  border-color: rgba(255, 255, 255, 0.25) !important;
  color: #e5e7eb !important;
}

:global(.dark) .theme-option:hover {
  border-color: var(--el-color-primary) !important;
  color: var(--el-color-primary) !important;
}

:global(.dark) .theme-option.active {
  background: var(--el-color-primary-dark-2) !important;
  border-color: var(--el-color-primary-dark-2) !important;
  color: var(--el-color-primary-light-9) !important;
}

:global(.dark) .theme-divider {
  background: rgba(255, 255, 255, 0.25) !important;
}

:global(.dark) .follow-system-row {
  color: #e5e7eb !important;
}
</style>
