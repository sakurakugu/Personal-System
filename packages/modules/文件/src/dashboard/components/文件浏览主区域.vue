<script setup lang="ts">
defineProps<{
  已选中资源: boolean
}>()

const emit = defineEmits<{
  'blank-contextmenu': [mouseEvent: globalThis.MouseEvent]
}>()
</script>

<template>
  <section class="explorer-main" @contextmenu="emit('blank-contextmenu', $event)">
    <div class="explorer-toolbar">
      <div class="breadcrumb-trail">
        <slot name="breadcrumb" />
      </div>
    </div>

    <div
      class="explorer-content"
      :class="{ 'explorer-content--with-selection': 已选中资源 }"
    >
      <slot />
    </div>
  </section>
</template>

<style scoped>
.explorer-main {
  display: flex;
  flex-direction: column;
  padding-top: 12px;
  padding-left: 20px;
  overflow: hidden;
  min-width: 0;
  min-height: 0;
}

.explorer-toolbar {
  display: block;
  min-width: 0;
  line-height: 1;
}

.breadcrumb-trail {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  min-height: 28px;
}

.breadcrumb-trail :deep(.el-breadcrumb) {
  display: flex;
  align-items: center;
  min-width: 0;
  line-height: 1;
}

.breadcrumb-trail :deep(.el-breadcrumb__item) {
  display: flex;
  align-items: center;
}

.breadcrumb-trail :deep(.el-breadcrumb__inner) {
  display: inline-flex;
  align-items: center;
  line-height: 1;
}

.breadcrumb-trail :deep(.el-breadcrumb__separator) {
  display: inline-flex;
  align-items: center;
  line-height: 1;
}

.breadcrumb-trail :deep(.breadcrumb-button) {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 2px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.breadcrumb-trail :deep(.breadcrumb-button:hover) {
  color: var(--el-color-primary);
}

.explorer-content {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding-right: 4px;
}

.explorer-content--with-selection {
  padding-bottom: 108px;
}

@media (max-width: 960px) {
  .explorer-main {
    padding-left: 0;
    padding-top: 20px;
  }
}

@media (max-width: 768px) {
  .explorer-content--with-selection {
    padding-bottom: 168px;
  }
}
</style>
