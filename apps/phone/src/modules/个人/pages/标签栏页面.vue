<script setup lang="ts">
import ProfileSubpageHeader from '@/modules/个人/components/个人子页面标题.vue'
import AppIconButton from '@/shared/components/图标按钮.vue'
import { 使用标签栏存储 } from '@/shared/stores/tab-bar'
import type { AppTabId } from '@/shared/tab-bar'
import { ArrowDownBold, ArrowUpBold } from '@element-plus/icons-vue'
import { computed } from 'vue'

const tabBar = 使用标签栏存储()
const tabBarSettingsItems = computed(() => tabBar.settingsItems)

function handleMoveTab(id: AppTabId, direction: -1 | 1) {
  tabBar.moveTab(id, direction)
}

function canToggleTab(item: {
  visible: boolean
  canHide: boolean
  canShow: boolean
}) {
  return item.visible ? item.canHide : item.canShow
}

function handleToggleItem(item: {
  id: AppTabId
  visible: boolean
  canHide: boolean
  canShow: boolean
}) {
  if (!canToggleTab(item)) {
    return
  }
  handleToggleTab(item.id, !item.visible)
}

function handleToggleTab(id: AppTabId, visible: boolean) {
  tabBar.setTabVisible(id, visible)
}
</script>

<template>
  <section class="page">
    <ProfileSubpageHeader
      title="底部导航"
    />

    <section class="panel-card stack">
      <div>
        <span class="info-label">标签规则</span>
        <strong class="section-title">已选 {{ tabBar.visibleTabIds.length }} / {{ tabBar.maximumVisibleTabCount }} 个标签</strong>
      </div>
      <div class="tabbar-settings-list">
        <article
          v-for="item in tabBarSettingsItems"
          :key="item.id"
          class="tabbar-settings-item"
          :class="{
            'tabbar-settings-item--visible': item.visible,
            'tabbar-settings-item--hidden': !item.visible,
            'tabbar-settings-item--locked': !canToggleTab(item),
          }"
          tabindex="0"
          @click="handleToggleItem(item)"
          @keydown.enter.prevent="handleToggleItem(item)"
          @keydown.space.prevent="handleToggleItem(item)"
        >
          <div class="tabbar-settings-main">
            <span class="tabbar-settings-icon">
              <component :is="item.icon" />
            </span>
            <div class="tabbar-settings-text">
              <strong>{{ item.label }}</strong>
            </div>
          </div>
          <div class="tabbar-settings-actions" @click.stop>
            <AppIconButton
              label="上移标签"
              size="sm"
              :disabled="!item.canMoveLeft"
              @click="handleMoveTab(item.id, -1)"
            >
              <ArrowUpBold />
            </AppIconButton>
            <AppIconButton
              label="下移标签"
              size="sm"
              :disabled="!item.canMoveRight"
              @click="handleMoveTab(item.id, 1)"
            >
              <ArrowDownBold />
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
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--theme-card-border);
  border-radius: 18px;
  background: var(--theme-panel-subtle);
  cursor: pointer;
  transition: background-color 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.tabbar-settings-item:focus-visible {
  outline: none;
  border-color: color-mix(in srgb, var(--el-color-primary) 36%, transparent);
  box-shadow: 0 0 0 3px var(--theme-focus-ring);
}

.tabbar-settings-item--visible {
  background: color-mix(in srgb, var(--theme-accent-soft) 68%, var(--theme-panel-subtle));
  border-color: color-mix(in srgb, var(--el-color-primary) 28%, var(--theme-card-border));
}

.tabbar-settings-item--hidden {
  opacity: 0.88;
}

.tabbar-settings-item--locked {
  cursor: default;
}

.tabbar-settings-item:not(.tabbar-settings-item--locked):active {
  transform: scale(0.992);
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
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
}

.tabbar-settings-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}

.tabbar-settings-item--visible .tabbar-settings-icon {
  background: color-mix(in srgb, var(--theme-accent-soft) 82%, white 18%);
}

.tabbar-settings-item--visible .panel-meta {
  color: var(--text-secondary);
}
</style>
