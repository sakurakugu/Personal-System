<script setup lang="ts">
import {
  执行图片分类,
  检查图片分类环境,
  type 图片分类后端,
  type 图片分类环境状态,
  type 图片分类结果,
} from '@/shared/image-classifier'
import { Cpu, FolderOpened, Histogram, MagicStick, Monitor, VideoCamera } from '@element-plus/icons-vue'
import {
  ElAlert,
  ElButton,
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElOption,
  ElSelect,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

type 分类表单 = {
  inputsText: string
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
const 错误信息 = ref('')

const 表单 = reactive<分类表单>({
  inputsText: '',
  recursive: true,
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

const 输入路径列表 = computed(() =>
  表单.inputsText
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean),
)

const 需要远程配置 = computed(() => 表单.backend !== 'mock')
const 可以启动分类 = computed(() => 输入路径列表.value.length > 0 && !分类进行中.value)
const 摘要 = computed(() => 结果.value?.summary ?? null)
const 分类结果列表 = computed(() => 结果.value?.results ?? [])
const 跳过结果列表 = computed(() => 结果.value?.skipped ?? [])

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
    <section class="image-classifier-page__hero">
      <div>
        <p class="image-classifier-page__eyebrow">桌面端专用</p>
        <h1>图片分类</h1>
        <p class="image-classifier-page__summary">
          这里直接调用本地 Python 分类核心，不走公共包页面。第一版先覆盖目录批量分类、环境检查和结果回看。
        </p>
      </div>

      <div class="image-classifier-page__actions">
        <ElButton :loading="环境检查中" @click="刷新环境状态">
          刷新环境
        </ElButton>
        <ElButton type="primary" :loading="分类进行中" :disabled="!可以启动分类" @click="开始分类">
          开始分类
        </ElButton>
      </div>
    </section>

    <ElAlert
      v-if="错误信息"
      class="image-classifier-page__alert"
      title="执行失败"
      :description="错误信息"
      type="error"
      show-icon
      :closable="false"
    />

    <div class="image-classifier-page__grid">
      <ElCard class="image-classifier-page__card" shadow="never">
        <template #header>
          <div class="image-classifier-page__card-header">
            <span class="image-classifier-page__card-title">
              <Monitor />
              <span>运行环境</span>
            </span>
            <ElTag :type="环境状态?.available ? 'success' : 'warning'" effect="plain">
              {{ 环境状态?.available ? '可用' : '待处理' }}
            </ElTag>
          </div>
        </template>

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
      </ElCard>

      <ElCard class="image-classifier-page__card" shadow="never">
        <template #header>
          <div class="image-classifier-page__card-header">
            <span class="image-classifier-page__card-title">
              <MagicStick />
              <span>分类参数</span>
            </span>
          </div>
        </template>

        <ElForm label-position="top">
          <ElFormItem label="输入路径">
            <ElInput
              v-model="表单.inputsText"
              type="textarea"
              :rows="6"
              placeholder="每行一个文件或目录路径，例如：&#10;D:\\images&#10;D:\\videos\\clip.mp4"
            />
          </ElFormItem>

          <div class="image-classifier-page__inline-grid">
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

          <template v-if="需要远程配置">
            <div class="image-classifier-page__inline-grid">
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
          </template>
        </ElForm>
      </ElCard>
    </div>

    <ElCard v-if="摘要" class="image-classifier-page__card" shadow="never">
      <template #header>
        <div class="image-classifier-page__card-header">
          <span class="image-classifier-page__card-title">
            <Histogram />
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
          <span class="image-classifier-page__card-title">
            <FolderOpened />
            <span>分类结果</span>
          </span>
          <ElTag effect="plain">
            {{ 分类结果列表.length }} 项
          </ElTag>
        </div>
      </template>

      <ElEmpty v-if="!分类结果列表.length" description="还没有分类结果，先填写路径并执行一次分类。" />
      <ElTable v-else :data="分类结果列表" stripe>
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
    </ElCard>

    <ElCard class="image-classifier-page__card" shadow="never">
      <template #header>
        <div class="image-classifier-page__card-header">
          <span class="image-classifier-page__card-title">
            <FolderOpened />
            <span>跳过文件</span>
          </span>
          <ElTag effect="plain">
            {{ 跳过结果列表.length }} 项
          </ElTag>
        </div>
      </template>

      <ElEmpty v-if="!跳过结果列表.length" description="当前没有跳过文件。" />
      <ElTable v-else :data="跳过结果列表" stripe>
        <ElTableColumn prop="path" label="路径" min-width="320" />
        <ElTableColumn prop="reason" label="原因" min-width="360" />
      </ElTable>
    </ElCard>
  </div>
</template>

<style scoped>
.image-classifier-page {
  display: grid;
  gap: 18px;
  height: 100%;
  padding: 20px;
  overflow-y: auto;
  background:
    radial-gradient(circle at top left, rgb(var(--el-color-primary-rgb) / 0.08), transparent 28%),
    linear-gradient(180deg, #f6fbf8 0%, #f3f7f5 100%);
  box-sizing: border-box;
}

.image-classifier-page__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.12);
  border-radius: 24px;
  background:
    linear-gradient(135deg, rgb(var(--el-color-primary-rgb) / 0.12), rgb(var(--el-color-primary-rgb) / 0.03)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.99));
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.image-classifier-page__eyebrow {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--el-color-primary);
  text-transform: uppercase;
}

.image-classifier-page h1 {
  margin: 0;
  font-size: 30px;
  line-height: 1.1;
  color: #102418;
}

.image-classifier-page__summary {
  max-width: 760px;
  margin: 10px 0 0;
  color: var(--el-text-color-secondary);
  line-height: 1.8;
}

.image-classifier-page__actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.image-classifier-page__alert {
  border-radius: 18px;
}

.image-classifier-page__grid {
  display: grid;
  grid-template-columns: minmax(320px, 0.95fr) minmax(420px, 1.35fr);
  gap: 18px;
}

.image-classifier-page__card {
  border-radius: 24px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.12);
  background:
    linear-gradient(160deg, rgba(255, 255, 255, 0.96), rgba(248, 251, 249, 0.98)),
    linear-gradient(135deg, rgb(var(--el-color-primary-rgb) / 0.06), transparent 46%);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.image-classifier-page__card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.image-classifier-page__card-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  color: #102418;
}

.image-classifier-page__inline-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.image-classifier-page__field-tip {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--el-text-color-secondary);
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
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.12);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.82);
}

.image-classifier-page__summary-item span {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.image-classifier-page__summary-item strong {
  font-size: 24px;
  line-height: 1;
  color: #102418;
}

.image-classifier-page__tag-icon {
  width: 14px;
  height: 14px;
  margin-right: 4px;
}

.dark .image-classifier-page {
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--el-color-primary-light-5) 12%, transparent), transparent 28%),
    linear-gradient(180deg, #111916 0%, #0f1513 100%);
}

.dark .image-classifier-page__hero,
.dark .image-classifier-page__card {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent);
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent), color-mix(in srgb, var(--el-color-primary-light-5) 5%, transparent)),
    rgba(18, 25, 22, 0.9);
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.24);
}

.dark .image-classifier-page h1,
.dark .image-classifier-page__card-title,
.dark .image-classifier-page__summary-item strong {
  color: #eef8f1;
}

.dark .image-classifier-page__summary-item {
  background: rgba(16, 24, 22, 0.72);
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 12%, transparent);
}

@media (max-width: 1180px) {
  .image-classifier-page__grid {
    grid-template-columns: 1fr;
  }

  .image-classifier-page__inline-grid,
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
  }

  .image-classifier-page__actions {
    width: 100%;
  }
}
</style>
