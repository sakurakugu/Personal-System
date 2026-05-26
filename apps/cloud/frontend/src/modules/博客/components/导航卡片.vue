<script setup lang="ts">
import { ChatLineRound, House, Link, Picture, VideoPlay } from '@element-plus/icons-vue';
import { ElIcon } from 'element-plus';
import { 使用设置存储 } from '../../../shared/stores/settings';

const settings = 使用设置存储()
</script>

<template>
  <div class="widget-card">
    <div class="widget-header">
      <span>导航</span>
    </div>
    <div class="nav-links">
      <router-link to="/blog" class="nav-item">
        <div class="nav-item__left">
          <span class="nav-item__icon">
            <ElIcon><House /></ElIcon>
          </span>
          <span class="nav-item__label">首页</span>
        </div>
      </router-link>
      <router-link to="/friends" class="nav-item">
        <div class="nav-item__left">
          <span class="nav-item__icon">
            <ElIcon><Link /></ElIcon>
          </span>
          <span class="nav-item__label">友链</span>
        </div>
      </router-link>
      <router-link v-if="!settings.commentsHidden" to="/guestbook" class="nav-item">
        <div class="nav-item__left">
          <span class="nav-item__icon">
            <ElIcon><ChatLineRound /></ElIcon>
          </span>
          <span class="nav-item__label">留言</span>
        </div>
      </router-link>
      <router-link to="/bangumi" class="nav-item">
        <div class="nav-item__left">
          <span class="nav-item__icon">
            <ElIcon><VideoPlay /></ElIcon>
          </span>
          <span class="nav-item__label">追番</span>
        </div>
      </router-link>
      <router-link to="/gallery" class="nav-item">
        <div class="nav-item__left">
          <span class="nav-item__icon">
            <ElIcon><Picture /></ElIcon>
          </span>
          <span class="nav-item__label">相册</span>
        </div>
      </router-link>
      <!-- <router-link to="/sponsor" class="nav-item">
        <ElIcon><Coffee /></ElIcon>
        <span>赞助</span>
      </router-link> -->
    </div>
  </div>
</template>

<style scoped>
.widget-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  font-weight: 700;
  font-size: 1.125rem;
  color: var(--text-primary);
  position: relative;
  margin-left: 32px;
  margin-top: 16px;
  margin-bottom: 8px;
  border-bottom: none;
}

.widget-header::before {
  content: '';
  position: absolute;
  left: -16px;
  top: 5.5px;
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--primary);
}

.nav-links {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 6px 12px 16px;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 8px 8px 16px;
  border-radius: 8px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: background 0.2s, color 0.2s, transform 0.2s;
}

.nav-item__left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.nav-item__icon {
  font-size: 1.25rem;
  color: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-item__label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.nav-item:hover {
  background: rgba(0, 0, 0, 0.03);
}

.dark .nav-item:hover {
  background: rgba(255, 255, 255, 0.04);
}

.nav-item:hover .nav-item__label {
  color: var(--text-primary);
}

.nav-item.router-link-active .nav-item__label {
  color: var(--text-primary);
  font-weight: 700;
}

@media (max-width: 576px) {
  .nav-links {
    flex-direction: row;
    flex-wrap: nowrap;
    gap: 8px;
    overflow-x: auto;
    overflow-y: hidden;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }

  .nav-links::-webkit-scrollbar {
    display: none;
  }

  .nav-item {
    flex: 0 0 auto;
    white-space: nowrap;
    padding-right: 16px;
  }
}
</style>
