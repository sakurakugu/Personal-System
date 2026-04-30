<script setup lang="ts">
import AppFooter from '../components/AppFooter.vue'
</script>

<template>
  <div class="not-found">
    <div class="content">
      <div class="title-wrap">
        <h1 class="title" data-aos="slide-down">404</h1>
        <p class="subtitle" data-aos="slide-down">页面未找到</p>
        <p class="description" data-aos="slide-up" data-aos-delay="100">您访问的页面不存在或已被移除</p>
        <router-link to="/" class="back-link" data-aos="slide-up" data-aos-delay="200">返回首页</router-link>
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<style scoped>
.not-found {
  --primary: var(--el-color-primary);

  position: relative;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding-top: var(--app-header-height);
}

.content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  width: 100%;
}

.title-wrap {
  font-weight: 700;
  text-align: center;
  opacity: 0;
  filter: blur(8px);
  will-change: transform, opacity, filter;
  animation: fade-in-blur 800ms ease-out 200ms forwards;
}

.title {
  margin: 0;
  font-size: 120px;
  font-weight: 700;
  color: var(--el-color-primary);
  line-height: 1;
  animation: slide-down 1s ease;
}

.subtitle {
  font-size: 28px;
  color: var(--text-primary);
  margin: 20px 0 10px;
  font-weight: 500;
  animation: slide-down 1s ease 50ms both;
}

.description {
  font-size: 16px;
  color: var(--text-secondary);
  margin-bottom: 30px;
  animation: slide-up 1s ease 100ms both;
}

.back-link {
  display: inline-block;
  padding: 10px 24px;
  border-radius: 20px;
  background: var(--el-color-primary);
  color: #fff;
  text-decoration: none;
  font-size: 14px;
  transition: transform 0.3s, opacity 0.3s;
  animation: slide-up 1s ease 200ms both;
}

.back-link:hover {
  opacity: 0.9;
  transform: translateY(-2px);
}

@media (max-width: 768px) {
  .title {
    font-size: 80px;
  }

  .subtitle {
    font-size: 22px;
  }

  .description {
    font-size: 14px;
  }
}

@keyframes fade-in-blur {
  0% {
    opacity: 0;
    filter: blur(10px);
  }
  100% {
    opacity: 1;
    filter: blur(0);
  }
}

@keyframes slide-up {
  0% {
    opacity: 0;
    transform: translateY(30px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slide-down {
  0% {
    opacity: 0;
    transform: translateY(-20px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
