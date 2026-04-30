<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { siBilibili, siGithub } from 'simple-icons'
</script>

<template>
  <div class="widget-card profile-card">
    <div class="profile-section">
      <router-link class="profile-avatar-link" to="/about" aria-label="关于我">
        <div class="profile-avatar-overlay">
          <Icon icon="fa7-regular:address-card" class="profile-avatar-icon" />
        </div>
        <div class="avatar">
          <img src="/头像.avif" alt="头像.avif" title="头像.avif">
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
  display: block;
  position: relative;
  width: 100%;
  max-width: 192px;
  margin: 4px auto 12px;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.15s;
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
