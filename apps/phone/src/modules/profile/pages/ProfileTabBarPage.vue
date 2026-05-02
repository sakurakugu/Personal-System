<script setup lang="ts">
import ProfileSubpageHeader from '@/modules/profile/components/ProfileSubpageHeader.vue'
import AppIconButton from '@/shared/components/AppIconButton.vue'
import { useTabBarStore } from '@/shared/stores/tab-bar'
import type { AppTabId } from '@/shared/tab-bar'
import { ArrowLeftBold, ArrowRightBold } from '@element-plus/icons-vue'
import { computed } from 'vue'

const tabBar = useTabBarStore()
const tabBarSettingsItems = computed(() => tabBar.settingsItems)

function getTabDescription(item: {
  visible: boolean
  required: boolean
  canHide: boolean
}) {
  if (item.required) {
    return '必选标签，不可隐藏'
  }
  if (item.visible && !item.canHide) {
    return `当前显示，至少保留 ${tabBar.minimumVisibleTabCount} 个`
  }
  return item.visible ? '当前显示，可调整顺序' : '当前隐藏，随时可恢复'
}

function handleMoveTab(id: AppTabId, direction: -1 | 1) {
  tabBar.moveTab(id, direction)
}

function handleToggleTab(id: AppTabId, visible: boolean) {
  tabBar.setTabVisible(id, visible)
}
</script>

<template>
  <section class="page">
    <ProfileSubpageHeader
      eyebrow="导航"
      title="底部导航"
      description="入口单独分层后，底部标签的显示和顺序也单独管理，不再塞在总览页里。"
    />

    <section class="panel-card stack">
      <div>
        <span class="info-label">标签规则</span>
        <strong class="section-title">至少保留 {{ tabBar.minimumVisibleTabCount }} 个，“我的”必选</strong>
      </div>
      <div class="tabbar-settings-list">
        <article v-for="item in tabBarSettingsItems" :key="item.id" class="tabbar-settings-item">
          <div class="tabbar-settings-main">
            <span class="tabbar-settings-icon">
              <component :is="item.icon" />
            </span>
            <div class="tabbar-settings-text">
              <strong>{{ item.label }}</strong>
              <span class="panel-meta">{{ getTabDescription(item) }}</span>
            </div>
          </div>
          <div class="tabbar-settings-actions">
            <button
              class="chip-button"
              :class="{ 'chip-button--active': item.visible }"
              type="button"
              :disabled="item.visible ? !item.canHide : !item.canShow"
              @click="handleToggleTab(item.id, !item.visible)"
            >
              {{ item.visible ? '显示中' : '已隐藏' }}
            </button>
            <AppIconButton
              label="左移标签"
              size="sm"
              :disabled="!item.canMoveLeft"
              @click="handleMoveTab(item.id, -1)"
            >
              <ArrowLeftBold />
            </AppIconButton>
            <AppIconButton
              label="右移标签"
              size="sm"
              :disabled="!item.canMoveRight"
              @click="handleMoveTab(item.id, 1)"
            >
              <ArrowRightBold />
            </AppIconButton>
          </div>
        </article>
      </div>
    </section>
  </section>
</template>

<style scoped>
.info-label {
  color: var(--text-tertiary);
}

.tabbar-settings-list {
  display: grid;
  gap: 12px;
}

.tabbar-settings-item {
  display: grid;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--theme-card-border);
  border-radius: 18px;
  background: var(--theme-panel-subtle);
}

.tabbar-settings-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tabbar-settings-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  color: var(--theme-accent-strong);
  background: var(--theme-panel-soft);
  border: 1px solid var(--theme-card-border);
}

.tabbar-settings-icon :deep(svg) {
  width: 20px;
  height: 20px;
  color: currentColor;
  fill: currentColor;
}

.tabbar-settings-text {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.tabbar-settings-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
