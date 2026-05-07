<script setup lang="ts">
import { computed, onBeforeUnmount, ref, useAttrs, watch } from 'vue'
import { useLink } from 'vue-router'
import { useDesktopRouteTabs } from '../../shared/composables/useDesktopRouteTabs'

defineOptions({
  inheritAttrs: false,
})

interface Props {
  to: string
  active?: boolean
  activeClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  active: false,
  activeClass: '',
})

const attrs = useAttrs()
const link = useLink({
  to: computed(() => props.to),
})
const { openDesktopRoute } = useDesktopRouteTabs()
const menuRef = ref<globalThis.HTMLDivElement>()
const menuVisible = ref(false)
const menuX = ref(0)
const menuY = ref(0)
const instanceId = `desktop-route-link-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
const activeClassName = computed(() => props.active && props.activeClass ? props.activeClass : undefined)

function closeContextMenu() {
  menuVisible.value = false
}

function updateMenuPosition() {
  const menuElement = menuRef.value
  if (!menuElement) {
    return
  }

  const margin = 8
  menuX.value = Math.min(menuX.value, window.innerWidth - menuElement.offsetWidth - margin)
  menuY.value = Math.min(menuY.value, window.innerHeight - menuElement.offsetHeight - margin)
  menuX.value = Math.max(margin, menuX.value)
  menuY.value = Math.max(margin, menuY.value)
}

function openContextMenu(event: globalThis.MouseEvent) {
  menuX.value = event.clientX
  menuY.value = event.clientY
  menuVisible.value = true
  window.dispatchEvent(new globalThis.CustomEvent('desktop-route-context-menu-open', { detail: { id: instanceId } }))
  window.requestAnimationFrame(() => updateMenuPosition())
}

function handleClick(event: globalThis.MouseEvent) {
  event.preventDefault()
  closeContextMenu()
  void openDesktopRoute(props.to)
}

function handleMouseDown(event: globalThis.MouseEvent) {
  if (event.button !== 1) {
    return
  }

  event.preventDefault()
}

function handleAuxClick(event: globalThis.MouseEvent) {
  if (event.button !== 1) {
    return
  }

  event.preventDefault()
  closeContextMenu()
  void openDesktopRoute(props.to, { newTab: true })
}

function handleContextMenu(event: globalThis.MouseEvent) {
  event.preventDefault()
  openContextMenu(event)
}

function handleOpenInNewTab() {
  closeContextMenu()
  void openDesktopRoute(props.to, { newTab: true })
}

function handleDocumentPointerDown(event: globalThis.PointerEvent) {
  const target = event.target
  if (target instanceof globalThis.Node && menuRef.value?.contains(target)) {
    return
  }

  closeContextMenu()
}

function handleDocumentKeyDown(event: globalThis.KeyboardEvent) {
  if (event.key === 'Escape') {
    closeContextMenu()
  }
}

function handleOtherContextMenuOpen(event: globalThis.Event) {
  const detail = event instanceof globalThis.CustomEvent ? event.detail as { id?: string } | undefined : undefined
  if (detail?.id === instanceId) {
    return
  }

  closeContextMenu()
}

watch(menuVisible, (visible) => {
  if (!visible) {
    document.removeEventListener('pointerdown', handleDocumentPointerDown)
    document.removeEventListener('keydown', handleDocumentKeyDown)
    window.removeEventListener('blur', closeContextMenu)
    window.removeEventListener('resize', closeContextMenu)
    window.removeEventListener('desktop-route-context-menu-open', handleOtherContextMenuOpen)
    return
  }

  document.addEventListener('pointerdown', handleDocumentPointerDown)
  document.addEventListener('keydown', handleDocumentKeyDown)
  window.addEventListener('blur', closeContextMenu)
  window.addEventListener('resize', closeContextMenu)
  window.addEventListener('desktop-route-context-menu-open', handleOtherContextMenuOpen)
})

onBeforeUnmount(() => {
  closeContextMenu()
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
  document.removeEventListener('keydown', handleDocumentKeyDown)
  window.removeEventListener('blur', closeContextMenu)
  window.removeEventListener('resize', closeContextMenu)
  window.removeEventListener('desktop-route-context-menu-open', handleOtherContextMenuOpen)
})
</script>

<template>
  <a
    v-bind="attrs"
    :href="link.href.value"
    :class="activeClassName"
    @click="handleClick"
    @mousedown="handleMouseDown"
    @auxclick="handleAuxClick"
    @contextmenu="handleContextMenu"
  >
    <slot />

    <Teleport to="body">
      <Transition name="desktop-route-context-menu">
        <div
          v-if="menuVisible"
          ref="menuRef"
          class="desktop-route-context-menu"
          :style="{ left: `${menuX}px`, top: `${menuY}px` }"
          @contextmenu.prevent
        >
          <button type="button" class="desktop-route-context-menu__item" @click="handleOpenInNewTab">
            在新标签页打开
          </button>
        </div>
      </Transition>
    </Teleport>
  </a>
</template>

<style scoped>
.desktop-route-context-menu {
  position: fixed;
  z-index: 3000;
  min-width: 148px;
  padding: 6px;
  border: 1px solid color-mix(in srgb, var(--desktop-border) 86%, transparent);
  border-radius: 12px;
  background: color-mix(in srgb, var(--desktop-panel) 96%, #ffffff 4%);
  box-shadow:
    0 18px 40px rgba(15, 23, 42, 0.16),
    0 4px 12px rgba(15, 23, 42, 0.1);
  backdrop-filter: blur(18px) saturate(160%);
}

.desktop-route-context-menu__item {
  width: 100%;
  padding: 9px 12px;
  border: none;
  border-radius: 8px;
  color: var(--desktop-text);
  background: transparent;
  text-align: left;
  font-size: 13px;
  cursor: pointer;
  transition:
    color 0.2s ease,
    background-color 0.2s ease;
}

.desktop-route-context-menu__item:hover {
  color: var(--desktop-text);
  background: color-mix(in srgb, var(--desktop-panel) 78%, var(--desktop-accent) 22%);
}

.desktop-route-context-menu-enter-active,
.desktop-route-context-menu-leave-active {
  transition:
    opacity 0.16s ease,
    transform 0.16s ease;
}

.desktop-route-context-menu-enter-from,
.desktop-route-context-menu-leave-to {
  opacity: 0;
  transform: translateY(4px) scale(0.98);
}
</style>
