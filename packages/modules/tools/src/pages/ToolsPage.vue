<script setup lang="ts">
import { Connection, Crop, Grid } from '@element-plus/icons-vue'
import { ElButton, ElCard, ElTag } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()

const 工具卡片列表 = [
  {
    标题: '图片工具',
    描述: '集中放图片编辑、格式转换和后续的拼接能力，作为图像处理的统一入口。',
    路径: '/tools/image',
    图标: Crop,
    标签: ['图片编辑', '格式转换', '图片拼接'],
    按钮文案: '进入图片工具',
    启用: true,
  },
  {
    标题: 'MC 服务器查询',
    描述: '输入服务器地址后查询 Java / Bedrock 服务器是否在线、当前玩家数、延迟和版本信息。',
    路径: '/tools/minecraft-server',
    图标: Connection,
    标签: ['在线状态', '玩家数量', '版本信息'],
    按钮文案: '进入服务器查询',
    启用: true,
  },
] as const

function 进入工具(path: string) {
  if (!path) {
    return
  }
  void router.push(path)
}
</script>

<template>
  <div class="tools-page">
    <section class="tools-hero">
      <span class="tools-hero__eyebrow">工具首页</span>
      <h1>把常用能力整理成明确入口</h1>
      <p>
        这里不再直接塞具体功能页，先作为工具总览。每类工具都单独占一个子路由，后面继续扩展时结构会更清晰。
      </p>
    </section>

    <section class="tools-grid" aria-label="工具列表">
      <ElCard
        v-for="item in 工具卡片列表"
        :key="item.标题"
        class="tools-card"
        shadow="never"
      >
        <div class="tools-card__icon">
          <component :is="item.图标" />
        </div>
        <div class="tools-card__body">
          <div class="tools-card__header">
            <h2>{{ item.标题 }}</h2>
            <div class="tools-card__tags">
              <ElTag
                v-for="tag in item.标签"
                :key="tag"
                effect="plain"
                round
              >
                {{ tag }}
              </ElTag>
            </div>
          </div>

          <p>{{ item.描述 }}</p>

          <div class="tools-card__footer">
            <ElButton
              :type="item.启用 ? 'primary' : 'default'"
              :plain="!item.启用"
              :disabled="!item.启用"
              @click="进入工具(item.路径)"
            >
              {{ item.按钮文案 }}
            </ElButton>
          </div>
        </div>
      </ElCard>
    </section>

    <section class="tools-note">
      <div class="tools-note__item">
        <Grid class="tools-note__icon" />
        <div>
          <h3>子路由拆分</h3>
          <p>图片工具和 MC 服务器查询都已经拆成独立子路由，后面新增工具时继续按类别扩展。</p>
        </div>
      </div>
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
    radial-gradient(circle at top left, rgb(var(--el-color-primary-rgb) / 0.12), transparent 30%),
    linear-gradient(180deg, #f4faf6 0%, #eef5f0 100%);
}

.tools-hero {
  margin-bottom: 18px;
  padding: 24px 28px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.14);
  border-radius: 26px;
  background:
    linear-gradient(140deg, rgb(var(--el-color-primary-rgb) / 0.12), rgb(var(--el-color-primary-rgb) / 0.02)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(255, 255, 255, 0.99));
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.tools-hero__eyebrow {
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

.tools-hero h1 {
  margin: 16px 0 10px;
  font-size: 34px;
  line-height: 1.15;
  color: #102418;
}

.tools-hero p {
  margin: 0;
  max-width: 760px;
  color: var(--el-text-color-secondary);
  line-height: 1.9;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.tools-card {
  min-height: 260px;
  border-radius: 24px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.12);
  background:
    linear-gradient(160deg, rgba(255, 255, 255, 0.97), rgba(247, 251, 248, 0.98)),
    linear-gradient(135deg, rgb(var(--el-color-primary-rgb) / 0.06), transparent 50%);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.05);
}

.tools-card :deep(.el-card__body) {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  gap: 18px;
  height: 100%;
  padding: 22px;
}

.tools-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 88px;
  height: 88px;
  border-radius: 28px;
  background: linear-gradient(145deg, rgba(var(--el-color-primary-rgb), 0.18), rgba(var(--el-color-primary-rgb), 0.08));
  color: var(--el-color-primary);
}

.tools-card__icon :deep(svg) {
  width: 38px;
  height: 38px;
}

.tools-card__body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.tools-card__header {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tools-card__header h2 {
  margin: 0;
  font-size: 26px;
  line-height: 1.15;
  color: #102418;
}

.tools-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tools-card p {
  margin: 18px 0 0;
  color: var(--el-text-color-secondary);
  line-height: 1.8;
}

.tools-card__footer {
  margin-top: auto;
  padding-top: 22px;
}

.tools-note {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 18px;
}

.tools-note__item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 18px 20px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.12);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.82);
}

.tools-note__icon {
  width: 22px;
  height: 22px;
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.tools-note h3 {
  margin: 0 0 6px;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.tools-note p {
  margin: 0;
  line-height: 1.7;
  color: var(--el-text-color-secondary);
}

.dark .tools-page {
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--el-color-primary-light-5) 12%, transparent), transparent 30%),
    linear-gradient(180deg, #111916 0%, #0f1513 100%);
}

.dark .tools-hero,
.dark .tools-card,
.dark .tools-note__item {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent);
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent), color-mix(in srgb, var(--el-color-primary-light-5) 5%, transparent)),
    rgba(18, 25, 22, 0.9);
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.24);
}

.dark .tools-hero h1,
.dark .tools-card__header h2 {
  color: #eef8f1;
}

@media (max-width: 1080px) {
  .tools-grid,
  .tools-note {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .tools-page {
    padding: 14px;
  }

  .tools-hero {
    padding: 18px;
  }

  .tools-hero h1 {
    font-size: 28px;
  }

  .tools-card :deep(.el-card__body) {
    grid-template-columns: 1fr;
  }

  .tools-card__icon {
    width: 72px;
    height: 72px;
    border-radius: 22px;
  }
}
</style>
