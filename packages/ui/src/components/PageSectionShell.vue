<script setup lang="ts">
import { ArrowLeftBold } from '@element-plus/icons-vue'
import type { Component } from 'vue'
import { useRouter } from 'vue-router'
import AppIconButton from './AppIconButton.vue'

interface Props {
  title: string
  to?: string
  showBack?: boolean
  icon?: Component
  titleTag?: 'h1' | 'h2' | 'h3' | 'div'
  fillBody?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  to: '/',
  showBack: false,
  icon: undefined,
  titleTag: 'h1',
  fillBody: false,
})

const router = useRouter()

function handleBack() {
  if (!props.showBack) {
    return
  }
  void router.push(props.to)
}
</script>

<template>
  <section
    class="page-section-shell"
    :class="{ 'page-section-shell--fill-body': fillBody }"
  >
    <header class="page-section-shell__header">
      <div v-if="showBack || $slots.prefix" class="page-section-shell__prefix">
        <AppIconButton
          v-if="showBack"
          class="page-section-shell__back"
          label="返回上一层"
          @click="handleBack"
        >
          <ArrowLeftBold />
        </AppIconButton>
        <slot name="prefix" />
      </div>

      <div
        class="page-section-shell__content"
        :class="{ 'page-section-shell__content--with-back': showBack || $slots.prefix }"
      >
        <component
          :is="titleTag"
          class="page-title page-section-shell__title"
        >
          <component :is="icon" v-if="icon" class="page-section-shell__title-icon" />
          <span>{{ title }}</span>
          <slot name="title-extra" />
        </component>
      </div>

      <div v-if="$slots.actions || $slots['header-extra']" class="page-section-shell__actions">
        <slot name="actions" />
        <slot name="header-extra" />
      </div>
    </header>

    <div class="page-section-shell__body">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.page-section-shell {
  display: grid;
  gap: 18px;
}

.page-section-shell--fill-body {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.page-section-shell__header {
  display: flex;
  align-items: flex-start;
  gap: 0;
}

.page-section-shell__prefix {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
}

.page-section-shell__content {
  min-width: 0;
  flex: 1;
}

.page-section-shell__content--with-back {
  padding-top: 6px;
}

.page-section-shell__body {
  min-width: 0;
}

.page-section-shell--fill-body .page-section-shell__body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.page-section-shell :deep(.page-title) {
  margin: 0;
  font-size: 24px;
  line-height: 1.2;
}

.page-section-shell__title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: 100%;
  min-width: 0;
  white-space: nowrap;
}

.page-section-shell__title-icon {
  width: 1em;
  height: 1em;
  flex: 0 0 auto;
  position: relative;
  top: 1px;
}

.page-section-shell__title span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.page-section-shell__back {
  border: 0;
  background: transparent;
}

.page-section-shell__back:hover {
  background: transparent;
}

.page-section-shell__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
  flex: 0 0 auto;
}

@media (max-width: 640px) {
  .page-section-shell__header {
    flex-wrap: wrap;
    row-gap: 10px;
  }

  .page-section-shell__content {
    flex-basis: 0;
  }

  .page-section-shell__actions {
    width: auto;
    margin-left: auto;
    justify-content: flex-end;
  }
}
</style>
