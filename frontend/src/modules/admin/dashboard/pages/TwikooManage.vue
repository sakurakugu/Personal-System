<script setup lang="ts">
import { ChatDotRound } from '@element-plus/icons-vue'
import { ElIcon } from 'element-plus'
import TwikooPanel from '../../../blog/components/TwikooPanel.vue'
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">
        <span class="page-title-main">
          <ElIcon><ChatDotRound /></ElIcon>
          <span>评论管理</span>
        </span>
      </h2>
    </div>

    <TwikooPanel
      class="page-panel"
      path="/dashboard/twikoo"
      title="评论面板"
      empty-description="后台评论面板尚未配置 Twikoo 服务地址"
      :fill-height="true"
      :show-panel-header="false"
      :auto-open-admin="true"
    />
  </div>
</template>

<style scoped>
.page-container {
  height: 100%;
  overflow: hidden;
  padding: 24px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-panel {
  flex: 1;
  min-height: 0;
}

.page-header {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
}

.page-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.3;
}

.page-title-main {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.page-title-main :deep(.el-icon) {
  color: var(--el-color-primary);
}

@media (max-width: 768px) {
  .page-container {
    padding: 16px;
  }
}
</style>
