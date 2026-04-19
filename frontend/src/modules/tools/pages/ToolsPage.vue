<script setup lang="ts">
import { ElButton, ElTag } from 'element-plus'
import { Crop, Download, MagicStick } from '@element-plus/icons-vue'
import AppFooter from '../../../app/components/AppFooter.vue'
import ImageEditorWorkbench from '../components/ImageEditorWorkbench.vue'

const highlights = [
  { label: '纯前端处理', icon: MagicStick },
  { label: '支持裁剪导出', icon: Crop },
  { label: '本地下载结果', icon: Download },
]

function scrollToWorkbench() {
  document.getElementById('tool-workbench')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <div class="tools-page">
    <section class="tools-hero">
      <div class="tools-hero__copy">
        <span class="tools-hero__eyebrow">工具箱</span>
        <h1>图片编辑器</h1>
        <p>
          现在工具页直接挂到控制台式布局里。左侧是和数据中心一致的可折叠侧栏，内容区保留图片编辑器本体，
          方便后面继续往这里加别的工具。
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

      <div class="tools-hero__actions">
        <ElButton type="primary" size="large" @click="scrollToWorkbench">开始编辑</ElButton>
      </div>
    </section>

    <section id="tool-workbench" class="tools-workbench">
      <ImageEditorWorkbench />
    </section>

    <section class="tools-footer">
      <AppFooter :show-firefly="false" />
    </section>
  </div>
</template>

<style scoped>
.tools-page {
  height: 100%;
  overflow-y: auto;
  padding: 18px;
  box-sizing: border-box;
  background:
    radial-gradient(circle at top left, rgb(var(--el-color-primary-rgb) / 0.1), transparent 28%),
    linear-gradient(180deg, #f6fbf8 0%, #f3f7f5 100%);
}

.tools-hero {
  margin-bottom: 18px;
  padding: 22px 24px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.14);
  border-radius: 22px;
  background:
    linear-gradient(135deg, rgb(var(--el-color-primary-rgb) / 0.12), rgb(var(--el-color-primary-rgb) / 0.03)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.99));
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 20px;
  align-items: center;
}

.tools-hero__copy {
  min-width: 0;
}

.tools-hero__eyebrow {
  color: var(--el-color-primary-dark-2);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.tools-hero__copy h1 {
  margin: 8px 0 10px;
  font-size: clamp(28px, 3vw, 40px);
  line-height: 1.1;
  color: #102418;
}

.tools-hero__copy p {
  max-width: 760px;
  color: var(--el-text-color-secondary);
  line-height: 1.8;
}

.tools-hero__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
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

.tools-hero__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.tools-workbench {
  min-width: 0;
}

.tools-footer {
  margin-top: 8px;
}

.dark .tools-page {
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--el-color-primary-light-5) 12%, transparent), transparent 28%),
    linear-gradient(180deg, #111916 0%, #0f1513 100%);
}

.dark .tools-hero {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent);
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent), color-mix(in srgb, var(--el-color-primary-light-5) 5%, transparent)),
    rgba(18, 25, 22, 0.9);
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.24);
}

.dark .tools-hero__eyebrow {
  color: var(--el-color-primary-light-5);
}

.dark .tools-hero__copy h1 {
  color: #eef8f1;
}

@media (max-width: 960px) {
  .tools-hero {
    grid-template-columns: 1fr;
    align-items: start;
  }

  .tools-hero__actions {
    justify-content: flex-start;
  }
}

@media (max-width: 767px) {
  .tools-page {
    padding: 14px;
  }

  .tools-hero {
    padding: 18px;
  }

  .tools-hero__actions :deep(.el-button) {
    width: 100%;
  }
}
</style>
