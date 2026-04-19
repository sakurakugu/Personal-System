<script setup lang="ts">
import { ElCard, ElTag } from 'element-plus'
import { PictureFilled, MagicStick, Download, Crop } from '@element-plus/icons-vue'
import ImageEditorWorkbench from '../components/ImageEditorWorkbench.vue'

const toolEntries = [
  {
    key: 'image-editor',
    title: '图片编辑',
    description: '本地上传后直接在浏览器里裁剪、旋转、翻转、调色并导出。',
    icon: PictureFilled,
    active: true,
  },
  {
    key: 'more-tools',
    title: '更多工具',
    description: '后续会继续往这里加，先把图片编辑打磨到可用。',
    icon: MagicStick,
    active: false,
  },
]

const highlights = [
  { label: '纯前端处理', icon: MagicStick },
  { label: '支持裁剪导出', icon: Crop },
  { label: '本地下载结果', icon: Download },
]
</script>

<template>
  <div class="tools-page">
    <section class="tools-hero">
      <div class="tools-hero__copy">
        <span class="tools-hero__eyebrow">工具箱</span>
        <h1>先把图片编辑做好</h1>
        <p>
          这个页面先放第一个可用工具: 纯前端图片编辑。图片只在当前浏览器里处理，不上传到后端，
          适合日常裁图、调色、旋转和快速导出。
        </p>
        <div class="tools-hero__tags">
          <ElTag v-for="item in highlights" :key="item.label" effect="plain" round>
            <span class="hero-tag__inner">
              <component :is="item.icon" class="hero-tag__icon" />
              {{ item.label }}
            </span>
          </ElTag>
        </div>
      </div>
      <div class="tools-hero__panel">
        <div class="hero-panel__value">01</div>
        <div class="hero-panel__title">图片编辑器</div>
        <div class="hero-panel__desc">浏览器内完成编辑与导出</div>
      </div>
    </section>

    <section class="tools-layout">
      <aside class="tools-sidebar">
        <ElCard class="tools-nav-card" shadow="never">
          <div class="tools-nav-card__title">当前工具</div>
          <div class="tools-nav-list">
            <button
              v-for="item in toolEntries"
              :key="item.key"
              type="button"
              class="tools-nav-item"
              :class="{ 'is-active': item.active, 'is-disabled': !item.active }"
              :disabled="!item.active"
            >
              <span class="tools-nav-item__icon">
                <component :is="item.icon" />
              </span>
              <span class="tools-nav-item__copy">
                <strong>{{ item.title }}</strong>
                <small>{{ item.description }}</small>
              </span>
            </button>
          </div>
        </ElCard>
      </aside>

      <main class="tools-main">
        <ImageEditorWorkbench />
      </main>
    </section>
  </div>
</template>

<style scoped>
.tools-page {
  --tools-surface: color-mix(in srgb, var(--bg-card) 88%, white);
  --tools-surface-soft: color-mix(in srgb, var(--el-color-primary) 4%, var(--bg-card));
  --tools-surface-strong: color-mix(in srgb, var(--el-color-primary) 10%, var(--bg-card));
  --tools-border-soft: color-mix(in srgb, var(--el-color-primary) 10%, var(--border-color));
  --tools-border-strong: color-mix(in srgb, var(--el-color-primary) 20%, var(--border-color));
  --tools-title: var(--text-primary);
  --tools-text: var(--text-secondary);
  --tools-shadow: 0 22px 54px rgba(15, 23, 42, 0.08);
  min-height: calc(var(--app-viewport-height) - var(--app-header-height));
  padding: 28px 18px 32px;
  background:
    radial-gradient(circle at top left, rgb(var(--el-color-primary-rgb) / 0.16), transparent 26%),
    radial-gradient(circle at right 18%, rgba(242, 177, 84, 0.18), transparent 24%),
    linear-gradient(180deg, color-mix(in srgb, var(--el-color-primary) 4%, white) 0%, color-mix(in srgb, var(--bg-primary) 92%, var(--el-color-primary) 8%) 100%);
}

.tools-hero {
  max-width: 1500px;
  margin: 0 auto 20px;
  padding: 26px 28px;
  border: 1px solid var(--tools-border-strong);
  border-radius: 28px;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--el-color-primary) 14%, transparent), color-mix(in srgb, white 78%, transparent) 52%, color-mix(in srgb, var(--el-color-primary-light-9) 52%, white) 100%),
    var(--tools-surface);
  box-shadow: var(--tools-shadow);
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px;
  gap: 18px;
  align-items: stretch;
}

.tools-hero__copy h1 {
  margin: 8px 0 10px;
  font-size: clamp(30px, 4vw, 44px);
  line-height: 1.08;
  color: var(--tools-title);
}

.tools-hero__copy p {
  max-width: 720px;
  color: var(--tools-text);
  line-height: 1.8;
  font-size: 15px;
}

.tools-hero__eyebrow {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  background: var(--tools-surface-strong);
  color: var(--tools-title);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.tools-hero__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.hero-tag__inner {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.hero-tag__icon {
  width: 14px;
  height: 14px;
}

.tools-hero__panel {
  position: relative;
  overflow: hidden;
  padding: 20px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top right, color-mix(in srgb, white 82%, transparent), transparent 34%),
    linear-gradient(160deg, color-mix(in srgb, white 86%, var(--el-color-primary-light-9)), color-mix(in srgb, var(--el-color-primary-light-9) 72%, white));
  border: 1px solid var(--tools-border-soft);
  display: grid;
  align-content: end;
  gap: 6px;
}

.tools-hero__panel::after {
  content: '';
  position: absolute;
  inset: auto -12px -18px auto;
  width: 128px;
  height: 128px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(242, 177, 84, 0.3), transparent 72%);
}

.hero-panel__value {
  font-size: 64px;
  line-height: 1;
  font-weight: 800;
  color: var(--tools-title);
  opacity: 0.86;
}

.hero-panel__title {
  font-size: 20px;
  font-weight: 700;
  color: var(--tools-title);
}

.hero-panel__desc {
  color: var(--tools-text);
  line-height: 1.7;
}

.tools-layout {
  max-width: 1500px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.tools-sidebar {
  position: sticky;
  top: 12px;
}

.tools-nav-card {
  border-radius: 24px;
  border-color: var(--tools-border-soft);
  background: color-mix(in srgb, var(--tools-surface) 92%, transparent);
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(14px);
}

.tools-nav-card :deep(.el-card__body) {
  padding: 18px;
}

.tools-nav-card__title {
  margin-bottom: 14px;
  font-size: 16px;
  font-weight: 700;
  color: var(--tools-title);
}

.tools-nav-list {
  display: grid;
  gap: 12px;
}

.tools-nav-item {
  width: 100%;
  padding: 14px;
  border: 1px solid var(--tools-border-soft);
  border-radius: 18px;
  background: var(--tools-surface-soft);
  display: flex;
  align-items: flex-start;
  gap: 12px;
  text-align: left;
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    background-color 0.18s ease;
}

.tools-nav-item.is-active {
  transform: translateY(-1px);
  border-color: var(--tools-border-strong);
  background: linear-gradient(145deg, color-mix(in srgb, var(--el-color-primary) 14%, var(--bg-card)), color-mix(in srgb, white 95%, var(--bg-card)));
}

.tools-nav-item.is-disabled {
  opacity: 0.72;
  cursor: not-allowed;
}

.tools-nav-item__icon {
  flex: 0 0 42px;
  width: 42px;
  height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: var(--tools-surface-strong);
  color: var(--tools-title);
}

.tools-nav-item__copy {
  display: grid;
  gap: 6px;
}

.tools-nav-item__copy strong {
  color: var(--tools-title);
  font-size: 14px;
}

.tools-nav-item__copy small {
  color: var(--tools-text);
  line-height: 1.7;
}

.tools-main {
  min-width: 0;
}

.dark .tools-page {
  --tools-surface: color-mix(in srgb, var(--bg-card) 92%, transparent);
  --tools-surface-soft: color-mix(in srgb, var(--el-color-primary-light-5) 8%, var(--bg-card));
  --tools-surface-strong: color-mix(in srgb, var(--el-color-primary-light-5) 14%, var(--bg-card));
  --tools-border-soft: color-mix(in srgb, var(--el-color-primary-light-5) 10%, var(--border-color));
  --tools-border-strong: color-mix(in srgb, var(--el-color-primary-light-5) 18%, var(--border-color));
  --tools-title: var(--text-primary);
  --tools-text: var(--text-secondary);
  --tools-shadow: 0 22px 54px rgba(2, 6, 23, 0.3);
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent), transparent 24%),
    radial-gradient(circle at right 18%, rgba(242, 177, 84, 0.12), transparent 24%),
    linear-gradient(180deg, #0f1513 0%, #121917 100%);
}

.dark .tools-hero,
.dark .tools-nav-card {
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--el-color-primary-light-5) 12%, transparent), rgba(16, 24, 22, 0.92)),
    var(--tools-surface);
  border-color: var(--tools-border-strong);
  box-shadow: var(--tools-shadow);
}

.dark .tools-nav-item {
  background: var(--tools-surface-soft);
  border-color: var(--tools-border-soft);
}

.dark .tools-nav-item.is-active {
  background: color-mix(in srgb, var(--el-color-primary-light-5) 12%, var(--bg-card));
  border-color: var(--tools-border-strong);
}

.dark .tools-hero__panel {
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.08), transparent 34%),
    linear-gradient(160deg, color-mix(in srgb, var(--el-color-primary-light-5) 8%, var(--bg-card)), color-mix(in srgb, var(--bg-card) 96%, black));
  border-color: var(--tools-border-soft);
}

@media (max-width: 1180px) {
  .tools-layout {
    grid-template-columns: 1fr;
  }

  .tools-sidebar {
    position: static;
  }
}

@media (max-width: 767px) {
  .tools-page {
    padding: 18px 14px 24px;
  }

  .tools-hero {
    grid-template-columns: 1fr;
    padding: 20px;
    border-radius: 24px;
  }
}
</style>
