<script setup lang="ts">
import { Monitor, Setting } from '@element-plus/icons-vue'
import { ElIcon, ElTag } from 'element-plus'
import { SettingsItem, SettingsPageShell, SettingsSectionCard } from '@personal-system/ui'

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
</style>
