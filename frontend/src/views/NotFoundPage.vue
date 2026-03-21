<template>
  <div class="not-found">
    <div class="content">
      <h1 class="title">404</h1>
      <p class="subtitle">页面未找到</p>
      <p class="description">您访问的页面不存在或已被移除</p>
      <el-button type="primary" @click="goHome">返回首页</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>

<style scoped>
.not-found {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  overflow: hidden;
}

.dark .not-found {
  background: var(--bg-primary);
}

.content {
  text-align: center;
  padding: 40px;
}

.title {
  font-size: 120px;
  font-weight: 700;
  color: var(--el-color-primary);
  margin: 0;
  line-height: 1;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
}

.subtitle {
  font-size: 28px;
  color: var(--el-text-color-primary);
  margin: 20px 0 10px;
  font-weight: 500;
}

.description {
  font-size: 16px;
  color: var(--el-text-color-secondary);
  margin-bottom: 30px;
}
</style>
