<script setup lang="ts">
import DesktopRouteLink from '@/app/components/DesktopRouteLink.vue'
import { useApiEnvironmentStore } from '@/shared/stores/api-environment'
import { Connection, Monitor, Setting } from '@element-plus/icons-vue'
import { ElIcon, ElTag } from 'element-plus'
import { SettingsItem, SettingsPageShell, SettingsSectionCard } from '@personal-system/ui'
import { computed } from 'vue'

const apiEnvironmentStore = useApiEnvironmentStore()
const canSwitchEnvironment = computed(() => apiEnvironmentStore.canSwitchEnvironment)
const activeEnvironmentName = computed(() => apiEnvironmentStore.activeEnvironment?.name || '未选择')

const settingSections = [
  {
    title: '桌面端设置',
    tag: '壳子已就绪',
    tagType: 'success' as const,
    description: '这里先复用云端设置页的卡片结构，后续可以逐步接入主题、窗口行为、同步偏好等桌面端能力。',
  },
  {
    title: '本地能力配置',
    tag: '待接入',
    tagType: 'info' as const,
    description: '预留给窗口置顶、开机启动、系统托盘、本地缓存目录等桌面端专属设置。',
  },
]
</script>

<template>
  <SettingsPageShell title="设置" :icon="Setting">
    <SettingsSectionCard header="通用设置">
      <DesktopRouteLink
        v-if="canSwitchEnvironment"
        class="settings-entry-link"
        to="/settings/api-environment"
      >
        <SettingsItem class="settings-entry">
          <template #title>
            <span class="setting-item-title">
              <ElIcon><Connection /></ElIcon>
              <span>接口环境</span>
            </span>
          </template>
          <template #actions>
            <ElTag effect="plain">
              {{ activeEnvironmentName }}
            </ElTag>
          </template>
          <template #tip>
            管理本地开发、线上环境和自定义接口地址。
          </template>
        </SettingsItem>
      </DesktopRouteLink>
    </SettingsSectionCard>

    <SettingsSectionCard
      v-for="section in settingSections"
      :key="section.title"
      :header="section.title"
    >
      <SettingsItem>
        <template #title>
          <span class="setting-item-title">
            <ElIcon><Monitor /></ElIcon>
            <span>{{ section.title }}</span>
          </span>
        </template>
        <template #actions>
          <ElTag :type="section.tagType">
            {{ section.tag }}
          </ElTag>
        </template>
        <template #tip>
          {{ section.description }}
        </template>
      </SettingsItem>
    </SettingsSectionCard>
  </SettingsPageShell>
</template>

<style scoped>
.setting-item-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.settings-entry-link {
  display: block;
  border-radius: 16px;
  color: inherit;
  text-decoration: none;
  transition: background-color 0.2s ease;
}

.settings-entry-link:hover {
  background: color-mix(in srgb, var(--desktop-panel) 78%, var(--desktop-accent) 22%);
}

.settings-entry {
  padding: 4px 6px;
}
</style>
