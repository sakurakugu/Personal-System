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
      <AppIconButton
        v-if="showBack"
        class="page-section-shell__back"
        label="返回上一层"
        @click="handleBack"
      >
        <ArrowLeftBold />
      </AppIconButton>

      <div
        class="page-section-shell__content"
        :class="{ 'page-section-shell__content--with-back': showBack }"
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

      <slot name="header-extra" />
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
  gap: 0px;
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
}

.page-section-shell__title-icon {
  width: 1em;
  height: 1em;
  flex: 0 0 auto;
  position: relative;
  top: 1px;
}

.page-section-shell__back {
  border: 0;
  background: transparent;
}

.page-section-shell__back:hover {
  background: transparent;
}
</style>
