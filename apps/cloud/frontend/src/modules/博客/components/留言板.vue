<script setup lang="ts">
import { ChatLineRound } from '@element-plus/icons-vue'
import MarkdownRenderer from '@personal-system/module-articles/components/Markdown渲染器.vue'
import { BlogTwikooPanel } from '@personal-system/module-blog/widgets'
import { ElIcon } from 'element-plus'
import { 使用设置存储 } from '../../../shared/stores/settings'

const settings = 使用设置存储()

const guestbookContent = `
- 下面都是默认值，随便留言即可
- 请保持友善和尊重，营造良好的交流氛围
- 欢迎分享你的想法，也可以提出对网站的建议
- 你的每一条留言，都会成为这个页面继续存在的理由
`
</script>

<template>
  <div class="guestbook-view">
    <section class="guestbook-card">
      <div class="header-wrap">
        <div class="header-row">
          <div class="header-icon">
            <ElIcon><ChatLineRound /></ElIcon>
          </div>
          <h1 class="header-title">留言</h1>
        </div>
        <p class="header-desc">欢迎在这里留下你的足迹，分享你的想法和建议。</p>
      </div>

      <MarkdownRenderer
        class="guestbook-markdown-preview article-markdown-preview"
        :content="guestbookContent"
      />
    </section>

    <BlogTwikooPanel
      path="/guestbook"
      title="开始留言"
      empty-description="留言板尚未配置 Twikoo 服务地址"
      :hide-admin-entry="true"
      :visibility="settings.commentVisibility"
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
  padding: 26px 30px;
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

.header-wrap {
  margin-bottom: 1rem;
}

.header-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.header-icon {
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  background: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 1.5rem;
}

.header-title {
  margin: 0;
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--text-primary);
}

.header-desc {
  margin: 0;
  font-size: 1rem;
  color: var(--text-secondary);
  line-height: 1.625;
  margin-bottom: 1rem;
}

.guestbook-markdown-preview {
  width: 100%;
}

.guestbook-markdown-preview:deep(ul) {
  margin: 0;
  padding-left: 1.35rem;
}

.guestbook-markdown-preview:deep(li) {
  color: var(--text-secondary);
  line-height: 1.8;
}

.guestbook-markdown-preview:deep(li + li) {
  margin-top: 0.8rem;
}

.guestbook-markdown-preview:deep(ul li::marker) {
  color: var(--el-color-primary);
}

@media (max-width: 576px) {
  .guestbook-card {
    padding: 18px 16px;
  }

  .header-row {
    align-items: flex-start;
  }

  .header-title {
    font-size: 1.5rem;
  }
}
</style>
