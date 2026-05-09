<script setup lang="ts">
import {
  执行图片分类,
  检查图片分类环境,
  选择图片分类输入,
  type 图片分类后端,
  type 图片分类环境状态,
  type 图片分类结果,
} from '@/shared/image-classifier'
import {
  CloseBold,
  Cpu,
  FolderOpened,
  Histogram,
  Monitor,
  Picture,
  Plus,
  VideoCamera,
} from '@element-plus/icons-vue'
import {
  ElAlert,
  ElButton,
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInputNumber,
  ElOption,
  ElSelect,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus'
import { BaseDialog } from '@personal-system/ui'
import { computed, onMounted, reactive, ref } from 'vue'

type 分类表单 = {
  inputs: string[]
  recursive: boolean
  backend: 图片分类后端
  baseUrl: string
  model: string
  apiKey: string
  videoFrameCount: number
}

const 环境状态 = ref<图片分类环境状态 | null>(null)
const 结果 = ref<图片分类结果 | null>(null)
const 环境检查中 = ref(false)
const 分类进行中 = ref(false)
const 运行环境弹窗可见 = ref(false)
const 选择输入中 = ref(false)
const 错误信息 = ref('')

const 表单 = reactive<分类表单>({
  inputs: [],
  recursive: false,
  backend: 'mock',
  baseUrl: 'http://127.0.0.1:11434',
  model: 'qwen3.5:4b',
  apiKey: '',
  videoFrameCount: 5,
})

const 后端选项: Array<{ label: string; value: 图片分类后端; description: string }> = [
  { label: '模拟后端（测试用）', value: 'mock', description: '不依赖模型，适合先验证桌面端链路。' },
  { label: '本地 Ollama', value: 'ollama', description: '连接本机 Ollama 视觉模型。' },
  { label: 'OpenAI 兼容接口', value: 'openai_compatible', description: '连接本地或远程 OpenAI 兼容视觉服务。' },
]

const 输入路径列表 = computed(() => 表单.inputs)

const 需要远程配置 = computed(() => 表单.backend !== 'mock')
const 可以启动分类 = computed(() => 输入路径列表.value.length > 0 && !分类进行中.value)
const 摘要 = computed(() => 结果.value?.summary ?? null)
const 分类结果列表 = computed(() => 结果.value?.results ?? [])
const 跳过结果列表 = computed(() => 结果.value?.skipped ?? [])

function 添加输入路径(paths: string[]) {
  const 已有路径集合 = new Set(表单.inputs)
  for (const path of paths.map((item) => item.trim()).filter(Boolean)) {
    if (!已有路径集合.has(path)) {
      表单.inputs.push(path)
      已有路径集合.add(path)
    }
  }
}

async function 添加文件() {
  选择输入中.value = true
  错误信息.value = ''
  try {
    添加输入路径(await 选择图片分类输入('file'))
  } catch (error) {
    错误信息.value = error instanceof Error ? error.message : String(error)
  } finally {
    选择输入中.value = false
  }
}

async function 添加文件夹() {
  选择输入中.value = true
  错误信息.value = ''
  try {
    添加输入路径(await 选择图片分类输入('folder'))
  } catch (error) {
    错误信息.value = error instanceof Error ? error.message : String(error)
  } finally {
    选择输入中.value = false
  }
}

function 删除输入路径(index: number) {
  表单.inputs.splice(index, 1)
}

function 清空输入路径() {
  if (分类进行中.value) {
    return
  }
  表单.inputs.splice(0, 表单.inputs.length)
}

function 毫秒转秒文案(durationMs: number) {
  if (durationMs < 1000) {
    return `${durationMs} ms`
  }
  return `${(durationMs / 1000).toFixed(2)} s`
}

async function 刷新环境状态() {
  环境检查中.value = true
  错误信息.value = ''
  try {
    环境状态.value = await 检查图片分类环境()
  } catch (error) {
    错误信息.value = error instanceof Error ? error.message : String(error)
  } finally {
    环境检查中.value = false
  }
}

async function 开始分类() {
  if (!可以启动分类.value) {
    return
  }

  分类进行中.value = true
  错误信息.value = ''
  try {
    结果.value = await 执行图片分类({
      inputs: 输入路径列表.value,
      recursive: 表单.recursive,
      backend: 表单.backend,
      baseUrl: 需要远程配置.value ? 表单.baseUrl : null,
      model: 需要远程配置.value ? 表单.model : null,
      apiKey: 需要远程配置.value ? 表单.apiKey : null,
      videoFrameCount: 表单.videoFrameCount,
      failOnEmpty: false,
    })
  } catch (error) {
    错误信息.value = error instanceof Error ? error.message : String(error)
  } finally {
    分类进行中.value = false
  }
}

onMounted(() => {
  void 刷新环境状态()
})
</script>

<template>
  <div class="image-classifier-page">
    <ElAlert
      v-if="错误信息"
      class="image-classifier-page__alert"
      title="执行失败"
      :description="错误信息"
      type="error"
      show-icon
      :closable="false"
    />

    <ElCard class="image-classifier-page__card" shadow="never">
      <div class="image-classifier-page__hero">
        <div class="image-classifier-page__hero-main">
          <div class="image-classifier-page__title">
            <ElIcon class="image-classifier-page__title-icon"><Picture /></ElIcon>
            <span>图片分类</span>
          </div>
        </div>

        <div class="image-classifier-page__actions">
          <ElButton @click="运行环境弹窗可见 = true">
            <ElIcon><Monitor /></ElIcon>
            运行环境
          </ElButton>
          <ElButton type="primary" :loading="分类进行中" :disabled="!可以启动分类" @click="开始分类">
            开始分类
          </ElButton>
        </div>
      </div>

      <ElForm label-position="top">
        <ElFormItem label="输入项">
          <div class="image-classifier-page__input-panel">
            <div class="image-classifier-page__input-toolbar">
              <ElButton :loading="选择输入中" @click="添加文件">
                <ElIcon><Plus /></ElIcon>
                添加文件
              </ElButton>
              <ElButton :loading="选择输入中" @click="添加文件夹">
                <ElIcon><FolderOpened /></ElIcon>
                添加文件夹
              </ElButton>
              <ElButton text :disabled="!输入路径列表.length || 分类进行中" @click="清空输入路径">
                清空
              </ElButton>
            </div>

            <div class="image-classifier-page__input-list-wrap">
              <ElEmpty v-if="!输入路径列表.length" description="还没有输入项，请从左侧添加文件或文件夹。" />
              <div v-else class="image-classifier-page__input-list">
                <div
                  v-for="(path, index) in 输入路径列表"
                  :key="path"
                  class="image-classifier-page__input-item"
                >
                  <span class="image-classifier-page__input-item-text" :title="path">{{ path }}</span>
                  <ElButton
                    text
                    :disabled="分类进行中"
                    class="image-classifier-page__input-item-remove"
                    @click="删除输入路径(index)"
                  >
                    <ElIcon><CloseBold /></ElIcon>
                  </ElButton>
                </div>
              </div>
            </div>
          </div>
        </ElFormItem>

        <div class="image-classifier-page__form-grid">
          <ElFormItem label="后端类型">
            <ElSelect v-model="表单.backend">
              <ElOption
                v-for="item in 后端选项"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </ElSelect>
            <p class="image-classifier-page__field-tip">
              {{ 后端选项.find((item) => item.value === 表单.backend)?.description }}
            </p>
          </ElFormItem>

          <ElFormItem label="递归子目录">
            <ElSwitch v-model="表单.recursive" />
          </ElFormItem>

          <ElFormItem label="视频抽帧数">
            <ElInputNumber v-model="表单.videoFrameCount" :min="1" :max="20" />
          </ElFormItem>
        </div>

        <div v-if="需要远程配置" class="image-classifier-page__form-grid">
          <ElFormItem label="服务地址">
            <ElInput v-model="表单.baseUrl" placeholder="http://127.0.0.1:11434" />
          </ElFormItem>

          <ElFormItem label="模型名">
            <ElInput v-model="表单.model" placeholder="qwen3.5:4b" />
          </ElFormItem>

          <ElFormItem label="API Key">
            <ElInput v-model="表单.apiKey" type="password" show-password placeholder="可为空" />
          </ElFormItem>
        </div>
      </ElForm>
    </ElCard>

    <BaseDialog
      v-model="运行环境弹窗可见"
      title="运行环境"
      width="720px"
      max-width="calc(100vw - 32px)"
    >
      <div class="image-classifier-page__dialog-toolbar">
        <ElTag :type="环境状态?.available ? 'success' : 'warning'" effect="plain">
          {{ 环境状态?.available ? '可用' : '待处理' }}
        </ElTag>
        <ElButton :loading="环境检查中" @click="刷新环境状态">
          刷新环境
        </ElButton>
      </div>

      <ElDescriptions v-if="环境状态" :column="1" border>
        <ElDescriptionsItem label="环境说明">
          {{ 环境状态.detail }}
        </ElDescriptionsItem>
        <ElDescriptionsItem label="仓库根目录">
          {{ 环境状态.workspaceRoot || '未定位' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem label="分类脚本目录">
          {{ 环境状态.classifierDir || '未定位' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem label="Python 命令">
          {{ 环境状态.pythonCommand || '未找到' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem label="ffmpeg">
          {{ 环境状态.ffmpegAvailable ? '已找到' : '未找到' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem label="ffprobe">
          {{ 环境状态.ffprobeAvailable ? '已找到' : '未找到' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem label="缺失项">
          {{ 环境状态.missingDependencies.length ? 环境状态.missingDependencies.join('；') : '无' }}
        </ElDescriptionsItem>
      </ElDescriptions>
    </BaseDialog>

    <ElCard v-if="摘要" class="image-classifier-page__card" shadow="never">
      <template #header>
        <div class="image-classifier-page__card-header">
          <span class="image-classifier-page__section-title">
            <ElIcon><Histogram /></ElIcon>
            <span>执行摘要</span>
          </span>
        </div>
      </template>

      <div class="image-classifier-page__summary-grid">
        <div class="image-classifier-page__summary-item">
          <span>总数</span>
          <strong>{{ 摘要.total }}</strong>
        </div>
        <div class="image-classifier-page__summary-item">
          <span>已分类</span>
          <strong>{{ 摘要.classified }}</strong>
        </div>
        <div class="image-classifier-page__summary-item">
          <span>跳过</span>
          <strong>{{ 摘要.skipped }}</strong>
        </div>
        <div class="image-classifier-page__summary-item">
          <span>耗时</span>
          <strong>{{ 毫秒转秒文案(摘要.durationMs) }}</strong>
        </div>
      </div>
    </ElCard>

    <ElCard class="image-classifier-page__card" shadow="never">
      <template #header>
        <div class="image-classifier-page__card-header">
          <span class="image-classifier-page__section-title">
            <ElIcon><FolderOpened /></ElIcon>
            <span>分类结果</span>
          </span>
          <ElTag effect="plain">
            {{ 分类结果列表.length }} 项
          </ElTag>
        </div>
      </template>

      <ElEmpty v-if="!分类结果列表.length" description="还没有分类结果，先填写路径并执行一次分类。" />
      <div v-else class="image-classifier-page__table-wrap">
        <ElTable :data="分类结果列表" stripe>
          <ElTableColumn prop="path" label="路径" min-width="320" />
          <ElTableColumn prop="labelZh" label="中文标签" min-width="120" />
          <ElTableColumn prop="label" label="英文标签" min-width="140" />
          <ElTableColumn prop="confidence" label="置信度" min-width="100" />
          <ElTableColumn prop="sourceKind" label="来源类型" min-width="100">
            <template #default="{ row }">
              <ElTag :type="row.sourceKind === 'video' ? 'warning' : 'success'" effect="plain">
                <VideoCamera v-if="row.sourceKind === 'video'" class="image-classifier-page__tag-icon" />
                <Cpu v-else class="image-classifier-page__tag-icon" />
                {{ row.sourceKind }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn prop="reason" label="原因" min-width="360" show-overflow-tooltip />
        </ElTable>
      </div>
    </ElCard>

    <ElCard class="image-classifier-page__card" shadow="never">
      <template #header>
        <div class="image-classifier-page__card-header">
          <span class="image-classifier-page__section-title">
            <ElIcon><FolderOpened /></ElIcon>
            <span>跳过文件</span>
          </span>
          <ElTag effect="plain">
            {{ 跳过结果列表.length }} 项
          </ElTag>
        </div>
      </template>

      <ElEmpty v-if="!跳过结果列表.length" description="当前没有跳过文件。" />
      <div v-else class="image-classifier-page__table-wrap">
        <ElTable :data="跳过结果列表" stripe>
          <ElTableColumn prop="path" label="路径" min-width="320" />
          <ElTableColumn prop="reason" label="原因" min-width="360" />
        </ElTable>
      </div>
    </ElCard>
  </div>
</template>

<style scoped>
.image-classifier-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  min-height: 0;
  padding: 16px;
  overflow: auto;
  box-sizing: border-box;
}

.image-classifier-page__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.image-classifier-page__hero-main {
  min-width: 0;
}

.image-classifier-page__alert {
  flex-shrink: 0;
}

.image-classifier-page__card {
  flex-shrink: 0;
}

.image-classifier-page__title,
.image-classifier-page__section-title {
  display: inline-flex;
  align-items: center;
  flex-direction: row;
  gap: 8px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  writing-mode: horizontal-tb;
  text-orientation: mixed;
  white-space: nowrap;
}

.image-classifier-page__title {
  font-size: 20px;
}

.image-classifier-page__section-title {
  font-size: 16px;
}

.image-classifier-page__title-icon {
  font-size: 20px;
}

.image-classifier-page__actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  flex-shrink: 0;
}

.image-classifier-page__card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.image-classifier-page__form-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.image-classifier-page__field-tip {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--el-text-color-regular);
}

.image-classifier-page__input-panel {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 16px;
}

.image-classifier-page__input-toolbar {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 12px;
}

.image-classifier-page__input-list-wrap {
  min-height: 220px;
  padding: 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  background: var(--el-fill-color-blank);
}

.image-classifier-page__input-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.image-classifier-page__input-item {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  background: var(--el-fill-color-light);
}

.image-classifier-page__input-item-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-primary);
}

.image-classifier-page__input-item-remove {
  flex-shrink: 0;
}

.image-classifier-page__dialog-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.image-classifier-page__summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.image-classifier-page__summary-item {
  display: grid;
  gap: 8px;
  padding: 16px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  background: var(--el-fill-color-blank);
}

.image-classifier-page__summary-item span {
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.image-classifier-page__summary-item strong {
  font-size: 24px;
  line-height: 1;
  color: var(--el-text-color-primary);
}

.image-classifier-page__tag-icon {
  width: 14px;
  height: 14px;
  margin-right: 4px;
}

.image-classifier-page__table-wrap {
  overflow-x: auto;
}

@media (max-width: 1180px) {
  .image-classifier-page__input-panel,
  .image-classifier-page__form-grid,
  .image-classifier-page__summary-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 860px) {
  .image-classifier-page {
    padding: 14px;
  }

  .image-classifier-page__hero {
    flex-direction: column;
    margin-bottom: 16px;
  }

  .image-classifier-page__actions {
    width: 100%;
  }
}
</style>
