<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { Plus, SwitchButton } from '@element-plus/icons-vue'
import { ElAvatar, ElButton, ElIcon } from 'element-plus'
import { computed, ref } from 'vue'
import { useSlots } from 'vue'
import type { Component } from 'vue'
import { 使用下拉面板 } from '@personal-system/ui'

type UserMenuItem = {
  label: string
  key: string
  type?: 'divider'
  icon?: Component | string
}

const props = withDefaults(defineProps<{
  isAuthed: boolean
  avatarUrl?: string | null
  avatarText: string
  menuItems: UserMenuItem[]
  extraMenuItems?: UserMenuItem[]
  registerEnabled?: boolean
  mobile?: boolean
}>(), {
  avatarUrl: '',
  extraMenuItems: () => [],
  registerEnabled: false,
  mobile: false,
})

const emit = defineEmits<{
  'menu-select': [key: string]
  'guest-select': [key: 'login' | 'register']
}>()

const isOpen = ref(false)
const dropdownRef = ref<globalThis.HTMLElement>()
const slots = useSlots()

const buttonAriaLabel = computed(() => (props.isAuthed ? '打开用户菜单' : '打开登录菜单'))
const hasExtraPanel = computed(() => {
  const content = slots.extraPanel?.()
  return Boolean(content && content.length > 0)
})
const hasExtraSection = computed(() => props.extraMenuItems.length > 0 || hasExtraPanel.value)
const shouldShowMainSectionDivider = computed(() => hasExtraSection.value && (props.isAuthed ? props.menuItems.length > 0 : true))

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

使用下拉面板([{ isOpen, wrapperRef: dropdownRef }])
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
      <div v-show="isOpen" class="custom-dropdown-panel" :class="{ 'custom-dropdown-panel--wide': hasExtraSection }">
        <template v-if="hasExtraSection">
          <template v-for="item in extraMenuItems" :key="item.key">
            <div v-if="item.type === 'divider'" class="custom-divider" role="separator" />
            <div v-else class="dropdown-item" @click="handleMenuSelect(item.key)">
              <Icon v-if="typeof item.icon === 'string'" :icon="item.icon" class="dropdown-item-icon" />
              <ElIcon v-else-if="item.icon" :size="16"><component :is="item.icon" /></ElIcon>
              <span>{{ item.label }}</span>
            </div>
          </template>
          <div v-if="hasExtraPanel && extraMenuItems.length" class="custom-divider" role="separator" />
          <div v-if="hasExtraPanel" class="extra-panel-wrapper">
            <slot name="extraPanel" />
          </div>
        </template>
        <div v-if="shouldShowMainSectionDivider" class="custom-divider" role="separator" />
        <template v-if="isAuthed">
          <template v-for="item in menuItems" :key="item.key">
            <div v-if="item.type === 'divider'" class="custom-divider" role="separator" />
            <div v-else class="dropdown-item" @click="handleMenuSelect(item.key)">
              <Icon v-if="typeof item.icon === 'string'" :icon="item.icon" class="dropdown-item-icon" />
              <ElIcon v-else-if="item.icon" :size="16"><component :is="item.icon" /></ElIcon>
              <span>{{ item.label }}</span>
            </div>
          </template>
        </template>
        <template v-else>
          <div class="dropdown-item" @click="handleGuestSelect('login')">
            <ElIcon :size="16"><SwitchButton /></ElIcon>
            <span>登录</span>
          </div>
          <div v-if="registerEnabled" class="dropdown-item" @click="handleGuestSelect('register')">
            <ElIcon :size="16"><Plus /></ElIcon>
            <span>注册</span>
          </div>
        </template>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
@import '@personal-system/ui/styles/dropdown.css';

.header-btn {
  --dropdown-panel-min-width: 140px;
  --dropdown-panel-motion-duration: 0.15s;
  --dropdown-panel-surface-transition-duration: 0.24s;
  --dropdown-item-transition-duration: 0.15s;
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

.custom-dropdown-panel--wide {
  width: min(140px, calc(100vw - 24px));
}

.custom-divider {
  height: 1px;
  background: var(--el-border-color-light);
  margin: 8px 0;
}

.dropdown-item-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.extra-panel-wrapper {
  overflow: hidden;
}

.dark .header-btn {
  color: rgba(255, 255, 255, 0.8);
}

.dark .avatar-btn::before,
.dark .avatar-btn:hover::before,
.dark .avatar-btn:active::before {
  opacity: 0;
  transform: scale(0.85);
  background: transparent;
}

.dark .user-avatar--fallback {
  background: var(--header-avatar-gradient-dark);
}

.dark .custom-divider {
  background: rgba(255, 255, 255, 0.08);
}
</style>
