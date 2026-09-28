<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { 使用认证存储 } from '@personal-system/domain/auth'
import { siBilibili, siGithub } from 'simple-icons'
import { onBeforeUnmount, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const auth = 使用认证存储()
const route = useRoute()
const router = useRouter()
const pressProgress = ref(0)
const isPressing = ref(false)
const longPressTriggered = ref(false)
const longPressDuration = 1200
let pressStartedAt = 0
let pressFrame = 0
let resetProgressTimer = 0

function clearPressFrame() {
  if (pressFrame) {
    window.cancelAnimationFrame(pressFrame)
    pressFrame = 0
  }
}

function resetPress() {
  clearPressFrame()
  isPressing.value = false
  pressProgress.value = 0
}

function finishLongPress() {
  clearPressFrame()
  isPressing.value = false
  pressProgress.value = 1
  longPressTriggered.value = true

  if (import.meta.env.DEV) {
    console.debug('[个人资料卡] 长按头像完成', { isAuthenticated: auth.isAuthenticated })
  }

  if (auth.isAuthenticated) {
    void router.push('/dashboard')
  } else {
    void router.replace({
      path: route.path,
      query: { ...route.query, login: '1' },
    })
  }

  window.clearTimeout(resetProgressTimer)
  resetProgressTimer = window.setTimeout(() => {
    pressProgress.value = 0
    longPressTriggered.value = false
  }, 260)
}

function updatePressProgress() {
  const progress = Math.min((globalThis.performance.now() - pressStartedAt) / longPressDuration, 1)
  pressProgress.value = progress
  if (progress >= 1) {
    finishLongPress()
    return
  }
  pressFrame = window.requestAnimationFrame(updatePressProgress)
}

function startLongPress(event: globalThis.PointerEvent) {
  if (event.pointerType === 'mouse' && event.button !== 0) return
  clearPressFrame()
  window.clearTimeout(resetProgressTimer)
  longPressTriggered.value = false
  isPressing.value = true
  pressProgress.value = 0
  pressStartedAt = globalThis.performance.now()
  pressFrame = window.requestAnimationFrame(updatePressProgress)
}

function cancelLongPress() {
  if (!isPressing.value) return
  resetPress()
}

function handleAvatarClick(event: globalThis.MouseEvent) {
  if (!longPressTriggered.value) return
  event.preventDefault()
  event.stopPropagation()
  longPressTriggered.value = false
}

onBeforeUnmount(() => {
  clearPressFrame()
  window.clearTimeout(resetProgressTimer)
})
</script>

<template>
  <div class="widget-card profile-card">
    <div class="profile-section">
      <router-link
        class="profile-avatar-link"
        to="/about"
        aria-label="关于我"
        @pointerdown="startLongPress"
        @pointerup="cancelLongPress"
        @pointerleave="cancelLongPress"
        @pointercancel="cancelLongPress"
        @click="handleAvatarClick"
        @contextmenu.prevent
      >
        <div
          v-if="isPressing || pressProgress > 0"
          class="profile-avatar-progress"
          :style="{ '--press-progress': `${pressProgress * 360}deg` }"
          aria-hidden="true"
        />
        <div class="profile-avatar-overlay">
          <Icon icon="fa7-regular:address-card" class="profile-avatar-icon" />
        </div>
        <div class="avatar">
          <img src="/头像.avif" alt="头像.avif" title="头像.avif" loading="lazy" decoding="async">
        </div>
      </router-link>
      <div class="profile-body">
        <div class="profile-info">
          <h3 class="profile-name">Sakurakugu</h3>
          <div class="profile-divider" />
          <p class="profile-desc">个人网站</p>
        </div>
        <div class="profile-links">
          <a href="https://github.com/sakurakugu" target="_blank" class="profile-link" aria-label="GitHub">
            <svg class="profile-link-icon" viewBox="0 0 24 24" width="24" height="24" fill="currentColor" v-html="siGithub.svg" />
          </a>
          <a href="https://space.bilibili.com/22731248" target="_blank" class="profile-link" aria-label="哔哩哔哩">
            <svg class="profile-link-icon" viewBox="0 0 24 24" width="24" height="24" fill="currentColor" v-html="siBilibili.svg" />
          </a>
          <a href="mailto:sakurakugu@qq.com" class="profile-link" aria-label="邮箱">
            <svg class="profile-link-icon" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
              <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" />
            </svg>
          </a>
          <router-link to="/rss" class="profile-link" aria-label="RSS 订阅">
            <Icon icon="material-symbols:rss-feed" class="profile-link-icon" />
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-card .profile-section {
  text-align: center;
  padding: 12px;
}

.profile-avatar-link {
  --avatar-frame-radius: 12px;
  display: block;
  position: relative;
  width: 100%;
  max-width: 192px;
  margin: 4px auto 12px;
  border-radius: var(--avatar-frame-radius);
  overflow: visible;
  cursor: pointer;
  touch-action: manipulation;
  user-select: none;
  -webkit-touch-callout: none;
  transition: transform 0.15s;
}

.profile-avatar-progress {
  position: absolute;
  inset: 0;
  z-index: 60;
  border-radius: var(--avatar-frame-radius);
  background: conic-gradient(var(--primary) var(--press-progress), transparent 0deg);
  pointer-events: none;
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  padding: 4px;
}

@media (min-width: 992px) {
  .profile-avatar-link {
    max-width: none;
    margin-top: 0;
  }
}

.profile-avatar-link:active {
  transform: scale(0.95);
}

.profile-avatar-overlay {
  position: absolute;
  inset: 0;
  z-index: 50;
  border-radius: var(--avatar-frame-radius);
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0);
  transition: background 0.2s;
  pointer-events: none;
}

.profile-avatar-link:hover .profile-avatar-overlay {
  background: rgba(0, 0, 0, 0.3);
}

.profile-avatar-link:active .profile-avatar-overlay {
  background: rgba(0, 0, 0, 0.5);
}

.profile-avatar-icon {
  width: 3rem;
  height: 3rem;
  color: white;
  opacity: 0;
  transform: scale(0.9);
  transition: all 0.2s;
}

.profile-avatar-link:hover .profile-avatar-icon {
  opacity: 1;
  transform: scale(1);
}

.avatar {
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: var(--avatar-frame-radius);
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.profile-name {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.profile-divider {
  width: 1.25rem;
  height: 4px;
  background: var(--primary);
  border-radius: 9999px;
  margin: 0 auto 8px;
}

.profile-desc {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-bottom: 10px;
}

.profile-body {
  padding: 0 8px;
}

.profile-links {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-bottom: 4px;
}

.profile-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--btn-regular-bg);
  color: var(--btn-content);
  text-decoration: none;
  transition: all 0.15s;
}

.profile-link:hover {
  background: var(--btn-regular-bg-hover);
}

.profile-link:active {
  transform: scale(0.9);
  background: var(--btn-regular-bg-active);
}

.profile-link-icon {
  width: 1.5rem;
  height: 1.5rem;
  fill: currentColor;
}

.profile-link-icon :deep(*) {
  fill: currentColor;
}
</style>
