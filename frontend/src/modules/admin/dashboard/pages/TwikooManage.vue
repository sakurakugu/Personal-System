<script setup lang="ts">
import { ChatDotRound } from '@element-plus/icons-vue'
import { ElIcon, ElTag } from 'element-plus'
import TwikooPanel from '../../../blog/components/TwikooPanel.vue'
</script>

<template>
  <div class="page-container">
    <section class="page-header">
      <div class="page-header-main">
        <div class="page-header-icon">
          <ElIcon><ChatDotRound /></ElIcon>
        </div>
        <div class="page-header-copy">
          <h2>评论管理</h2>
          <p>这里保留评论管理入口，普通前台页面将隐藏管理小齿轮。</p>
        </div>
      </div>
      <ElTag type="warning" effect="dark">仅超级管理员可见</ElTag>
    </section>

    <TwikooPanel
      path="/dashboard/twikoo"
      title="评论面板"
      empty-description="后台评论面板尚未配置 Twikoo 服务地址"
    />
  </div>
</template>

<style scoped>
.page-container {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 20px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.12);
  background:
    linear-gradient(135deg, rgb(var(--el-color-primary-rgb) / 0.12), rgb(var(--el-color-primary-rgb) / 0.03)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.99));
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
}

.page-header-main {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  min-width: 0;
}

.page-header-icon {
  width: 52px;
  height: 52px;
  border-radius: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgb(var(--el-color-primary-rgb) / 0.18), rgb(var(--el-color-primary-rgb) / 0.08));
  color: var(--el-color-primary-dark-2);
  font-size: 24px;
  flex: 0 0 auto;
}

.page-header-copy {
  min-width: 0;
}

.page-header-copy h2 {
  margin: 0;
  font-size: 24px;
  line-height: 1.3;
}

.page-header-copy p {
  margin: 8px 0 0;
  color: var(--el-text-color-secondary);
  line-height: 1.7;
}

.dark .page-header {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent);
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent), color-mix(in srgb, var(--el-color-primary-light-5) 5%, transparent)),
    rgba(18, 25, 22, 0.9);
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.24);
}

.dark .page-header-icon {
  color: var(--el-color-primary-light-5);
}

@media (max-width: 768px) {
  .page-container {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
  }
}
</style>
