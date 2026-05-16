<script setup lang="ts">
import { Check, Monitor, RefreshRight, SetUp } from '@element-plus/icons-vue'
import { 检查Git环境, type Git环境状态 } from '@/shared/windows-tools'
import { ElAlert, ElButton, ElCard, ElDescriptions, ElDescriptionsItem, ElEmpty, ElMessage, ElTag } from 'element-plus'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

type Windows工具值 = 'init' | 'git'

const route = useRoute()
const router = useRouter()

const 工具选项 = [
  { label: '初始化', value: 'init', icon: SetUp },
  { label: 'Git 环境', value: 'git', icon: Check },
] as const

const 当前工具 = computed<Windows工具值>(() => {
  const queryValue = Array.isArray(route.query.windowsTool)
    ? route.query.windowsTool[0]
    : route.query.windowsTool

  if (queryValue === 'git' || queryValue === 'init') {
    return queryValue
  }

  return 'init'
})

const Git检查中 = ref(false)
const Git状态 = ref<Git环境状态 | null>(null)
const Git错误信息 = ref('')

const Git状态标签 = computed(() => {
  if (!Git状态.value) {
    return { type: 'info' as const, text: '未检查' }
  }

  return Git状态.value.installed
    ? { type: 'success' as const, text: '已安装' }
    : { type: 'danger' as const, text: '未安装' }
})

function 切换工具(value: string | number) {
  if (value !== 'init' && value !== 'git') {
    return
  }

  void router.replace({
    path: route.path,
    query: {
      ...route.query,
      windowsTool: value === 'init' ? undefined : value,
    },
  })
}

async function 执行Git检查() {
  if (Git检查中.value) {
    return
  }

  Git检查中.value = true
  Git错误信息.value = ''
  try {
    Git状态.value = await 检查Git环境()
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    Git错误信息.value = message
    Git状态.value = null
    ElMessage.error(`Git 环境检查失败：${message}`)
  } finally {
    Git检查中.value = false
  }
}

watch(当前工具, (value) => {
  if (value !== 'git') {
    return
  }
  if (Git状态.value || Git错误信息.value || Git检查中.value) {
    return
  }
  void 执行Git检查()
}, { immediate: true })
</script>

<template>
  <div class="windows-tools-page">
    <section class="windows-tools-page__hero">
      <nav class="windows-tools-page__top-nav" aria-label="Windows 工具切换">
        <button
          v-for="item in 工具选项"
          :key="item.value"
          type="button"
          class="windows-tools-page__top-nav-item"
          :class="{ 'is-active': 当前工具 === item.value }"
          :aria-pressed="当前工具 === item.value"
          @click="切换工具(item.value)"
        >
          <span class="windows-tools-page__top-nav-icon">
            <component :is="item.icon" />
          </span>
          <span class="windows-tools-page__top-nav-label">{{ item.label }}</span>
        </button>
      </nav>
    </section>

    <section class="windows-tools-page__content">
      <ElCard v-if="当前工具 === 'init'" class="windows-tools-page__panel" shadow="never">
        <div class="windows-tools-page__panel-header">
          <div>
            <span class="windows-tools-page__eyebrow">预留功能</span>
            <h2>Windows 初始化</h2>
            <p>这里先预留给后续的环境初始化流程，例如依赖检查、目录准备和常用工具安装。</p>
          </div>
        </div>

        <ElEmpty description="初始化流程暂未实现，入口已预留。" />
      </ElCard>

      <ElCard v-else class="windows-tools-page__panel" shadow="never">
        <div class="windows-tools-page__panel-header windows-tools-page__panel-header--with-actions">
          <div>
            <span class="windows-tools-page__eyebrow">环境检测</span>
            <h2>Git 环境</h2>
            <p>检查当前系统是否安装 Git，并展示 `git --version` 的结果。</p>
          </div>
          <ElButton type="primary" :loading="Git检查中" @click="执行Git检查">
            <template #icon><RefreshRight /></template>
            重新检测
          </ElButton>
        </div>

        <ElAlert
          v-if="Git错误信息"
          class="windows-tools-page__alert"
          type="error"
          :title="Git错误信息"
          :closable="false"
          show-icon
        />

        <div class="windows-tools-page__status">
          <div class="windows-tools-page__status-main">
            <div class="windows-tools-page__status-icon">
              <Monitor />
            </div>
            <div class="windows-tools-page__status-text">
              <strong>Git 安装状态</strong>
              <span>{{ Git状态?.detail || '点击重新检测以获取当前系统的 Git 状态。' }}</span>
            </div>
          </div>
          <ElTag :type="Git状态标签.type" effect="dark" round>{{ Git状态标签.text }}</ElTag>
        </div>

        <ElDescriptions class="windows-tools-page__descriptions" :column="1" border>
          <ElDescriptionsItem label="是否安装">
            {{ Git状态?.installed ? '是' : '否' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="Git 版本">
            {{ Git状态?.version || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="详细信息">
            {{ Git状态?.detail || '尚未执行检测。' }}
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>
    </section>
  </div>
</template>

<style scoped>
.windows-tools-page {
  height: 100%;
  overflow-y: auto;
  padding: 18px;
  box-sizing: border-box;
  background:
    radial-gradient(circle at top left, rgb(var(--el-color-primary-rgb) / 0.1), transparent 28%),
    linear-gradient(180deg, #f7fafc 0%, #eef3f8 100%);
}

.windows-tools-page__hero {
  margin-bottom: 18px;
  padding: 12px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.14);
  border-radius: 22px;
  background:
    linear-gradient(135deg, rgb(var(--el-color-primary-rgb) / 0.12), rgb(var(--el-color-primary-rgb) / 0.03)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.99));
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.windows-tools-page__top-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.windows-tools-page__top-nav-item {
  min-width: 0;
  min-height: 48px;
  padding: 0 18px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.12);
  border-radius: 14px;
  background-color: rgba(255, 255, 255, 0.82);
  color: #475569;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  text-align: center;
  cursor: pointer;
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    background-color 0.18s ease,
    box-shadow 0.18s ease,
    color 0.18s ease;
}

.windows-tools-page__top-nav-item:hover {
  transform: translateY(-1px);
  border-color: rgb(var(--el-color-primary-rgb) / 0.24);
  background-color: rgba(var(--el-color-primary-rgb), 0.16);
  color: var(--el-color-primary);
  box-shadow: 0 10px 20px rgb(var(--el-color-primary-rgb) / 0.12);
}

.windows-tools-page__top-nav-item:focus-visible {
  outline: 2px solid rgb(var(--el-color-primary-rgb) / 0.42);
  outline-offset: 2px;
}

.windows-tools-page__top-nav-item.is-active {
  border-color: rgb(var(--el-color-primary-rgb) / 0.28);
  background-color: rgba(var(--el-color-primary-rgb), 0.22);
  color: var(--el-color-primary);
  box-shadow: 0 12px 24px rgb(var(--el-color-primary-rgb) / 0.16);
}

.windows-tools-page__top-nav-item.is-active:hover {
  background-color: rgba(var(--el-color-primary-rgb), 0.28);
}

.windows-tools-page__top-nav-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 12px;
  color: #64748b;
  flex-shrink: 0;
}

.windows-tools-page__top-nav-icon :deep(svg) {
  width: 18px;
  height: 18px;
}

.windows-tools-page__top-nav-label {
  font-size: 14px;
  font-weight: 700;
  line-height: 1;
}

.windows-tools-page__content {
  min-width: 0;
}

.windows-tools-page__panel {
  border-radius: 24px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.12);
  background:
    linear-gradient(160deg, rgba(255, 255, 255, 0.96), rgba(248, 251, 249, 0.98)),
    linear-gradient(135deg, rgb(var(--el-color-primary-rgb) / 0.06), transparent 46%);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.windows-tools-page__panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.windows-tools-page__panel-header--with-actions {
  margin-bottom: 18px;
}

.windows-tools-page__eyebrow {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(var(--el-color-primary-rgb), 0.12);
  color: var(--el-color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.windows-tools-page__panel h2 {
  margin: 16px 0 10px;
  font-size: 28px;
  line-height: 1.15;
  color: #102418;
}

.windows-tools-page__panel p {
  margin: 0;
  max-width: 720px;
  color: var(--el-text-color-secondary);
  line-height: 1.8;
}

.windows-tools-page__alert {
  margin-bottom: 16px;
}

.windows-tools-page__status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.12);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
}

.windows-tools-page__status-main {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.windows-tools-page__status-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(var(--el-color-primary-rgb), 0.18), rgba(var(--el-color-primary-rgb), 0.08));
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.windows-tools-page__status-icon :deep(svg) {
  width: 28px;
  height: 28px;
}

.windows-tools-page__status-text {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.windows-tools-page__status-text strong {
  font-size: 18px;
  color: #102418;
}

.windows-tools-page__status-text span {
  color: var(--el-text-color-secondary);
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.windows-tools-page__descriptions {
  margin-top: 18px;
}

.dark .windows-tools-page {
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--el-color-primary-light-5) 12%, transparent), transparent 28%),
    linear-gradient(180deg, #111916 0%, #0f1513 100%);
}

.dark .windows-tools-page__hero,
.dark .windows-tools-page__panel,
.dark .windows-tools-page__status {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent);
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent), color-mix(in srgb, var(--el-color-primary-light-5) 5%, transparent)),
    rgba(18, 25, 22, 0.9);
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.24);
}

.dark .windows-tools-page__top-nav-item {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 12%, transparent);
  background-color: rgba(16, 24, 22, 0.72);
  color: #d7dee7;
}

.dark .windows-tools-page__top-nav-item:hover {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 22%, transparent);
  background-color: rgba(var(--el-color-primary-rgb), 0.2);
  color: var(--el-color-primary-light-3);
  box-shadow: 0 12px 24px rgba(2, 6, 23, 0.2);
}

.dark .windows-tools-page__top-nav-item.is-active {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 28%, transparent);
  background-color: rgba(var(--el-color-primary-rgb), 0.26);
  color: var(--el-color-primary-light-3);
  box-shadow: 0 16px 30px rgba(2, 6, 23, 0.24);
}

.dark .windows-tools-page__panel h2,
.dark .windows-tools-page__status-text strong {
  color: #eef8f1;
}

.dark .windows-tools-page__status-text span {
  color: #b6c1cf;
}

@media (max-width: 1080px) {
  .windows-tools-page__panel-header,
  .windows-tools-page__status {
    flex-direction: column;
    align-items: flex-start;
  }

  .windows-tools-page__top-nav-item {
    flex: 1 1 0;
  }
}

@media (max-width: 767px) {
  .windows-tools-page {
    padding: 14px;
  }

  .windows-tools-page__hero {
    padding: 10px;
  }

  .windows-tools-page__top-nav {
    display: grid;
    grid-template-columns: 1fr;
  }

  .windows-tools-page__top-nav-item {
    min-height: 52px;
    padding: 0 16px;
    justify-content: flex-start;
  }

  .windows-tools-page__panel h2 {
    font-size: 24px;
  }

  .windows-tools-page__status-main {
    align-items: flex-start;
  }
}
</style>
