<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'
import { useThemeStore } from '../../../stores/theme'
// import GitHubCard from './GitHubCard.vue'

const themeStore = useThemeStore()

const MdPreview = defineAsyncComponent({
  loader: async () => {
    const [editorModule] = await Promise.all([
      import('md-editor-v3'),
      import('md-editor-v3/lib/style.css'),
    ])
    return editorModule.MdPreview
  },
  delay: 0,
  suspensible: false,
})

const markdownPreviewTheme = computed(() => (themeStore.isDark ? 'dark' : 'light'))

const aboutContent = `
你好！我是 **Sakurakugu** ，这是我的个人网站。

## 🛠️ 关于本站

这个网站是我的个人空间，用来记录生活、分享技术、沉淀思考。

前端基于 **Vue 3 + TypeScript** 构建，采用了 [Element Plus](https://element-plus.org/) 作为组件库，Markdown 渲染由 [md-editor-v3](https://github.com/imzbf/md-editor-v3) 提供支持。博客主题风格参考了 [Firefly](https://github.com/CuteLeaf/Firefly) 的设计理念，追求清新、简洁与现代化的视觉体验。

---

*感谢你的来访！希望在这里能找到对你有用的内容！*
`
</script>

<template>
  <div class="about-view">
    <div class="about-card">
      <h1 class="about-title">关于我 / About Me</h1>
      <MdPreview
        class="about-markdown-preview"
        :model-value="aboutContent"
        :theme="markdownPreviewTheme"
        preview-theme="github"
        code-theme="github"
        language="zh-CN"
      />
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

.is-overlay-mode .about-card {
  background: rgba(255, 255, 255, var(--overlay-card-opacity));
}

.dark .blog-home.is-overlay-mode .about-card {
  background: rgba(15, 23, 42, var(--overlay-card-opacity));
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

.about-markdown-preview :deep(.md-editor),
.about-markdown-preview :deep(.md-editor-preview-wrapper),
.about-markdown-preview :deep(.md-editor-preview) {
  background: transparent !important;
}

.about-markdown-preview :deep(.md-editor-preview h2),
.about-markdown-preview :deep(.md-editor-preview h3) {
  scroll-margin-top: 80px;
}

@media (max-width: 576px) {
  .about-card {
    padding: 16px;
  }

  .about-title {
    font-size: 1.5rem;
  }
}
</style>
