<script setup lang="ts">
import { HomeFilled, Link, UserFilled } from '@element-plus/icons-vue'
import { ElIcon } from 'element-plus'
</script>

<template>
  <div class="widget-card">
    <div class="widget-header">
      <span>导航</span>
    </div>
    <div class="nav-links">
      <router-link to="/blog" class="nav-item">
        <ElIcon><HomeFilled /></ElIcon>
        <span>首页</span>
      </router-link>
      <router-link to="/blog?mode=friends" class="nav-item">
        <ElIcon><Link /></ElIcon>
        <span>友链</span>
      </router-link>
      <router-link to="/blog?mode=about" class="nav-item">
        <ElIcon><UserFilled /></ElIcon>
        <span>关于我</span>
      </router-link>
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
  gap: 4px;
  padding: 10px 12px 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s;
}

.nav-item:hover {
  background: var(--btn-plain-bg-hover);
  color: var(--primary);
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
  }
}
</style>
