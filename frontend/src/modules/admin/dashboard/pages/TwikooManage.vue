<script setup lang="ts">
import { ChatDotRound } from '@element-plus/icons-vue'
import { ElIcon, ElSpace, ElSwitch } from 'element-plus'
import { ref, watch } from 'vue'
import TwikooPanel from '../../../blog/components/TwikooPanel.vue'

const 自动进入管理页存储键 = 'twikoo-manage-auto-open-admin'

function 读取自动进入设置() {
  if (typeof window === 'undefined') {
    return true
  }
  const 已保存值 = window.localStorage.getItem(自动进入管理页存储键)
  if (已保存值 === null) {
    return true
  }
  return 已保存值 === 'true'
}

const autoOpenAdmin = ref(读取自动进入设置())

watch(autoOpenAdmin, (value) => {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.setItem(自动进入管理页存储键, String(value))
})
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

      <ElSpace alignment="center" class="page-actions">
        <div class="auto-open-switch">
          <span class="auto-open-switch__label">自动进入管理页</span>
          <ElSwitch v-model="autoOpenAdmin" />
        </div>
      </ElSpace>
    </div>

    <TwikooPanel
      class="page-panel"
      path="/dashboard/twikoo"
      title="评论面板"
      empty-description="后台评论面板尚未配置 Twikoo 服务地址"
      :fill-height="true"
      :show-panel-header="false"
      :force-admin-entry="true"
      :auto-open-admin="autoOpenAdmin"
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
  justify-content: space-between;
  gap: 16px;
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

.page-actions {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.auto-open-switch {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.auto-open-switch__label {
  font-size: 14px;
  color: var(--text-secondary);
  white-space: nowrap;
}

@media (max-width: 768px) {
  .page-container {
    padding: 16px;
  }

  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .page-actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
