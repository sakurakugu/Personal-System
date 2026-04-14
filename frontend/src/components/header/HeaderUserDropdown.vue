<script setup lang="ts">
/* global HTMLElement, MouseEvent */
import { ElAvatar, ElButton, ElIcon } from 'element-plus'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { Component } from 'vue'

type UserMenuItem = {
  label: string
  key: string
  type?: 'divider'
  icon?: Component
}

const props = withDefaults(defineProps<{
  isAuthed: boolean
  avatarUrl?: string | null
  avatarText: string
  menuItems: UserMenuItem[]
  registerEnabled?: boolean
  mobile?: boolean
}>(), {
  avatarUrl: '',
  registerEnabled: false,
  mobile: false,
})

const emit = defineEmits<{
  'menu-select': [key: string]
  'guest-select': [key: 'login' | 'register']
}>()

const isOpen = ref(false)
const dropdownRef = ref<HTMLElement>()

const buttonAriaLabel = computed(() => (props.isAuthed ? '打开用户菜单' : '打开登录菜单'))

function adjustPanelPosition(wrapperEl?: HTMLElement) {
  if (!wrapperEl) return
  const panel = wrapperEl.querySelector('.custom-dropdown-panel') as HTMLElement | null
  if (!panel) return
  const wrapperRect = wrapperEl.getBoundingClientRect()
  const panelRect = panel.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  const gap = 8
  const panelOffset = 20

  let desiredLeft = wrapperRect.left + wrapperRect.width / 2 - panelRect.width / 2
  if (desiredLeft < gap) {
    desiredLeft = gap
  }
  if (desiredLeft + panelRect.width > viewportWidth - gap) {
    desiredLeft = viewportWidth - gap - panelRect.width
  }

  const relativeLeft = desiredLeft - wrapperRect.left
  const availableHeight = Math.max(0, viewportHeight - wrapperRect.bottom - panelOffset - gap)
  wrapperEl.style.setProperty('--panel-left', `${relativeLeft}px`)
  wrapperEl.style.setProperty('--panel-transform', 'none')
  wrapperEl.style.setProperty('--panel-max-height', `${availableHeight}px`)
}

function openMenu() {
  isOpen.value = true
}

function closeMenu() {
  isOpen.value = false
}

function toggleMenu() {
  if (!props.mobile) return
  isOpen.value = !isOpen.value
}

function handleMenuSelect(key: string) {
  emit('menu-select', key)
  closeMenu()
}

function handleGuestSelect(key: 'login' | 'register') {
  emit('guest-select', key)
  closeMenu()
}

function closeMenuIfOutside(event?: MouseEvent) {
  if (!event) {
    closeMenu()
    return
  }
  const path = event.composedPath ? event.composedPath() : []
  const insideDropdown = dropdownRef.value && path.includes(dropdownRef.value)
  if (!insideDropdown) {
    closeMenu()
  }
}

watch(isOpen, async (value) => {
  if (!value) return
  await nextTick()
  adjustPanelPosition(dropdownRef.value)
})

onMounted(() => {
  document.addEventListener('click', closeMenuIfOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeMenuIfOutside)
})
</script>

<template>
  <div
    ref="dropdownRef"
    class="dropdown-wrapper user-dropdown"
    @mouseenter="openMenu"
    @mouseleave="closeMenu"
  >
    <ElButton
      class="header-btn avatar-btn"
      :aria-label="buttonAriaLabel"
      @click.stop="toggleMenu"
    >
      <ElAvatar
        v-if="isAuthed && avatarUrl"
        :src="avatarUrl"
        size="default"
        class="user-avatar"
      />
      <ElAvatar
        v-else-if="isAuthed"
        size="default"
        class="user-avatar user-avatar--fallback"
      >
        {{ avatarText }}
      </ElAvatar>
      <ElAvatar
        v-else
        size="default"
        class="guest-avatar"
        :style="{ backgroundColor: 'var(--header-accent-surface)', color: 'var(--header-accent)' }"
      >
        登录
      </ElAvatar>
    </ElButton>
    <Transition name="dropdown">
      <div v-show="isOpen" class="custom-dropdown-panel">
        <template v-if="isAuthed">
          <template v-for="item in menuItems" :key="item.key">
            <div v-if="item.type === 'divider'" class="custom-divider" role="separator" />
            <div v-else class="dropdown-item" @click="handleMenuSelect(item.key)">
              <ElIcon v-if="item.icon" :size="16"><component :is="item.icon" /></ElIcon>
              <span>{{ item.label }}</span>
            </div>
          </template>
        </template>
        <template v-else>
          <div class="dropdown-item" @click="handleGuestSelect('login')">登录</div>
          <div v-if="registerEnabled" class="dropdown-item" @click="handleGuestSelect('register')">注册</div>
        </template>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.dropdown-wrapper {
  position: relative;
}

.dropdown-wrapper:hover::after,
.dropdown-wrapper:focus-within::after {
  content: '';
  position: absolute;
  top: 100%;
  left: var(--panel-left, 50%);
  width: 260px;
  height: 20px;
  transform: var(--panel-transform, translateX(-50%));
}

.header-btn {
  position: relative;
  z-index: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: rgba(0, 0, 0, 0.7);
  cursor: pointer;
  transition: color 0.15s ease-out;
  overflow: hidden;
  outline: none;
}

.header-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: rgba(0, 0, 0, 0.06);
  transform: scale(0.85);
  opacity: 0;
  z-index: -1;
  transition: all 0.15s ease-out;
}

.header-btn:hover::before {
  transform: scale(1);
  opacity: 1;
}

.header-btn:active::before {
  background: rgba(0, 0, 0, 0.1);
}

.avatar-btn,
.avatar-btn:hover,
.avatar-btn:focus {
  background: transparent !important;
}

.avatar-btn::before,
.avatar-btn:hover::before,
.avatar-btn:active::before {
  opacity: 0;
  transform: scale(0.85);
  background: transparent;
}

.user-avatar,
.guest-avatar {
  flex-shrink: 0;
}

.user-avatar--fallback {
  background: var(--header-avatar-gradient);
  color: #fff;
  font-weight: 700;
}

.custom-dropdown-panel {
  position: absolute;
  top: calc(100% + 20px);
  left: var(--panel-left, 50%);
  transform: var(--panel-transform, translateX(-50%));
  min-width: 160px;
  max-width: calc(100vw - 24px);
  max-height: var(--panel-max-height, calc(100dvh - 92px));
  padding: 8px;
  box-sizing: border-box;
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background-color: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
  z-index: 200;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  transition: background-color 0.24s ease, border-color 0.24s ease, box-shadow 0.24s ease;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.5) rgba(255, 255, 255, 0.18);
}

.custom-dropdown-panel::-webkit-scrollbar {
  width: 10px;
}

.custom-dropdown-panel::-webkit-scrollbar-track {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
}

.custom-dropdown-panel::-webkit-scrollbar-thumb {
  border: 2px solid transparent;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.5);
  background-clip: padding-box;
}

.custom-dropdown-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.62);
  background-clip: padding-box;
}

.custom-dropdown-panel::-webkit-scrollbar-corner {
  background: transparent;
}

.custom-divider {
  height: 1px;
  background: var(--el-border-color-light);
  margin: 8px 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 10px;
  margin: 2px 0;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.5;
  color: rgba(0, 0, 0, 0.8);
  cursor: pointer;
  transition: all 0.15s ease-out;
}

.dropdown-item:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--header-accent);
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

:global(.dark) .header-btn {
  color: rgba(255, 255, 255, 0.8);
}

:global(.dark) .avatar-btn::before,
:global(.dark) .avatar-btn:hover::before,
:global(.dark) .avatar-btn:active::before {
  opacity: 0;
  transform: scale(0.85);
  background: transparent;
}

:global(.dark) .user-avatar--fallback {
  background: var(--header-avatar-gradient-dark);
}

:global(.dark) .custom-dropdown-panel {
  background-color: rgba(30, 41, 59, 0.55);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
  scrollbar-color: rgba(255, 255, 255, 0.32) rgba(255, 255, 255, 0.1);
}

:global(.dark) .custom-dropdown-panel::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

:global(.dark) .custom-dropdown-panel::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.32);
  background-clip: padding-box;
}

:global(.dark) .custom-dropdown-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.42);
  background-clip: padding-box;
}

:global(.dark) .custom-divider {
  background: rgba(255, 255, 255, 0.08);
}

:global(.dark) .dropdown-item {
  color: rgba(255, 255, 255, 0.85);
}

:global(.dark) .dropdown-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--header-accent-bright);
}
</style>
