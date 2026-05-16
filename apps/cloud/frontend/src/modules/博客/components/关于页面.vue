<script setup lang="ts">
import { ChatLineRound } from '@element-plus/icons-vue'
import { ElIcon } from 'element-plus'
import Markdown渲染器 from '@personal-system/module-articles/components/Markdown渲染器.vue'
import { 使用设置存储 } from '../../../shared/stores/settings'

const settings = 使用设置存储()

const aboutContent = `
你好！我是 **Sakurakugu** ，这是我的个人网站。

## 🛠️ 关于本站

这个网站是我的个人空间，用来记录生活、分享技术、沉淀思考。

前端基于 **Vue 3 + Ts** 构建，采用了 [Element Plus](https://element-plus.org/) 作为组件库，

主页主题风格复刻了 [Firefly](https://github.com/CuteLeaf/Firefly) （主要是太好看了）。

---

*感谢你的来访！希望在这里能找到对你有用的内容！*
`
</script>

<template>
  <div class="about-view">
    <div class="about-card">
      <h1 class="about-title">关于我 / About Me</h1>
      <Markdown渲染器
        class="about-markdown-preview article-markdown-preview"
        :content="aboutContent"
      />
      <router-link v-if="!settings.commentsHidden" to="/guestbook" class="guestbook-link-card">
        <span class="guestbook-link-icon">
          <ElIcon><ChatLineRound /></ElIcon>
        </span>
        <span class="guestbook-link-copy">
          <strong>去留言板</strong>
          <small>如果你想打个招呼、提建议或者单纯留个脚印，可以直接去留言页。</small>
        </span>
      </router-link>
      <!-- <GitHubCard repo="CuteLeaf/Firefly" /> -->
      <!-- <GitHubCard repo="saicaca/fuwari" /> -->
    </div>
  </div>
</template>

<style scoped>
.about-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.about-card {
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
  padding: 24px 28px;
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s, border-color 0.2s;
}

.about-card:hover {
  box-shadow: 0 18px 34px rgba(148, 163, 184, 0.18);
}

.dark .about-card {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.dark .about-card:hover {
  box-shadow: 0 18px 34px rgba(2, 6, 23, 0.35);
}

.about-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0 0 16px;
  color: var(--text-primary);
}

.about-markdown-preview {
  width: 100%;
}

.about-markdown-preview :deep(h2),
.about-markdown-preview :deep(h3) {
  scroll-margin-top: 80px;
}

.guestbook-link-card {
  margin-top: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 1rem 1.1rem;
  border-radius: 1rem;
  text-decoration: none;
  background: linear-gradient(135deg, color-mix(in srgb, var(--el-color-primary) 10%, white), color-mix(in srgb, var(--el-color-primary-light-3) 8%, white));
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 16%, transparent);
  color: inherit;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.guestbook-link-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(148, 163, 184, 0.16);
  border-color: color-mix(in srgb, var(--el-color-primary) 24%, transparent);
}

.guestbook-link-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 0.875rem;
  background: rgba(255, 255, 255, 0.75);
  color: var(--el-color-primary-dark-2);
  font-size: 1.25rem;
  flex: 0 0 auto;
}

.guestbook-link-copy {
  display: grid;
  gap: 0.25rem;
}

.guestbook-link-copy strong {
  color: var(--text-primary);
  font-size: 1rem;
}

.guestbook-link-copy small {
  color: var(--text-secondary);
  line-height: 1.6;
}

@media (max-width: 576px) {
  .about-card {
    padding: 16px;
  }

  .about-title {
    font-size: 1.5rem;
  }

  .guestbook-link-card {
    align-items: flex-start;
  }
}
</style>
