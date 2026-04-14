<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { siBilibili, siGithub } from 'simple-icons'
</script>

<template>
  <div class="widget-card profile-card">
    <div class="profile-section">
      <a class="profile-avatar-link" href="/about" aria-label="关于我">
        <div class="profile-avatar-overlay">
          <Icon icon="fa7-regular:address-card" class="profile-avatar-icon" />
        </div>
        <div class="avatar">
          <img src="/头像.avif" alt="头像.avif" title="头像.avif">
        </div>
      </a>
      <div class="profile-info">
        <h3 class="profile-name">Sakurakugu</h3>
        <div class="profile-divider" />
        <p class="profile-desc">个人网站</p>
      </div>
      <div class="profile-links">
        <a href="https://github.com/sakurakugu" target="_blank" class="profile-link" aria-label="GitHub">
          <svg class="profile-link-icon" viewBox="0 0 24 24" width="20" height="20" fill="currentColor" v-html="siGithub.svg" />
        </a>
        <a href="https://space.bilibili.com/22731248" target="_blank" class="profile-link" aria-label="哔哩哔哩">
          <svg class="profile-link-icon" viewBox="0 0 24 24" width="20" height="20" fill="currentColor" v-html="siBilibili.svg" />
        </a>
        <a href="mailto:sakurakugu@qq.com" class="profile-link" aria-label="邮箱">
          <svg class="profile-link-icon" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" />
          </svg>
        </a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-card .profile-section {
  text-align: center;
  padding: 20px 16px 16px;
}

.profile-avatar-link {
  display: block;
  position: relative;
  width: 96px;
  height: 96px;
  margin: 0 auto 12px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
}

.profile-avatar-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
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

.profile-avatar-icon {
  width: 2.5rem;
  height: 2.5rem;
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
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
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
  border-radius: 2px;
  margin: 0 auto 8px;
}

.profile-desc {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-bottom: 12px;
}

.profile-links {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
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
  transition: all 0.2s;
}

.profile-link:hover {
  background: var(--btn-regular-bg-hover);
}

.profile-link:active {
  transform: scale(0.9);
  background: var(--btn-regular-bg-active);
}

.profile-link-icon {
  width: 1.125rem;
  height: 1.125rem;
  fill: currentColor;
}

.profile-link-icon :deep(*) {
  fill: currentColor;
}

@media (max-width: 576px) {
  .profile-card .profile-section {
    display: flex;
    align-items: center;
    gap: 14px;
    text-align: left;
    padding: 16px;
  }

  .avatar {
    width: 68px;
    height: 68px;
    margin: 0;
    flex-shrink: 0;
  }

  .profile-info {
    flex: 1;
    min-width: 0;
  }

  .profile-desc {
    margin-bottom: 0;
  }
}
</style>
