<script setup lang="ts">
import ProfileSubpageHeader from '@/modules/profile/components/ProfileSubpageHeader.vue'
import { useThemeStore } from '@/shared/stores/theme'
import { Icon } from '@iconify/vue'
import { ThemeHuePanel } from '@personal-system/ui'
import { ElSwitch } from 'element-plus'

const theme = useThemeStore()
const themeModes = [
  { value: 'light', label: '浅色', icon: 'material-symbols:wb-sunny-outline-rounded' },
  { value: 'dark', label: '深色', icon: 'material-symbols:dark-mode-outline-rounded' },
] as const

function handleThemeModeChange(mode: 'light' | 'dark') {
  theme.setMode(mode)
}

function handleFollowSystemChange(value: string | number | boolean) {
  if (value === true) {
    theme.setMode('system')
    return
  }
  theme.setMode(theme.isDark ? 'dark' : 'light')
}
</script>

<template>
  <section class="page">
    <ProfileSubpageHeader
      title="主题设置"
    />

    <section class="panel-card theme-panel">
      <div class="theme-section">
        <div class="theme-title">主题设置</div>
        <div class="theme-options">
          <button
            v-for="item in themeModes"
            :key="item.value"
            class="theme-option"
            :class="{ active: theme.mode === item.value }"
            type="button"
            @click="handleThemeModeChange(item.value)"
          >
            <Icon :icon="item.icon" class="option-icon" />
            <span class="theme-option-label">{{ item.label }}</span>
          </button>
        </div>
        <div class="follow-system-row">
          <Icon
            icon="material-symbols:brightness-auto-outline-rounded"
            class="row-icon"
          />
          <span class="follow-system-label">跟随系统</span>
          <ElSwitch
            :model-value="theme.mode === 'system'"
            @update:model-value="handleFollowSystemChange"
          />
        </div>
      </div>
    </section>

    <section class="panel-card theme-panel">
      <div class="theme-section">
        <ThemeHuePanel
          :model-value="theme.hue"
          :default-value="theme.defaultHue"
          @update:model-value="theme.setHue"
        />
      </div>
    </section>
  </section>
</template>

<style scoped>
.theme-panel {
  padding: 18px 18px 16px;
}

.theme-panel + .theme-panel {
  margin-top: 14px;
}

.theme-section {
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
  background: var(--theme-hue-title-accent, var(--header-accent-soft, var(--el-color-primary-light-3)));
}

.theme-options {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.theme-option {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px;
  border-radius: 6px;
  border: 1px solid var(--theme-card-border);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
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

.theme-option .option-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
  color: var(--el-color-primary);
}

.row-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
  color: var(--el-color-primary);
}

.theme-option span {
  font-size: 12px;
}

.theme-option-label {
  line-height: 1;
}

.follow-system-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-primary);
}

.follow-system-label {
  margin-right: auto;
}

.dark .theme-title {
  color: rgba(255, 255, 255, 0.9) !important;
}

.dark .theme-title::before {
  background: var(--theme-hue-title-accent-dark, var(--header-accent-bright, var(--el-color-primary-light-5))) !important;
}

.dark .theme-option {
  border-color: rgba(255, 255, 255, 0.25) !important;
  color: #e5e7eb !important;
}

.dark .theme-option:hover {
  border-color: var(--el-color-primary) !important;
  color: var(--el-color-primary) !important;
}

.dark .theme-option.active {
  background: var(--el-color-primary-dark-2) !important;
  border-color: var(--el-color-primary-dark-2) !important;
  color: var(--el-color-primary-light-9) !important;
}

.dark .follow-system-row {
  color: #e5e7eb !important;
}

.dark .theme-option span {
  color: inherit !important;
}
</style>
