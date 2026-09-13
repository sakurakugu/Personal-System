<script setup lang="ts">
import { ArrowDown, ArrowUp } from '@element-plus/icons-vue'
import { ElCard, ElIcon } from 'element-plus'
import { computed, ref, type Component } from 'vue'

const props = withDefaults(defineProps<{
  title: string
  subtitle?: string
  icon?: Component
  disabled?: boolean
  collapsible?: boolean
  defaultCollapsed?: boolean
}>(), {
  subtitle: '',
  icon: undefined,
  disabled: false,
  collapsible: true,
  defaultCollapsed: false,
})

const emit = defineEmits<{
  toggle: [expanded: boolean]
}>()

const isCollapsed = ref(props.defaultCollapsed)
const toggleLabel = computed(() => (isCollapsed.value ? '展开卡片内容' : '收起卡片内容'))

function toggleCollapse() {
  if (!props.collapsible) {
    return
  }
  isCollapsed.value = !isCollapsed.value
  emit('toggle', !isCollapsed.value)
}

function handleHeaderKeydown(event: globalThis.KeyboardEvent) {
  if (event.target !== event.currentTarget) {
    return
  }

  if (event.key !== 'Enter' && event.key !== ' ') {
    return
  }

  event.preventDefault()
  toggleCollapse()
}
</script>

<template>
  <ElCard
    class="workbench-section-card"
    :class="{ 'is-disabled-card': disabled, 'is-collapsed-card': isCollapsed }"
    :body-style="isCollapsed ? { display: 'none' } : undefined"
  >
    <template #header>
      <div
        class="workbench-section-card__header"
        :class="{ 'is-collapsible-header': collapsible }"
        :role="collapsible ? 'button' : undefined"
        :tabindex="collapsible ? 0 : undefined"
        :aria-expanded="collapsible ? !isCollapsed : undefined"
        @click="toggleCollapse"
        @keydown="handleHeaderKeydown"
      >
        <div class="workbench-section-card__heading">
          <span class="workbench-section-card__title">
            <component :is="icon" v-if="icon" class="workbench-section-card__icon" />
            {{ title }}
          </span>
          <span v-if="subtitle" class="workbench-section-card__subtitle">{{ subtitle }}</span>
        </div>

        <div class="workbench-section-card__actions" @click.stop @keydown.stop>
          <slot name="actions" />
          <button
            v-if="collapsible"
            type="button"
            class="workbench-section-card__toggle"
            :aria-label="toggleLabel"
            :aria-expanded="!isCollapsed"
            @click="toggleCollapse"
          >
            <ElIcon>
              <ArrowUp v-if="!isCollapsed" />
              <ArrowDown v-else />
            </ElIcon>
          </button>
        </div>
      </div>
    </template>

    <slot />
  </ElCard>
</template>

<style scoped>
.workbench-section-card {
  min-width: 0;
}

.is-disabled-card {
  opacity: 0.74;
}

.workbench-section-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.is-collapsible-header {
  cursor: pointer;
}

.is-collapsible-header:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--el-color-primary) 28%, transparent);
  outline-offset: 4px;
  border-radius: 12px;
}

.workbench-section-card__heading {
  min-width: 0;
  min-height: 24px;
  display: grid;
  align-content: center;
  gap: 4px;
  flex: 1;
}

.workbench-section-card__title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 700;
  line-height: 1.45;
}

.workbench-section-card__subtitle {
  min-width: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workbench-section-card__icon {
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
}

.workbench-section-card__actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex: 0 0 auto;
}

.workbench-section-card__toggle {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--el-color-primary) 8%, transparent);
  cursor: pointer;
  transition:
    background-color 0.18s ease,
    color 0.18s ease,
    transform 0.18s ease;
}

.workbench-section-card__toggle:hover {
  color: var(--text-primary);
  background: color-mix(in srgb, var(--el-color-primary) 14%, transparent);
}

.workbench-section-card__toggle:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--el-color-primary) 30%, transparent);
  outline-offset: 2px;
}

.workbench-section-card__toggle:active {
  transform: scale(0.96);
}

.workbench-section-card__toggle :deep(.el-icon) {
  font-size: 16px;
}

.is-collapsed-card :deep(.el-card__body) {
  display: none;
}

@media (max-width: 768px) {
  .workbench-section-card__header {
    align-items: flex-start;
  }

  .workbench-section-card__actions {
    max-width: 45%;
    flex-wrap: wrap;
  }
}
</style>
