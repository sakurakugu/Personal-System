<script setup lang="ts">
import { ChatLineRound } from '@element-plus/icons-vue'
import { ElIcon } from 'element-plus'
import MarkdownRenderer from '@personal-system/module-articles/components/MarkdownRenderer.vue'
import TwikooPanel from './TwikooPanel.vue'
import { useSettingsStore } from '../../../shared/stores/settings'

const settings = useSettingsStore()

const guestbookContent = `
- 请保持友善和尊重，营造良好的交流氛围
- 欢迎分享你的想法，也可以提出对网站的建议
- 你的每一条留言，都会成为这个页面继续存在的理由
`
</script>

<template>
  <div class="guestbook-view">
    <section class="guestbook-card">
      <div class="guestbook-header">
        <div class="guestbook-title-row">
          <div class="guestbook-icon">
            <ElIcon><ChatLineRound /></ElIcon>
          </div>
          <div class="guestbook-heading">
            <h1 class="guestbook-title">留言</h1>
          </div>
        </div>
        <p class="guestbook-subtitle">欢迎在这里留下你的足迹，分享你的想法和建议。</p>
      </div>

      <MarkdownRenderer
        class="guestbook-markdown-preview article-markdown-preview"
        :content="guestbookContent"
      />
    </section>

    <TwikooPanel
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

.guestbook-header {
  display: grid;
  gap: 0.85rem;
  margin-bottom: 22px;
}

.guestbook-title-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.guestbook-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.85rem;
  background: var(--el-color-primary);
  color: #ffffff;
  font-size: 1.25rem;
  box-shadow: 0 12px 24px color-mix(in srgb, var(--el-color-primary) 28%, transparent);
  flex: 0 0 auto;
}

.guestbook-heading {
  min-width: 0;
}

.guestbook-title {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
}

.guestbook-subtitle {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
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

  .guestbook-header {
    gap: 0.75rem;
  }

  .guestbook-title-row {
    align-items: flex-start;
  }

  .guestbook-title {
    font-size: 1.5rem;
  }
}
</style>
