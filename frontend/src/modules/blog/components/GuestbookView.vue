<script setup lang="ts">
import { ChatLineRound } from '@element-plus/icons-vue'
import { ElIcon } from 'element-plus'
import TwikooPanel from './TwikooPanel.vue'
</script>

<template>
  <div class="guestbook-view">
    <section class="guestbook-card">
      <div class="guestbook-header">
        <div class="guestbook-icon">
          <ElIcon><ChatLineRound /></ElIcon>
        </div>
        <div>
          <h1 class="guestbook-title">留言板</h1>
          <p class="guestbook-subtitle">想说点什么都可以留在这里，站点建议、打招呼、路过签到都欢迎。</p>
        </div>
      </div>

      <div class="guestbook-content">
        <p>这里不再区分站内用户和游客，评论将统一交给 Twikoo 管理。</p>
        <p>如果你是第一次来，可以随便留一句今天的心情，或者告诉我你从哪篇文章点进来的。</p>
        <p>请保持友善，广告、引战和无关内容会直接删除。</p>
      </div>
    </section>

    <TwikooPanel
      path="/guestbook"
      title="开始留言"
      empty-description="留言板尚未配置 Twikoo 服务地址"
      :hide-admin-entry="true"
    />
  </div>
</template>

<style scoped>
.guestbook-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.guestbook-card {
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
  padding: 24px 28px;
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s, border-color 0.2s;
}

.guestbook-card:hover {
  box-shadow: 0 18px 34px rgba(148, 163, 184, 0.18);
}

.dark .guestbook-card {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.dark .guestbook-card:hover {
  box-shadow: 0 18px 34px rgba(2, 6, 23, 0.35);
}

.is-overlay-mode .guestbook-card {
  background: rgba(255, 255, 255, var(--overlay-card-opacity));
}

.dark .blog-home.is-overlay-mode .guestbook-card {
  background: rgba(15, 23, 42, var(--overlay-card-opacity));
}

.guestbook-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 20px;
}

.guestbook-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  border-radius: 1rem;
  background: linear-gradient(135deg, color-mix(in srgb, var(--el-color-primary) 22%, white), color-mix(in srgb, var(--el-color-primary-light-3) 16%, white));
  color: var(--el-color-primary-dark-2);
  font-size: 1.5rem;
  flex: 0 0 auto;
}

.guestbook-title {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
}

.guestbook-subtitle {
  margin: 0.4rem 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.guestbook-content {
  display: grid;
  gap: 0.75rem;
  color: var(--text-secondary);
  line-height: 1.8;
}

.guestbook-content p {
  margin: 0;
}

@media (max-width: 576px) {
  .guestbook-card {
    padding: 18px 16px;
  }

  .guestbook-header {
    flex-direction: column;
  }

  .guestbook-title {
    font-size: 1.5rem;
  }
}
</style>
