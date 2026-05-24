<script setup lang="ts">
import { 获取桌面运行时 } from '@/shared/desktop-runtime'
import {
  停止图片分类,
  切换图片分类Ollama模型,
  发现图片分类输入,
  启动图片分类Ollama,
  执行图片分类结果处理,
  检查图片分类环境,
  流式执行图片分类,
  测试图片分类连接,
  获取图片分类Ollama模型状态,
  选择图片分类输入,
  选择图片分类输出路径,
  type 图片分类后端,
  type 图片分类环境状态,
  type 图片分类结果,
  type 图片分类结果摘要,
  type 图片分类结果项,
  type 图片分类跳过项,
  type 图片分类进度事件,
} from '@/shared/image-classifier'
import { 使用桌面图片分类器存储 } from '@/shared/stores/image-classifier'
import { CaretBottom, CaretTop, Cpu, FolderOpened, Histogram, Monitor, Picture, Plus, VideoCamera } from '@element-plus/icons-vue'
import { BaseDialog } from '@personal-system/ui'
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
  ElInput,
  ElInputNumber,
  ElOption,
  ElSelect,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus'
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'

type 鼠标事件 = globalThis.MouseEvent

type 分类表单 = {
  inputs: string[]
  recursive: boolean
  backend: 图片分类后端
  baseUrl: string
  model: string
  apiKey: string
  videoFrameCount: number
}

const 图片扩展名集合 = new Set(['png', 'jpg', 'jpeg', 'webp', 'bmp', 'gif', 'heic', 'heif', 'avif'])

const 环境状态 = ref<图片分类环境状态 | null>(null)
const 结果 = ref<图片分类结果 | null>(null)
const 环境检查中 = ref(false)
const 分类进行中 = ref(false)
const 运行环境弹窗可见 = ref(false)
const 后端配置已折叠 = ref(true)
const 分类结果已折叠 = ref(false)
const 预览详情已折叠 = ref(false)
const 跳过文件已折叠 = ref(true)
const 选择输入中 = ref(false)
const 停止进行中 = ref(false)
const 测试连接中 = ref(false)
const 启动Ollama中 = ref(false)
const 切换Ollama模型中 = ref(false)
const 刷新Ollama模型状态中 = ref(false)
const 导出Csv中 = ref(false)
const 导出Json中 = ref(false)
const 移动分类图片中 = ref(false)
const 当前状态文案 = ref('就绪')
const 错误信息 = ref('')
const 已选输入路径 = ref<string[]>([])
const 当前预览路径 = ref<string | null>(null)
const 当前结果路径 = ref<string | null>(null)
const 已完成数量 = ref(0)
const Ollama模型已加载 = ref(false)
const 左侧面板实例 = ref<{ $el?: globalThis.HTMLElement } | null>(null)
const 右侧面板元素 = ref<globalThis.HTMLElement | null>(null)
const 左侧面板高度 = ref('')
const 图片分类状态 = 使用桌面图片分类器存储()

let 右侧面板高度观察器: globalThis.ResizeObserver | null = null

const 表单 = reactive<分类表单>({
  inputs: [],
  recursive: true,
  backend: 'ollama',
  baseUrl: 'http://127.0.0.1:11434',
  model: 'qwen3.5:4b',
  apiKey: '',
  videoFrameCount: 5,
})

const 后端选项: Array<{ label: string; value: 图片分类后端; description: string }> = [
  { label: '模拟后端（测试用）', value: 'mock', description: '不依赖模型，适合先验证桌面端链路。' },
  { label: '本地 Ollama', value: 'ollama', description: '连接本机 Ollama 视觉模型。' },
  { label: 'OpenAI 兼容接口', value: 'openai_compatible', description: '连接本地或远程 OpenAI 兼容视觉服务，可按服务要求填写 API Key。' },
]

const 输入路径列表 = computed(() => 表单.inputs)
const 需要服务地址 = computed(() => 表单.backend !== 'mock')
const 需要模型名 = computed(() => 表单.backend !== 'mock')
const 需要ApiKey = computed(() => 表单.backend === 'openai_compatible')
const 使用Ollama后端 = computed(() => 表单.backend === 'ollama')
const Ollama模型按钮文案 = computed(() => Ollama模型已加载.value ? '关闭模型' : '开启模型')
const 可操作Ollama按钮 = computed(() => !分类进行中.value)
const 摘要 = computed(() => 结果.value?.summary ?? null)
const 分类结果列表 = computed(() => 结果.value?.results ?? [])
const 跳过结果列表 = computed(() => 结果.value?.skipped ?? [])
const 已选输入数量 = computed(() => 已选输入路径.value.length)
const 可分类全部 = computed(() => 输入路径列表.value.length > 0 && !分类进行中.value)
const 可分类选中项 = computed(() => 已选输入数量.value > 0 && !分类进行中.value)
const 可移除选中项 = computed(() => 已选输入数量.value > 0 && !分类进行中.value)
const 有可处理分类结果 = computed(() => 分类结果列表.value.length > 0)
const 可测试连接 = computed(() => !测试连接中.value)
const 工具栏操作已禁用 = computed(() => 分类进行中.value)
const 当前结果项 = computed<图片分类结果项 | null>(() => (
  分类结果列表.value.find((item) => item.path === 当前结果路径.value) ?? null
))

const 预览图片地址 = ref('')

const 预览说明 = computed(() => {
  const path = 当前预览路径.value
  if (!path) {
    return '未选择图片'
  }
  if (!是图片路径(path)) {
    return '当前选中项不是图片，暂不支持预览'
  }
  return ''
})

const 左侧面板样式 = computed(() => (
  左侧面板高度.value
    ? { height: 左侧面板高度.value }
    : undefined
))

function 获取左侧面板元素() {
  const element = 左侧面板实例.value?.$el
  return element instanceof globalThis.HTMLElement ? element : null
}

function 同步左侧面板高度() {
  const 左侧面板元素 = 获取左侧面板元素()
  const 右侧面板 = 右侧面板元素.value
  if (!左侧面板元素 || !右侧面板) {
    return
  }
  左侧面板高度.value = `${Math.ceil(右侧面板.getBoundingClientRect().height)}px`
}

async function 初始化左侧面板高度同步() {
  await nextTick()
  同步左侧面板高度()
  if (!右侧面板元素.value) {
    return
  }

  右侧面板高度观察器?.disconnect()
  右侧面板高度观察器 = new globalThis.ResizeObserver(() => {
    同步左侧面板高度()
  })
  右侧面板高度观察器.observe(右侧面板元素.value)
}

function 构建空结果(): 图片分类结果 {
  return {
    summary: {
      total: 0,
      classified: 0,
      skipped: 0,
      durationMs: 0,
    },
    results: [],
    skipped: [],
  }
}

function 取路径扩展名(path: string) {
  const normalizedPath = path.replace(/\\/g, '/')
  const filename = normalizedPath.split('/').pop() ?? ''
  const lastDotIndex = filename.lastIndexOf('.')
  if (lastDotIndex < 0) {
    return ''
  }
  return filename.slice(lastDotIndex + 1).toLowerCase()
}

function 取路径文件名(path: string) {
  return path.split(/[/\\]/).pop() ?? path
}

function 是图片路径(path: string) {
  return 图片扩展名集合.has(取路径扩展名(path))
}

async function 同步预览图片地址() {
  const targetPath = 当前预览路径.value
  if (!targetPath || !是图片路径(targetPath)) {
    预览图片地址.value = ''
    return
  }

  const runtime = 获取桌面运行时()
  if (!runtime) {
    预览图片地址.value = ''
    return
  }
  预览图片地址.value = await runtime.convertFileSrc(targetPath)
}

function 添加输入路径(paths: string[]) {
  const 已有路径集合 = new Set(表单.inputs)
  for (const path of paths.map((item) => item.trim()).filter(Boolean)) {
    if (!已有路径集合.has(path)) {
      表单.inputs.push(path)
      已有路径集合.add(path)
      if (!当前预览路径.value) {
        当前预览路径.value = path
      }
    }
  }
  当前状态文案.value = 表单.inputs.length ? `已加载 ${表单.inputs.length} 个媒体文件。` : '就绪'
}

function 重置分类结果状态(total = 0) {
  结果.value = {
    summary: {
      total,
      classified: 0,
      skipped: 0,
      durationMs: 0,
    },
    results: [],
    skipped: [],
  }
  当前结果路径.value = null
  已完成数量.value = 0
}

function 更新摘要(summary: 图片分类结果摘要) {
  if (!结果.value) {
    结果.value = 构建空结果()
  }
  结果.value.summary = summary
}

function 写入分类结果项(item: 图片分类结果项) {
  if (!结果.value) {
    结果.value = 构建空结果()
  }
  const index = 结果.value.results.findIndex((current) => current.path === item.path)
  if (index >= 0) {
    结果.value.results.splice(index, 1, item)
  } else {
    结果.value.results.push(item)
  }
  if (!当前结果路径.value) {
    当前结果路径.value = item.path
  }
}

function 写入跳过结果项(item: 图片分类跳过项) {
  if (!结果.value) {
    结果.value = 构建空结果()
  }
  const index = 结果.value.skipped.findIndex((current) => current.path === item.path)
  if (index >= 0) {
    结果.value.skipped.splice(index, 1, item)
  } else {
    结果.value.skipped.push(item)
  }
}

function 是停止分类消息(message: string) {
  return message.includes('图片分类已停止。') || message.includes('分类已停止，')
}

function 提取错误消息(error: unknown) {
  const rawMessage = error instanceof Error ? error.message : String(error)
  const invokeErrorMarker = ': Error: '
  const markerIndex = rawMessage.lastIndexOf(invokeErrorMarker)
  if (markerIndex >= 0) {
    return rawMessage.slice(markerIndex + invokeErrorMarker.length).trim()
  }
  return rawMessage
}

function 处理分类进度事件(event: 图片分类进度事件) {
  if (event.type === 'started') {
    重置分类结果状态(event.total)
    当前状态文案.value = `正在分类，共 ${event.total} 个输入项...`
    return
  }

  if (event.type === 'result') {
    写入分类结果项(event.result)
    已完成数量.value = event.completed
    更新摘要({
      total: event.total,
      classified: 结果.value?.results.length ?? 0,
      skipped: 结果.value?.skipped.length ?? 0,
      durationMs: 结果.value?.summary.durationMs ?? 0,
    })
    当前状态文案.value = 停止进行中.value
      ? `正在停止，当前已完成 ${event.completed}/${event.total}：${取路径文件名(event.result.path)}`
      : `正在分类，已完成 ${event.completed}/${event.total}：${取路径文件名(event.result.path)}`
    return
  }

  if (event.type === 'skipped') {
    写入跳过结果项(event.item)
    已完成数量.value = event.completed
    更新摘要({
      total: event.total,
      classified: 结果.value?.results.length ?? 0,
      skipped: 结果.value?.skipped.length ?? 0,
      durationMs: 结果.value?.summary.durationMs ?? 0,
    })
    当前状态文案.value = `已跳过 ${event.completed}/${event.total}：${取路径文件名(event.item.path)}`
    return
  }

  更新摘要(event.summary)
  已完成数量.value = event.summary.total
  当前状态文案.value = `分类完成：${event.summary.classified} 个已分类，${event.summary.skipped} 个跳过`
}

async function 添加文件() {
  选择输入中.value = true
  错误信息.value = ''
  try {
    const 选中文件 = await 选择图片分类输入('file')
    添加输入路径(await 发现图片分类输入(选中文件, false))
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
    const 选中文件夹 = await 选择图片分类输入('folder')
    添加输入路径(await 发现图片分类输入(选中文件夹, 表单.recursive))
  } catch (error) {
    错误信息.value = error instanceof Error ? error.message : String(error)
  } finally {
    选择输入中.value = false
  }
}

function 清空全部() {
  if (分类进行中.value) {
    return
  }
  表单.inputs.splice(0, 表单.inputs.length)
  已选输入路径.value = []
  当前预览路径.value = null
  当前结果路径.value = null
  结果.value = null
  已完成数量.value = 0
  错误信息.value = ''
  当前状态文案.value = '已清空'
}

function 移除选中输入项() {
  if (分类进行中.value || !已选输入路径.value.length) {
    return
  }
  const 选中集合 = new Set(已选输入路径.value)
  表单.inputs = 表单.inputs.filter((path) => !选中集合.has(path))
  if (结果.value) {
    结果.value.results = 结果.value.results.filter((item) => !选中集合.has(item.path))
    结果.value.skipped = 结果.value.skipped.filter((item) => !选中集合.has(item.path))
    结果.value.summary = {
      ...结果.value.summary,
      total: 表单.inputs.length,
      classified: 结果.value.results.length,
      skipped: 结果.value.skipped.length,
    }
  }
  if (当前结果路径.value && 选中集合.has(当前结果路径.value)) {
    当前结果路径.value = 结果.value?.results[0]?.path ?? null
  }
  if (当前预览路径.value && 选中集合.has(当前预览路径.value)) {
    当前预览路径.value = 表单.inputs[0] ?? null
  }
  已选输入路径.value = []
  当前状态文案.value = `已移除 ${选中集合.size} 个文件。`
}

function 切换输入项选中(path: string, event: 鼠标事件) {
  const 当前集合 = new Set(已选输入路径.value)
  if (event.ctrlKey || event.metaKey) {
    if (当前集合.has(path)) {
      当前集合.delete(path)
    } else {
      当前集合.add(path)
    }
    已选输入路径.value = 输入路径列表.value.filter((item) => 当前集合.has(item))
    当前预览路径.value = path
    return
  }
  已选输入路径.value = [path]
  当前预览路径.value = path
}

function 输入项是否选中(path: string) {
  return 已选输入路径.value.includes(path)
}

function 选择结果项(row: 图片分类结果项) {
  当前结果路径.value = row.path
  当前预览路径.value = row.path
}

function 毫秒转秒文案(durationMs: number) {
  if (durationMs < 1000) {
    return `${durationMs} ms`
  }
  return `${(durationMs / 1000).toFixed(2)} s`
}

function 重置为本地Ollama默认配置() {
  表单.backend = 'ollama'
  表单.baseUrl = 'http://127.0.0.1:11434'
  表单.model = 'qwen3.5:4b'
  表单.apiKey = ''
  Ollama模型已加载.value = false
  错误信息.value = ''
  当前状态文案.value = '已重置为本地 Ollama 默认配置。'
  void 刷新Ollama模型状态()
}

async function 刷新Ollama模型状态() {
  if (!使用Ollama后端.value || 切换Ollama模型中.value || 刷新Ollama模型状态中.value) {
    return
  }
  const model = 表单.model.trim()
  const baseUrl = 表单.baseUrl.trim() || 'http://127.0.0.1:11434'
  if (!model) {
    Ollama模型已加载.value = false
    return
  }

  刷新Ollama模型状态中.value = true
  try {
    const result = await 获取图片分类Ollama模型状态({
      baseUrl,
      model,
    })
    Ollama模型已加载.value = result.loaded
  } catch {
    Ollama模型已加载.value = false
  } finally {
    刷新Ollama模型状态中.value = false
  }
}

async function 启动本地Ollama() {
  if (!使用Ollama后端.value || 启动Ollama中.value) {
    return
  }
  启动Ollama中.value = true
  错误信息.value = ''
  当前状态文案.value = '正在检查 Ollama 服务...'
  try {
    const result = await 启动图片分类Ollama(表单.baseUrl.trim() || 'http://127.0.0.1:11434')
    当前状态文案.value = result.message
    await 刷新Ollama模型状态()
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    错误信息.value = message
    当前状态文案.value = `Ollama 启动失败：${message}`
  } finally {
    启动Ollama中.value = false
  }
}

async function 切换Ollama模型加载状态() {
  if (!使用Ollama后端.value || 切换Ollama模型中.value) {
    return
  }
  const model = 表单.model.trim()
  if (!model) {
    错误信息.value = '请先填写模型名。'
    当前状态文案.value = '配置错误：模型名不能为空。'
    return
  }

  切换Ollama模型中.value = true
  错误信息.value = ''
  const shouldLoad = !Ollama模型已加载.value
  当前状态文案.value = `正在${shouldLoad ? '启动' : '关闭'}模型：${model}...`
  try {
    const result = await 切换图片分类Ollama模型({
      baseUrl: 表单.baseUrl.trim() || 'http://127.0.0.1:11434',
      model,
      shouldLoad,
    })
    当前状态文案.value = result.message
    Ollama模型已加载.value = shouldLoad
    await 刷新Ollama模型状态()
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    错误信息.value = message
    当前状态文案.value = `模型状态切换失败：${message}`
    await 刷新Ollama模型状态()
  } finally {
    切换Ollama模型中.value = false
  }
}

async function 测试当前后端连接() {
  if (测试连接中.value) {
    return
  }
  测试连接中.value = true
  错误信息.value = ''
  当前状态文案.value = '正在测试后端连接...'
  try {
    const result = await 测试图片分类连接({
      backend: 表单.backend,
      baseUrl: 需要服务地址.value ? 表单.baseUrl : null,
      model: 需要模型名.value ? 表单.model : null,
      apiKey: 需要ApiKey.value ? 表单.apiKey : null,
    })
    当前状态文案.value = result.message
    if (使用Ollama后端.value) {
      await 刷新Ollama模型状态()
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    错误信息.value = message
    当前状态文案.value = `连接失败：${message}`
  } finally {
    测试连接中.value = false
  }
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

async function 执行分类(paths: string[]) {
  if (!paths.length || 分类进行中.value) {
    return
  }

  分类进行中.value = true
  停止进行中.value = false
  错误信息.value = ''
  重置分类结果状态(paths.length)
  当前状态文案.value = `正在分类，共 ${paths.length} 个输入项...`
  try {
    await 流式执行图片分类({
      inputs: paths,
      recursive: 表单.recursive,
      backend: 表单.backend,
      baseUrl: 需要服务地址.value ? 表单.baseUrl : null,
      model: 需要模型名.value ? 表单.model : null,
      apiKey: 需要ApiKey.value ? 表单.apiKey : null,
      videoFrameCount: 表单.videoFrameCount,
      failOnEmpty: false,
    }, 处理分类进度事件)
  } catch (error) {
    const message = 提取错误消息(error)
    if (是停止分类消息(message)) {
      错误信息.value = ''
      当前状态文案.value = message
      return
    }
    错误信息.value = message
    当前状态文案.value = '分类失败'
  } finally {
    分类进行中.value = false
    停止进行中.value = false
  }
}

async function 分类选中项() {
  await 执行分类([...已选输入路径.value])
}

async function 全部分类() {
  await 执行分类([...输入路径列表.value])
}

async function 停止当前分类() {
  if (!分类进行中.value || 停止进行中.value) {
    return
  }
  停止进行中.value = true
  错误信息.value = ''
  当前状态文案.value = '正在停止，等待当前任务结束...'
  try {
    await 停止图片分类()
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    错误信息.value = message
    当前状态文案.value = `停止失败：${message}`
    停止进行中.value = false
  }
}

async function 导出分类结果Csv() {
  if (!有可处理分类结果.value || 导出Csv中.value) {
    return
  }
  导出Csv中.value = true
  错误信息.value = ''
  当前状态文案.value = '正在选择 CSV 导出位置...'
  try {
    const outputPath = await 选择图片分类输出路径('csv')
    if (!outputPath) {
      当前状态文案.value = '已取消导出 CSV'
      return
    }
    const result = await 执行图片分类结果处理({
      action: 'export_csv',
      payload: {
        results: 分类结果列表.value,
        skipped: 跳过结果列表.value,
      },
      outputPath,
    })
    当前状态文案.value = result.message
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    错误信息.value = message
    当前状态文案.value = `导出 CSV 失败：${message}`
  } finally {
    导出Csv中.value = false
  }
}

async function 导出分类结果Json() {
  if (!有可处理分类结果.value || 导出Json中.value) {
    return
  }
  导出Json中.value = true
  错误信息.value = ''
  当前状态文案.value = '正在选择 JSON 导出位置...'
  try {
    const outputPath = await 选择图片分类输出路径('json')
    if (!outputPath) {
      当前状态文案.value = '已取消导出 JSON'
      return
    }
    const result = await 执行图片分类结果处理({
      action: 'export_json',
      payload: {
        results: 分类结果列表.value,
        skipped: 跳过结果列表.value,
      },
      outputPath,
    })
    当前状态文案.value = result.message
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    错误信息.value = message
    当前状态文案.value = `导出 JSON 失败：${message}`
  } finally {
    导出Json中.value = false
  }
}

async function 按分类移动图片() {
  if (!有可处理分类结果.value || 移动分类图片中.value) {
    return
  }
  移动分类图片中.value = true
  错误信息.value = ''
  当前状态文案.value = '正在选择分类输出目录...'
  try {
    const 原结果列表 = [...分类结果列表.value]
    const outputPath = await 选择图片分类输出路径('folder')
    if (!outputPath) {
      当前状态文案.value = '已取消移动分类图片'
      return
    }
    const result = await 执行图片分类结果处理({
      action: 'move_results',
      payload: {
        results: 分类结果列表.value,
        skipped: 跳过结果列表.value,
      },
      outputPath,
    })
    const 路径映射 = new Map(
      原结果列表.map((item, index) => [item.path, result.results?.[index]?.path ?? item.path]),
    )
    if (结果.value) {
      结果.value.results = result.results ?? []
      结果.value.skipped = result.skipped ?? 结果.value.skipped
      结果.value.summary = {
        ...结果.value.summary,
        classified: 结果.value.results.length,
        skipped: 结果.value.skipped.length,
      }
    }
    表单.inputs = 表单.inputs.map((path) => 路径映射.get(path) ?? path)
    已选输入路径.value = 已选输入路径.value.map((path) => 路径映射.get(path) ?? path)
    if (当前预览路径.value) {
      当前预览路径.value = 路径映射.get(当前预览路径.value) ?? 当前预览路径.value
    }
    if (当前结果路径.value) {
      当前结果路径.value = 路径映射.get(当前结果路径.value) ?? 当前结果路径.value
    }
    当前状态文案.value = result.message
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    错误信息.value = message
    当前状态文案.value = `移动分类图片失败：${message}`
  } finally {
    移动分类图片中.value = false
  }
}

onMounted(() => {
  void 刷新环境状态()
  void 刷新Ollama模型状态()
  void 初始化左侧面板高度同步()
  void 同步预览图片地址()
})

onBeforeUnmount(() => {
  右侧面板高度观察器?.disconnect()
  右侧面板高度观察器 = null
  图片分类状态.设置分类进行中(false)
})

watch(分类进行中, (value) => {
  图片分类状态.设置分类进行中(value)
}, { immediate: true })

watch(当前预览路径, () => {
  void 同步预览图片地址()
})

watch(() => 表单.backend, () => {
  错误信息.value = ''
  if (!使用Ollama后端.value) {
    Ollama模型已加载.value = false
    return
  }
  void 刷新Ollama模型状态()
})

watch(
  () => [表单.baseUrl, 表单.model],
  () => {
    if (!使用Ollama后端.value) {
      return
    }
    Ollama模型已加载.value = false
    void 刷新Ollama模型状态()
  },
)

watch(
  () => [分类结果已折叠.value, 预览详情已折叠.value, 跳过文件已折叠.value, 错误信息.value],
  () => {
    void nextTick().then(() => {
      同步左侧面板高度()
    })
  },
)
</script>

<template>
  <div class="image-classifier-page">
    <div class="image-classifier-page__main">
      <ElAlert
        v-if="错误信息"
        class="image-classifier-page__alert"
        title="执行失败"
        :description="错误信息"
        type="error"
        show-icon
        :closable="false"
      />

      <ElCard
        class="image-classifier-page__card image-classifier-page__config-card"
        :class="{ 'is-collapsed': 后端配置已折叠 }"
        shadow="never"
      >
        <template #header>
          <div class="image-classifier-page__panel-header">
            <span class="image-classifier-page__panel-title">
              <ElIcon><Picture /></ElIcon>
              <span>后端配置</span>
            </span>
            <div class="image-classifier-page__header-actions">
              <ElButton @click="运行环境弹窗可见 = true">
                <ElIcon><Monitor /></ElIcon>
                运行环境
              </ElButton>
              <ElButton
                class="image-classifier-page__icon-button"
                :title="后端配置已折叠 ? '展开配置' : '收起配置'"
                @click="后端配置已折叠 = !后端配置已折叠"
              >
                <ElIcon>
                  <CaretTop v-if="后端配置已折叠" />
                  <CaretBottom v-else />
                </ElIcon>
              </ElButton>
            </div>
          </div>
        </template>

        <ElForm v-if="!后端配置已折叠" label-position="top" class="image-classifier-page__config-form">
          <div class="image-classifier-page__config-grid">
            <ElFormItem label="后端类型">
              <ElSelect v-model="表单.backend">
                <ElOption
                  v-for="item in 后端选项"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </ElSelect>
            </ElFormItem>

            <ElFormItem v-if="需要服务地址" label="服务地址">
              <ElInput v-model="表单.baseUrl" placeholder="http://127.0.0.1:11434" />
            </ElFormItem>

            <ElFormItem v-if="需要模型名" label="模型名">
              <ElInput v-model="表单.model" placeholder="qwen3.5:4b" />
            </ElFormItem>

            <ElFormItem v-if="需要ApiKey" label="API Key">
              <ElInput
                v-model="表单.apiKey"
                type="password"
                show-password
                placeholder="可为空"
              />
            </ElFormItem>
          </div>
          <div v-if="使用Ollama后端" class="image-classifier-page__config-actions">
            <ElButton :disabled="!可操作Ollama按钮" @click="重置为本地Ollama默认配置">
              重置
            </ElButton>
            <ElButton :loading="启动Ollama中" :disabled="!可操作Ollama按钮 || 切换Ollama模型中" @click="启动本地Ollama">
              启动 Ollama
            </ElButton>
            <ElButton :loading="切换Ollama模型中" :disabled="!可操作Ollama按钮 || 启动Ollama中" @click="切换Ollama模型加载状态">
              {{ Ollama模型按钮文案 }}
            </ElButton>
            <ElButton :loading="测试连接中" :disabled="!可测试连接" @click="测试当前后端连接">
              测试连接
            </ElButton>
          </div>
          <div v-else class="image-classifier-page__config-actions">
            <ElButton :loading="测试连接中" :disabled="!可测试连接" @click="测试当前后端连接">
              测试连接
            </ElButton>
          </div>
          <p class="image-classifier-page__field-tip">
            {{ 后端选项.find((item) => item.value === 表单.backend)?.description }}
          </p>
        </ElForm>
      </ElCard>

      <ElCard class="image-classifier-page__card" shadow="never">
        <div class="image-classifier-page__toolbar">
          <ElButton :loading="选择输入中" :disabled="工具栏操作已禁用" @click="添加文件">
            <ElIcon><Plus /></ElIcon>
            添加文件
          </ElButton>
          <ElButton :loading="选择输入中" :disabled="工具栏操作已禁用" @click="添加文件夹">
            <ElIcon><FolderOpened /></ElIcon>
            添加文件夹
          </ElButton>
          <div class="image-classifier-page__toolbar-field">
            <span>递归子目录</span>
            <ElSwitch v-model="表单.recursive" :disabled="工具栏操作已禁用" />
          </div>
          <div class="image-classifier-page__toolbar-field">
            <span>视频抽帧数</span>
            <ElInputNumber v-model="表单.videoFrameCount" :min="1" :max="20" :disabled="工具栏操作已禁用" />
          </div>
          <ElButton type="primary" :disabled="!可分类选中项" @click="分类选中项">
            分类选中项
          </ElButton>
          <ElButton type="primary" plain :disabled="!可分类全部" @click="全部分类">
            全部分类
          </ElButton>
          <ElButton :disabled="!分类进行中" :loading="停止进行中" @click="停止当前分类">
            停止分类
          </ElButton>
          <ElButton :disabled="!有可处理分类结果 || 工具栏操作已禁用" :loading="移动分类图片中" @click="按分类移动图片">
            按分类移动图片
          </ElButton>
          <ElButton :disabled="!有可处理分类结果 || 工具栏操作已禁用" :loading="导出Csv中" @click="导出分类结果Csv">
            导出 CSV
          </ElButton>
          <ElButton :disabled="!有可处理分类结果 || 工具栏操作已禁用" :loading="导出Json中" @click="导出分类结果Json">
            导出 JSON
          </ElButton>
        </div>
      </ElCard>

      <div class="image-classifier-page__body">
        <ElCard ref="左侧面板实例" class="image-classifier-page__left-panel" :style="左侧面板样式" shadow="never">
          <template #header>
            <div class="image-classifier-page__panel-header">
              <span class="image-classifier-page__panel-title">
                <ElIcon><FolderOpened /></ElIcon>
                <span>全部图片</span>
              </span>
              <div class="image-classifier-page__header-actions">
                <ElButton size="small" :disabled="!可移除选中项" @click="移除选中输入项">
                  移除此文件
                </ElButton>
                <ElButton size="small" :disabled="分类进行中 || !输入路径列表.length" @click="清空全部">
                  清空
                </ElButton>
                <ElTag effect="plain">{{ 输入路径列表.length }} 项</ElTag>
              </div>
            </div>
          </template>

          <ElEmpty v-if="!输入路径列表.length" description="请先添加图片、视频或文件夹，文件夹会自动展开为内部媒体文件。" />
          <div v-else class="image-classifier-page__input-list">
            <button
              v-for="path in 输入路径列表"
              :key="path"
              type="button"
              class="image-classifier-page__input-item"
              :class="{ 'is-active': 输入项是否选中(path) }"
              @click="切换输入项选中(path, $event)"
            >
              <span class="image-classifier-page__input-item-text" :title="path">{{ path }}</span>
            </button>
          </div>
        </ElCard>

        <div ref="右侧面板元素" class="image-classifier-page__right-panel">
          <ElCard
            class="image-classifier-page__right-section image-classifier-page__right-section--result"
            :class="{
              'is-collapsed': 分类结果已折叠,
              'is-scrollable': 分类结果列表.length > 0 && !分类结果已折叠,
            }"
            shadow="never"
          >
            <template #header>
              <div class="image-classifier-page__panel-header">
                <span class="image-classifier-page__panel-title">
                  <ElIcon><Histogram /></ElIcon>
                  <span>分类结果</span>
                </span>
                <div class="image-classifier-page__header-actions">
                  <div class="image-classifier-page__header-tags">
                    <ElTag effect="plain">{{ 分类结果列表.length }} 项</ElTag>
                    <ElTag v-if="摘要" type="info" effect="plain">
                      {{ 毫秒转秒文案(摘要.durationMs) }}
                    </ElTag>
                  </div>
                  <ElButton
                    class="image-classifier-page__icon-button"
                    :title="分类结果已折叠 ? '展开分类结果' : '收起分类结果'"
                    @click="分类结果已折叠 = !分类结果已折叠"
                  >
                    <ElIcon>
                      <CaretTop v-if="分类结果已折叠" />
                      <CaretBottom v-else />
                    </ElIcon>
                  </ElButton>
                </div>
              </div>
            </template>

            <template v-if="!分类结果已折叠">
              <div v-if="!分类结果列表.length" class="image-classifier-page__empty-text">
                还没有分类结果，请先执行分类。
              </div>
              <div v-else class="image-classifier-page__table-wrap">
                <ElTable
                  :data="分类结果列表"
                  height="100%"
                  stripe
                  highlight-current-row
                  :current-row-key="当前结果路径 ?? undefined"
                  row-key="path"
                  @current-change="(row) => row && 选择结果项(row)"
                  @row-click="(row) => 选择结果项(row)"
                >
                  <ElTableColumn prop="path" label="图片" min-width="320" show-overflow-tooltip />
                  <ElTableColumn prop="labelZh" label="标签" min-width="120" />
                  <ElTableColumn prop="confidence" label="置信度" min-width="100" />
                </ElTable>
              </div>
            </template>
          </ElCard>

          <ElCard
            class="image-classifier-page__right-section"
            :class="{ 'is-collapsed': 预览详情已折叠 }"
            shadow="never"
          >
            <template #header>
              <div class="image-classifier-page__panel-header">
                <span class="image-classifier-page__panel-title">
                  <ElIcon><Picture /></ElIcon>
                  <span>预览 / 详情</span>
                </span>
                <ElButton
                  class="image-classifier-page__icon-button"
                  :title="预览详情已折叠 ? '展开预览 / 详情' : '收起预览 / 详情'"
                  @click="预览详情已折叠 = !预览详情已折叠"
                >
                  <ElIcon>
                    <CaretTop v-if="预览详情已折叠" />
                    <CaretBottom v-else />
                  </ElIcon>
                </ElButton>
              </div>
            </template>

            <div v-if="!预览详情已折叠" class="image-classifier-page__detail-layout">
              <div class="image-classifier-page__preview-box">
                <img v-if="预览图片地址" :src="预览图片地址" alt="预览图" class="image-classifier-page__preview-image">
                <div v-else class="image-classifier-page__preview-empty">
                  {{ 预览说明 }}
                </div>
              </div>

              <div class="image-classifier-page__detail-box">
                <div class="image-classifier-page__detail-line">
                  <span>路径</span>
                  <strong>{{ 当前结果项?.path ?? 当前预览路径 ?? '未选择' }}</strong>
                </div>
                <div class="image-classifier-page__detail-line">
                  <span>中文标签</span>
                  <strong>{{ 当前结果项?.labelZh ?? '-' }}</strong>
                </div>
                <div class="image-classifier-page__detail-line">
                  <span>英文标签</span>
                  <strong>{{ 当前结果项?.label ?? '-' }}</strong>
                </div>
                <div class="image-classifier-page__detail-line">
                  <span>来源类型</span>
                  <strong>
                    <ElTag v-if="当前结果项" :type="当前结果项.sourceKind === 'video' ? 'warning' : 'success'" effect="plain">
                      <VideoCamera v-if="当前结果项.sourceKind === 'video'" class="image-classifier-page__tag-icon" />
                      <Cpu v-else class="image-classifier-page__tag-icon" />
                      {{ 当前结果项.sourceKind }}
                    </ElTag>
                    <template v-else>-</template>
                  </strong>
                </div>
                <div class="image-classifier-page__detail-line">
                  <span>置信度</span>
                  <strong>{{ 当前结果项?.confidence ?? '-' }}</strong>
                </div>

                <div class="image-classifier-page__detail-text-block">
                  <div class="image-classifier-page__detail-text-title">原因说明</div>
                  <div class="image-classifier-page__detail-text">
                    {{ 当前结果项?.reason || '未选择分类结果。' }}
                  </div>
                </div>

                <div class="image-classifier-page__detail-text-block">
                  <div class="image-classifier-page__detail-text-title">原始响应</div>
                  <div class="image-classifier-page__detail-text">
                    {{ 当前结果项?.rawResponse || '暂无原始响应。' }}
                  </div>
                </div>
              </div>
            </div>
          </ElCard>

          <ElCard
            class="image-classifier-page__right-section"
            :class="{
              'is-collapsed': 跳过文件已折叠,
              'image-classifier-page__right-section--skipped': true,
              'is-scrollable': 跳过结果列表.length > 0 && !跳过文件已折叠,
            }"
            shadow="never"
          >
            <template #header>
              <div class="image-classifier-page__panel-header">
                <span class="image-classifier-page__panel-title">
                  <ElIcon><FolderOpened /></ElIcon>
                  <span>跳过文件</span>
                </span>
                <div class="image-classifier-page__header-actions">
                  <ElTag effect="plain">{{ 跳过结果列表.length }} 项</ElTag>
                  <ElButton
                    class="image-classifier-page__icon-button"
                    :title="跳过文件已折叠 ? '展开跳过文件' : '收起跳过文件'"
                    @click="跳过文件已折叠 = !跳过文件已折叠"
                  >
                    <ElIcon>
                      <CaretTop v-if="跳过文件已折叠" />
                      <CaretBottom v-else />
                    </ElIcon>
                  </ElButton>
                </div>
              </div>
            </template>

            <template v-if="!跳过文件已折叠">
              <div v-if="!跳过结果列表.length" class="image-classifier-page__empty-text image-classifier-page__empty-text--compact">
                当前没有跳过文件。
              </div>
              <div v-else class="image-classifier-page__table-wrap">
                <ElTable :data="跳过结果列表" height="100%" stripe>
                  <ElTableColumn prop="path" label="路径" min-width="320" show-overflow-tooltip />
                  <ElTableColumn prop="reason" label="原因" min-width="360" show-overflow-tooltip />
                </ElTable>
              </div>
            </template>
          </ElCard>
        </div>
      </div>
    </div>

    <div class="image-classifier-page__status-bar">
      <span>{{ 当前状态文案 }}</span>
      <span v-if="摘要">总数 {{ 摘要.total }} / 已分类 {{ 摘要.classified }} / 跳过 {{ 摘要.skipped }} / 已完成 {{ 已完成数量 }}</span>
      <span v-else>已选 {{ 已选输入数量 }} 项</span>
    </div>

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
  </div>
</template>

<style scoped>
.image-classifier-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  box-sizing: border-box;
  background: #eef2f6;
}

.image-classifier-page__main {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  padding: 12px 12px 0;
  overflow: auto;
}

.image-classifier-page__alert,
.image-classifier-page__card,
.image-classifier-page__status-bar {
  flex-shrink: 0;
}

.image-classifier-page__panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 24px;
}

.image-classifier-page__panel-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.image-classifier-page__config-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.image-classifier-page__config-card.is-collapsed :deep(.el-card__body) {
  display: none;
}

.image-classifier-page__right-section.is-collapsed :deep(.el-card__body) {
  display: none;
}

.image-classifier-page__config-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.image-classifier-page__field-tip {
  margin: 10px 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--el-text-color-regular);
}

.image-classifier-page__config-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.image-classifier-page__icon-button {
  width: 24px;
  min-width: 24px;
  height: 24px;
  padding: 0;
}

.image-classifier-page__toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 2px 0;
}

.image-classifier-page__toolbar-field {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 4px;
  color: var(--el-text-color-primary);
  white-space: nowrap;
}

.image-classifier-page__body {
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
  gap: 12px;
  flex: 1 1 auto;
  min-height: 0;
  align-items: stretch;
}

.image-classifier-page__left-panel,
.image-classifier-page__right-panel,
.image-classifier-page__right-section {
  min-height: 0;
}

.image-classifier-page__left-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  align-self: stretch;
}

.image-classifier-page__left-panel :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  padding: 10px;
  overflow: hidden;
}

.image-classifier-page__right-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  align-self: start;
}

.image-classifier-page__right-section {
  min-height: 0;
}

.image-classifier-page__right-section--result.is-scrollable {
  display: flex;
  flex-direction: column;
  max-height: 58%;
}

.image-classifier-page__right-section--skipped.is-scrollable {
  display: flex;
  flex-direction: column;
  max-height: 32%;
}

.image-classifier-page__right-section :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.image-classifier-page__input-list {
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 4px;
  width: 100%;
  min-height: 0;
  overflow: auto;
  padding: 2px;
  background: #ffffff;
  border: 1px solid #dcdfe6;
}

.image-classifier-page__input-item {
  display: flex;
  align-items: center;
  width: 100%;
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid transparent;
  border-radius: 0;
  background: #ffffff;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.image-classifier-page__input-item:hover {
  border-color: #dcdfe6;
  background: #f5f7fa;
}

.image-classifier-page__input-item.is-active {
  border-color: #7aaef7;
  background: #dbeafe;
}

.image-classifier-page__input-item-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-primary);
}

.image-classifier-page__header-tags {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.image-classifier-page__header-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.image-classifier-page__table-wrap {
  display: flex;
  min-height: 0;
  overflow: hidden;
}

.image-classifier-page__empty-text {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
  padding: 16px;
  text-align: center;
  line-height: 1.6;
  color: var(--el-text-color-secondary);
}

.image-classifier-page__empty-text--compact {
  min-height: 72px;
}

.image-classifier-page :deep(.el-table) {
  --el-table-header-bg-color: #f5f7fa;
  --el-table-row-hover-bg-color: #edf4ff;
}

.image-classifier-page :deep(.el-table .current-row td.el-table__cell) {
  background: #dbeafe;
}

.image-classifier-page__detail-layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 12px;
  min-height: 0;
  align-items: start;
}

.image-classifier-page__preview-box {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  aspect-ratio: 1 / 1;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  background: #fafafa;
  overflow: hidden;
}

.image-classifier-page__preview-image {
  width: 100%;
  max-height: 70vh;
  height: auto;
  object-fit: contain;
}

.image-classifier-page__preview-empty {
  padding: 16px;
  text-align: center;
  line-height: 1.6;
  color: var(--el-text-color-secondary);
}

.image-classifier-page__detail-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.image-classifier-page__detail-line {
  display: grid;
  grid-template-columns: 84px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  font-size: 13px;
}

.image-classifier-page__detail-line span {
  color: var(--el-text-color-secondary);
}

.image-classifier-page__detail-line strong {
  min-width: 0;
  overflow-wrap: anywhere;
  color: var(--el-text-color-primary);
}

.image-classifier-page__detail-text-block {
  display: grid;
  gap: 6px;
}

.image-classifier-page__detail-text-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.image-classifier-page__detail-text {
  min-height: 72px;
  padding: 10px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  background: #fafafa;
  line-height: 1.7;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  color: var(--el-text-color-regular);
}

.image-classifier-page__tag-icon {
  width: 14px;
  height: 14px;
  margin-right: 4px;
}

.image-classifier-page__status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 12px 12px 12px;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #ffffff;
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.image-classifier-page__dialog-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

@media (max-width: 1280px) {
  .image-classifier-page__config-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .image-classifier-page__detail-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 980px) {
  .image-classifier-page__body {
    grid-template-columns: 1fr;
  }

  .image-classifier-page__status-bar {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
