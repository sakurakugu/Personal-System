<script setup lang="ts">
import { 查询我的世界服务器, type 我的世界服务器查询结果, type 我的世界服务器版本 } from '@/shared/minecraft-server'
import { 写入我的世界服务器存储, 读取我的世界服务器存储, type 我的世界服务器记录 } from '@/shared/minecraft-server-storage'
import { Connection, CopyDocument, DataAnalysis, Monitor, Position, RefreshRight } from '@element-plus/icons-vue'
import { ElAlert, ElButton, ElCard, ElForm, ElFormItem, ElInput, ElInputNumber, ElMessage, ElOption, ElSelect, ElSlider, ElTag } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'

type 查询表单 = {
  address: string
  edition: 我的世界服务器版本
  timeout: number
}

const 表单 = reactive<查询表单>({
  address: '',
  edition: 'auto',
  timeout: 3,
})

const route = useRoute()

const 查询中 = ref(false)
const 错误信息 = ref('')
const 记录加载中 = ref(false)
const 结果 = ref<我的世界服务器查询结果 | null>(null)
const 当前状态 = ref('等待输入服务器地址。')
const 收藏列表 = ref<我的世界服务器记录[]>([])
const 历史列表 = ref<我的世界服务器记录[]>([])
const 描述背景亮度 = ref(55)

const 协议选项: Array<{ label: string; value: 我的世界服务器版本; description: string }> = [
  { label: '自动识别', value: 'auto', description: '优先按常见端口猜测，再回退到另一种协议。' },
  { label: 'Java 版', value: 'java', description: '适合普通 PC Java 版服务器。' },
  { label: 'Bedrock 版', value: 'bedrock', description: '适合基岩版、手机端或网易 Bedrock 兼容服务。' },
]
type Minecraft文本样式状态 = {
  color: string | null
  bold: boolean
  italic: boolean
  underline: boolean
  strikethrough: boolean
  obfuscated: boolean
}

type Minecraft文本片段 = {
  text: string
  style: Record<string, string>
  className: string[]
  obfuscated?: boolean
}

const Minecraft颜色映射: Record<string, string> = {
  '0': '#000000',
  '1': '#0000aa',
  '2': '#00aa00',
  '3': '#00aaaa',
  '4': '#aa0000',
  '5': '#aa00aa',
  '6': '#ffaa00',
  '7': '#aaaaaa',
  '8': '#555555',
  '9': '#5555ff',
  a: '#55ff55',
  b: '#55ffff',
  c: '#ff5555',
  d: '#ff55ff',
  e: '#ffff55',
  f: '#ffffff',
}

const 服务器图标地址 = computed(() => {
  const icon = 结果.value?.icon?.trim()
  return icon ? icon : ''
})
const 描述富文本行列表 = computed(() => 解析Minecraft文本(结果.value?.description || 结果.value?.error || '没有返回描述信息。'))
const 玩家示例富文本行列表 = computed(() => {
  if (!结果.value?.samplePlayers.length) {
    return 解析Minecraft文本('当前没有玩家示例信息。')
  }
  return 结果.value.samplePlayers.flatMap((player, index) => {
    const lines = 解析Minecraft文本(player)
    if (index === 0) {
      return lines
    }
    return [[{ text: '', style: {}, className: [] }], ...lines]
  })
})
const 描述纯文本 = computed(() => 提取Minecraft纯文本(结果.value?.description || 结果.value?.error || '没有返回描述信息。'))
const 描述区域样式 = computed(() => {
  const 有描述内容 = Boolean(结果.value?.description?.trim())
  const 亮度 = 有描述内容 ? Math.max(0, Math.min(255, Math.round(描述背景亮度.value))) : 255
  const 颜色 = `rgb(${亮度}, ${亮度}, ${亮度})`
  const 前景色 = 亮度 >= 128 ? '#111111' : '#f2f2f2'
  return {
    backgroundColor: 颜色,
    color: 前景色,
  }
})
const 结果摘要行列表 = computed(() => {
  if (!结果.value) {
    return []
  }
  const result = 结果.value
  const lines = [
    `地址：${result.requestedAddress}`,
    `在线：${result.online ? '是' : '否'}`,
    `协议：${result.resolvedEdition || '未识别'}`,
    `主机：${result.host}`,
    `端口：${result.resolvedPort ?? result.requestedPort ?? '-'}`,
    `延迟：${result.latencyMs != null ? `${result.latencyMs} ms` : '-'}`,
    `版本：${result.versionName || '-'}`,
    `协议版本：${result.protocolVersion ?? '-'}`,
    `玩家：${result.playersOnline ?? '-'} / ${result.playersMax ?? '-'}`,
    `地图：${result.mapName || '-'}`,
    `模式：${result.gameMode || '-'}`,
    `品牌：${result.brand || '-'}`,
  ]
  if (result.error) {
    lines.push(`错误：${result.error}`)
  }
  return lines
})
const 原始结果JSON = computed(() => (结果.value ? JSON.stringify(结果.value, null, 2) : ''))
const 当前地址已收藏 = computed(() => {
  const address = 表单.address.trim()
  return Boolean(address) && 收藏列表.value.some((item) => item.address === address && item.edition === 表单.edition)
})
const 底部状态右侧文案 = computed(() => {
  if (结果.value) {
    return [
      `状态 ${结果.value.online ? '在线' : '离线'}`,
      `协议 ${结果.value.resolvedEdition || '-'}`,
      `玩家 ${结果.value.playersOnline ?? '-'} / ${结果.value.playersMax ?? '-'}`,
      `延迟 ${结果.value.latencyMs != null ? `${结果.value.latencyMs} ms` : '-'}`,
    ].join(' / ')
  }
  return `收藏 ${收藏列表.value.length} 项 / 最近查询 ${历史列表.value.length} 项`
})

let 扰动计时器: number | null = null
const 扰动种子 = ref(0)

启动扰动计时器()
onBeforeUnmount(() => {
  停止扰动计时器()
})

初始化路由参数()
onMounted(() => {
  读取本地记录()
})

async function 执行查询() {
  const address = 表单.address.trim()
  if (!address || 查询中.value) {
    return
  }

  查询中.value = true
  错误信息.value = ''
  当前状态.value = '正在查询服务器状态...'
  try {
    const result = await 查询我的世界服务器({
      address,
      edition: 表单.edition,
      timeout: 表单.timeout,
    })
    结果.value = result
    记录历史(address, 表单.edition)
    当前状态.value = result.online
      ? `查询完成：${result.host} 在线`
      : `查询完成：${result.error || '服务器离线'}`
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    错误信息.value = message
    当前状态.value = `查询失败：${message}`
    结果.value = null
  } finally {
    查询中.value = false
  }
}

function 重置() {
  表单.address = ''
  表单.edition = 'auto'
  表单.timeout = 3
  错误信息.value = ''
  结果.value = null
  当前状态.value = '已重置。'
}

function 读取本地记录() {
  if (记录加载中.value) {
    return
  }
  记录加载中.value = true
  void 读取我的世界服务器存储()
    .then((data) => {
      收藏列表.value = data.favorites
      历史列表.value = data.history
    })
    .catch((error) => {
      const message = error instanceof Error ? error.message : String(error)
      错误信息.value = `读取记录失败：${message}`
      收藏列表.value = []
      历史列表.value = []
    })
    .finally(() => {
      记录加载中.value = false
    })
}

function 保存本地记录() {
  void 写入我的世界服务器存储({
    favorites: 收藏列表.value,
    history: 历史列表.value,
  })
}

function 记录历史(address: string, edition: 我的世界服务器版本) {
  历史列表.value = [{ address, edition }, ...历史列表.value.filter((item) => !(item.address === address && item.edition === edition))].slice(0, 30)
  保存本地记录()
}

function 加入当前收藏() {
  const address = 表单.address.trim()
  if (!address) {
    ElMessage.info('请先输入服务器地址')
    return
  }
  if (当前地址已收藏.value) {
    ElMessage.info('这个服务器已经在收藏里')
    return
  }
  收藏列表.value = [{ address, edition: 表单.edition }, ...收藏列表.value].slice(0, 20)
  保存本地记录()
  当前状态.value = '已加入收藏。'
}

function 移除收藏(address: string, edition: 我的世界服务器版本) {
  收藏列表.value = 收藏列表.value.filter((item) => !(item.address === address && item.edition === edition))
  保存本地记录()
  当前状态.value = '已移除收藏。'
}

function 清空历史() {
  历史列表.value = []
  保存本地记录()
  当前状态.value = '已清空历史记录。'
}

function 刷新记录() {
  读取本地记录()
}

function 应用记录(item: 我的世界服务器记录) {
  表单.address = item.address
  表单.edition = item.edition
  当前状态.value = `已载入：${item.address}`
}

function 格式化记录(item: 我的世界服务器记录) {
  return `[${item.edition}] ${item.address}`
}

async function 复制描述纯文本() {
  try {
    await navigator.clipboard.writeText(描述纯文本.value)
    ElMessage.success('描述纯文本已复制')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '复制失败，请检查权限')
  }
}

async function 复制原始结果JSON() {
  if (!原始结果JSON.value) {
    ElMessage.info('当前没有可复制的原始结果')
    return
  }
  try {
    await navigator.clipboard.writeText(原始结果JSON.value)
    ElMessage.success('原始结果 JSON 已复制')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '复制失败，请检查权限')
  }
}

function 初始化路由参数() {
  const routeAddress = Array.isArray(route.query.address) ? route.query.address[0] : route.query.address
  const routeEdition = Array.isArray(route.query.edition) ? route.query.edition[0] : route.query.edition

  if (typeof routeAddress === 'string' && routeAddress.trim()) {
    表单.address = routeAddress.trim()
  }
  if (routeEdition === 'auto' || routeEdition === 'java' || routeEdition === 'bedrock') {
    表单.edition = routeEdition
  }
}

function 创建默认样式状态(): Minecraft文本样式状态 {
  return {
    color: null,
    bold: false,
    italic: false,
    underline: false,
    strikethrough: false,
    obfuscated: false,
  }
}

function 克隆样式状态(state: Minecraft文本样式状态): Minecraft文本样式状态 {
  return {
    color: state.color,
    bold: state.bold,
    italic: state.italic,
    underline: state.underline,
    strikethrough: state.strikethrough,
    obfuscated: state.obfuscated,
  }
}

function 解析Minecraft文本(input: string): Minecraft文本片段[][] {
  const lines: Minecraft文本片段[][] = [[]]
  let buffer = ''
  let state = 创建默认样式状态()

  function 推入片段() {
    if (!buffer) {
      return
    }
    lines[lines.length - 1].push({
      text: state.obfuscated ? 生成扰动文本(buffer, 扰动种子.value) : buffer,
      style: 生成片段样式(state),
      className: 生成片段类名(state),
      obfuscated: state.obfuscated,
    })
    buffer = ''
  }

  for (let index = 0; index < input.length; index += 1) {
    const current = input[index]
    const next = input[index + 1]?.toLowerCase()

    if (current === '\n') {
      推入片段()
      lines.push([])
      continue
    }

    if (current === '§' && next) {
      推入片段()
      state = 应用Minecraft格式码(state, next)
      index += 1
      continue
    }

    buffer += current
  }

  推入片段()

  return lines.length ? lines : [[{ text: '', style: {}, className: [] }]]
}

function 应用Minecraft格式码(
  previous: Minecraft文本样式状态,
  code: string,
): Minecraft文本样式状态 {
  if (code in Minecraft颜色映射) {
    return {
      color: Minecraft颜色映射[code],
      bold: false,
      italic: false,
      underline: false,
      strikethrough: false,
      obfuscated: false,
    }
  }

  const next = 克隆样式状态(previous)
  if (code === 'l') {
    next.bold = true
  } else if (code === 'k') {
    next.obfuscated = true
  } else if (code === 'm') {
    next.strikethrough = true
  } else if (code === 'n') {
    next.underline = true
  } else if (code === 'o') {
    next.italic = true
  } else if (code === 'r') {
    return 创建默认样式状态()
  }

  return next
}

function 生成片段样式(state: Minecraft文本样式状态) {
  return {
    color: state.color || 'inherit',
    fontWeight: state.bold ? '700' : 'inherit',
    fontStyle: state.italic ? 'italic' : 'normal',
    textDecoration: [
      state.underline ? 'underline' : '',
      state.strikethrough ? 'line-through' : '',
    ].filter(Boolean).join(' ') || 'none',
  }
}

function 生成片段类名(state: Minecraft文本样式状态) {
  const classNames: string[] = []
  if (state.obfuscated) {
    classNames.push('is-obfuscated')
  }
  if (state.bold) {
    classNames.push('is-bold')
  }
  if (state.italic) {
    classNames.push('is-italic')
  }
  if (state.underline) {
    classNames.push('is-underline')
  }
  if (state.strikethrough) {
    classNames.push('is-strikethrough')
  }
  return classNames
}

function 提取Minecraft纯文本(input: string) {
  let result = ''
  for (let index = 0; index < input.length; index += 1) {
    const current = input[index]
    const next = input[index + 1]
    if (current === '§' && next) {
      index += 1
      continue
    }
    result += current
  }
  return result
}

function 启动扰动计时器() {
  if (typeof window === 'undefined' || 扰动计时器 != null) {
    return
  }
  扰动计时器 = window.setInterval(() => {
    扰动种子.value += 1
  }, 180)
}

function 停止扰动计时器() {
  if (扰动计时器 == null || typeof window === 'undefined') {
    return
  }
  window.clearInterval(扰动计时器)
  扰动计时器 = null
}

function 生成扰动文本(input: string, seed: number) {
  const 字符集 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@#$%&*?'
  let output = ''
  for (let index = 0; index < input.length; index += 1) {
    const current = input[index]
    if (/\s/.test(current)) {
      output += current
      continue
    }
    const code = (seed * 17 + index * 31 + current.charCodeAt(0)) % 字符集.length
    output += 字符集[code]
  }
  return output
}
</script>

<template>
  <div class="minecraft-server-page">
    <div class="minecraft-server-page__main">
      <ElAlert
        v-if="错误信息"
        class="minecraft-server-page__alert"
        type="error"
        :title="错误信息"
        show-icon
        :closable="false"
      />

      <ElCard class="minecraft-server-page__panel minecraft-server-page__panel--config" shadow="never">
        <template #header>
          <div class="minecraft-server-page__panel-header">
            <span class="minecraft-server-page__panel-title">
              <Connection />
              查询配置
            </span>
            <div class="minecraft-server-page__header-actions">
              <ElButton :loading="记录加载中" plain size="small" @click="刷新记录">
                刷新记录
              </ElButton>
            </div>
          </div>
        </template>

        <ElForm class="minecraft-server-page__form" label-position="top">
          <div class="minecraft-server-page__config-grid">
            <ElFormItem class="minecraft-server-page__field" label="服务器地址">
              <ElInput
                v-model="表单.address"
                placeholder="例如 play.example.com 或 play.example.com:25565"
                clearable
                @keyup.enter="执行查询"
              />
            </ElFormItem>

            <ElFormItem class="minecraft-server-page__field" label="协议">
              <ElSelect v-model="表单.edition">
                <ElOption
                  v-for="item in 协议选项"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </ElSelect>
            </ElFormItem>

            <ElFormItem class="minecraft-server-page__field" label="超时（秒）">
              <ElInputNumber v-model="表单.timeout" :min="1" :max="15" :step="0.5" controls-position="right" />
            </ElFormItem>
          </div>

          <div class="minecraft-server-page__actions">
            <ElButton type="primary" :loading="查询中" :disabled="!表单.address.trim()" @click="执行查询">
              <template #icon><RefreshRight /></template>
              开始查询
            </ElButton>
            <ElButton :disabled="查询中" @click="重置">重置</ElButton>
            <ElButton plain :disabled="当前地址已收藏" @click="加入当前收藏">
              加入收藏
            </ElButton>
          </div>
        </ElForm>
      </ElCard>

      <div class="minecraft-server-page__body">
        <div class="minecraft-server-page__sidebar">
          <ElCard class="minecraft-server-page__panel minecraft-server-page__panel--summary" shadow="never">
            <template #header>
              <div class="minecraft-server-page__panel-header">
                <span class="minecraft-server-page__panel-title">
                  <DataAnalysis />
                  摘要
                </span>
              </div>
            </template>

            <div v-if="结果" class="minecraft-server-page__summary">
              <div class="minecraft-server-page__summary-icon-wrap">
                <img
                  v-if="服务器图标地址"
                  :src="服务器图标地址"
                  alt="服务器图标"
                  class="minecraft-server-page__summary-icon"
                >
                <div v-else class="minecraft-server-page__summary-icon minecraft-server-page__summary-icon--empty">
                  MC
                </div>
              </div>
              <div class="minecraft-server-page__summary-main">
                <div class="minecraft-server-page__summary-title-row">
                  <strong>{{ 结果.host }}</strong>
                </div>
                <div class="minecraft-server-page__summary-tag-row">
                  <ElTag :type="结果.online ? 'success' : 'danger'" effect="plain">
                    {{ 结果.online ? '在线' : '离线' }}
                  </ElTag>
                  <ElTag v-if="结果.resolvedEdition" effect="plain">
                    {{ 结果.resolvedEdition }}
                  </ElTag>
                </div>
                <div class="minecraft-server-page__summary-subtitle">
                  {{ 结果.versionName || '未返回版本信息' }}
                </div>
              </div>
            </div>

            <div v-else class="minecraft-server-page__empty">
              请输入服务器地址后开始查询。
            </div>

            <div class="minecraft-server-page__summary-text">
              <div
                v-for="line in 结果摘要行列表"
                :key="line"
                class="minecraft-server-page__summary-line"
              >
                {{ line }}
              </div>
            </div>
          </ElCard>

          <ElCard class="minecraft-server-page__panel" shadow="never">
            <template #header>
              <div class="minecraft-server-page__panel-header">
                <span class="minecraft-server-page__panel-title">
                  <Monitor />
                  收藏服务器
                </span>
                <div class="minecraft-server-page__header-actions">
                  <ElTag effect="plain">{{ 收藏列表.length }} 项</ElTag>
                </div>
              </div>
            </template>

            <div v-if="!收藏列表.length" class="minecraft-server-page__list-empty">
              还没有收藏服务器。
            </div>
            <div v-else class="minecraft-server-page__record-list">
              <div
                v-for="item in 收藏列表"
                :key="`favorite-${item.edition}-${item.address}`"
                class="minecraft-server-page__record-row"
              >
                <button
                  type="button"
                  class="minecraft-server-page__record-item"
                  @click="应用记录(item)"
                >
                  <span class="minecraft-server-page__record-item-text" :title="格式化记录(item)">
                    {{ 格式化记录(item) }}
                  </span>
                </button>
                <ElButton text @click="移除收藏(item.address, item.edition)">
                  移除
                </ElButton>
              </div>
            </div>
          </ElCard>

          <ElCard class="minecraft-server-page__panel" shadow="never">
            <template #header>
              <div class="minecraft-server-page__panel-header">
                <span class="minecraft-server-page__panel-title">
                  <Connection />
                  最近查询
                </span>
                <div class="minecraft-server-page__header-actions">
                  <ElButton text :disabled="!历史列表.length" @click="清空历史">
                    清空历史
                  </ElButton>
                  <ElTag effect="plain">{{ 历史列表.length }} 项</ElTag>
                </div>
              </div>
            </template>

            <div v-if="!历史列表.length" class="minecraft-server-page__list-empty">
              还没有查询记录。
            </div>
            <div v-else class="minecraft-server-page__record-list">
              <button
                v-for="item in 历史列表"
                :key="`history-${item.edition}-${item.address}`"
                type="button"
                class="minecraft-server-page__record-item"
                @click="应用记录(item)"
              >
                <span class="minecraft-server-page__record-item-text" :title="格式化记录(item)">
                  {{ 格式化记录(item) }}
                </span>
              </button>
            </div>
          </ElCard>
        </div>

        <ElCard class="minecraft-server-page__panel minecraft-server-page__panel--details" shadow="never">
          <template #header>
            <div class="minecraft-server-page__panel-header">
              <span class="minecraft-server-page__panel-title">
                <Position />
                详细结果
              </span>
            </div>
          </template>

          <template v-if="结果">
            <section class="minecraft-server-page__detail-card">
              <div class="minecraft-server-page__detail-title minecraft-server-page__detail-title--with-action">
                <span class="minecraft-server-page__detail-title-label">
                  <Monitor />
                  服务器描述
                </span>
                <div class="minecraft-server-page__detail-title-actions">
                  <span class="minecraft-server-page__detail-slider-label">背景</span>
                  <ElSlider
                    v-model="描述背景亮度"
                    class="minecraft-server-page__detail-slider"
                    :min="0"
                    :max="255"
                    :show-tooltip="false"
                  />
                  <ElButton text @click="复制描述纯文本">
                    <template #icon><CopyDocument /></template>
                    复制纯文本
                  </ElButton>
                </div>
              </div>
              <div class="minecraft-server-page__description-box" :style="描述区域样式">
                <div class="minecraft-server-page__description-icon-wrap" :style="描述区域样式">
                  <img
                    v-if="服务器图标地址"
                    :src="服务器图标地址"
                    alt="服务器图标"
                    class="minecraft-server-page__description-icon"
                  >
                  <div v-else class="minecraft-server-page__description-icon minecraft-server-page__description-icon--empty">
                    MC
                  </div>
                </div>
                <div class="minecraft-server-page__detail-text minecraft-server-page__detail-text--description" :style="描述区域样式">
                  <div
                    v-for="(line, lineIndex) in 描述富文本行列表"
                    :key="`motd-line-${lineIndex}`"
                    class="minecraft-server-page__motd-line"
                  >
                    <span
                      v-for="(segment, segmentIndex) in line"
                      :key="`motd-segment-${lineIndex}-${segmentIndex}`"
                      :class="segment.className"
                      :style="segment.style"
                    >
                      {{ segment.text || '\u00A0' }}
                    </span>
                  </div>
                </div>
              </div>
            </section>

            <section class="minecraft-server-page__detail-card">
              <div class="minecraft-server-page__detail-title">
                玩家示例
              </div>
              <div class="minecraft-server-page__detail-text">
                <div
                  v-for="(line, lineIndex) in 玩家示例富文本行列表"
                  :key="`player-line-${lineIndex}`"
                  class="minecraft-server-page__motd-line"
                >
                  <span
                    v-for="(segment, segmentIndex) in line"
                    :key="`player-segment-${lineIndex}-${segmentIndex}`"
                    :class="segment.className"
                    :style="segment.style"
                  >
                    {{ segment.text || '\u00A0' }}
                  </span>
                </div>
              </div>
            </section>

            <section class="minecraft-server-page__detail-card">
              <div class="minecraft-server-page__detail-title minecraft-server-page__detail-title--with-action">
                <span class="minecraft-server-page__detail-title-label">
                  <DataAnalysis />
                  原始结果 JSON
                </span>
                <ElButton text @click="复制原始结果JSON">
                  <template #icon><CopyDocument /></template>
                  复制 JSON
                </ElButton>
              </div>
              <pre class="minecraft-server-page__json">{{ 原始结果JSON }}</pre>
            </section>
          </template>

          <div v-else class="minecraft-server-page__empty minecraft-server-page__empty--details">
            还没有查询结果，请先输入服务器地址。
          </div>
        </ElCard>
      </div>
    </div>

    <div class="minecraft-server-page__status-bar">
      <span>{{ 当前状态 }}</span>
      <span>{{ 底部状态右侧文案 }}</span>
    </div>
  </div>
</template>

<style scoped>
.minecraft-server-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  box-sizing: border-box;
  background: linear-gradient(180deg, #f5f7fb 0%, #edf1f6 100%);
}

.minecraft-server-page__main {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  padding: 12px 12px 0;
  overflow: auto;
}

.minecraft-server-page__alert {
  flex-shrink: 0;
}

.minecraft-server-page__panel {
  border-radius: 16px;
  border: 1px solid #d8dde6;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 253, 0.98));
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
}

.minecraft-server-page__panel--config {
  flex-shrink: 0;
}

.minecraft-server-page__panel--config :deep(.el-card__body) {
  padding: 20px 24px 18px;
}

.minecraft-server-page__panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 24px;
}

.minecraft-server-page__panel-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: #1d2430;
  white-space: nowrap;
  flex-shrink: 0;
}

.minecraft-server-page__header-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.minecraft-server-page__form {
  display: grid;
  gap: 16px;
}

.minecraft-server-page__config-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(180px, 220px) minmax(160px, 180px);
  gap: 16px;
  align-items: start;
}

.minecraft-server-page__field {
  min-width: 0;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  column-gap: 12px;
  align-items: center;
  margin-bottom: 0;
}

.minecraft-server-page__field :deep(.el-form-item__label) {
  padding: 0;
  line-height: 40px;
  white-space: nowrap;
}

.minecraft-server-page__field :deep(.el-form-item__content) {
  min-width: 0;
}

.minecraft-server-page__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.minecraft-server-page__body {
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
  gap: 12px;
  flex: 1 1 auto;
  min-height: 0;
  align-items: start;
}

.minecraft-server-page__sidebar {
  display: grid;
  gap: 12px;
  min-height: 0;
}

.minecraft-server-page__panel--details {
  align-self: start;
}

.minecraft-server-page__summary {
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr);
  gap: 14px;
  align-items: center;
  margin-bottom: 12px;
}

.minecraft-server-page__summary-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
}

.minecraft-server-page__summary-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  border: 1px solid #d3d8e0;
  background: linear-gradient(180deg, #ffffff, #eef2f7);
  image-rendering: pixelated;
  object-fit: contain;
}

.minecraft-server-page__summary-icon--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 800;
  color: #3b4a63;
}

.minecraft-server-page__summary-main {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.minecraft-server-page__summary-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.minecraft-server-page__summary-title-row strong {
  font-size: 18px;
  line-height: 1.2;
  color: #1d2430;
}

.minecraft-server-page__summary-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.minecraft-server-page__summary-subtitle {
  color: #667085;
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.minecraft-server-page__summary-text {
  display: grid;
  gap: 6px;
  padding-top: 4px;
  font-size: 13px;
  line-height: 1.7;
  color: #344054;
}

.minecraft-server-page__summary-line {
  padding: 2px 0;
  border-bottom: 1px dashed #e6eaf0;
}

.minecraft-server-page__summary-line:last-child {
  border-bottom: 0;
}

.minecraft-server-page__record-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.minecraft-server-page__record-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.minecraft-server-page__record-item {
  display: flex;
  align-items: center;
  width: 100%;
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid #dcdfe6;
  border-radius: 10px;
  background: #ffffff;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.minecraft-server-page__record-item:hover {
  border-color: #7aaef7;
  background: #f8fbff;
}

.minecraft-server-page__record-item-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #344054;
}

.minecraft-server-page__list-empty {
  color: #667085;
  line-height: 1.8;
}

.minecraft-server-page__detail-card {
  display: grid;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid #dbe1ea;
  border-radius: 14px;
  background: rgba(246, 248, 252, 0.9);
}

.minecraft-server-page__detail-card + .minecraft-server-page__detail-card {
  margin-top: 12px;
}

.minecraft-server-page__detail-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: #1d2430;
  white-space: nowrap;
}

.minecraft-server-page__detail-title--with-action {
  justify-content: space-between;
}

.minecraft-server-page__detail-title-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.minecraft-server-page__detail-title-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.minecraft-server-page__detail-slider-label {
  color: #667085;
  font-size: 13px;
  font-weight: 500;
}

.minecraft-server-page__detail-slider {
  width: 140px;
}

.minecraft-server-page__description-box {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 12px;
  border-radius: 12px;
}

.minecraft-server-page__description-icon-wrap {
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.minecraft-server-page__description-icon {
  width: 64px;
  height: 64px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.45);
  object-fit: contain;
  image-rendering: pixelated;
}

.minecraft-server-page__description-icon--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 800;
}

.minecraft-server-page__detail-text {
  min-height: 72px;
  white-space: pre-wrap;
  line-height: 1.8;
  color: #344054;
  overflow-wrap: anywhere;
}

.minecraft-server-page__detail-text--description {
  min-height: 64px;
}

.minecraft-server-page__motd-line {
  min-height: 1.8em;
}

.minecraft-server-page__json {
  margin: 0;
  min-height: 160px;
  max-height: 420px;
  overflow: auto;
  padding: 12px;
  border-radius: 10px;
  background: #f8fafc;
  color: #1f2937;
  font-family:
    "Cascadia Mono",
    "JetBrains Mono",
    Consolas,
    "Courier New",
    monospace;
  font-size: 16px;
  line-height: 1.2;
  white-space: pre-wrap;
  word-break: break-word;
}

.minecraft-server-page__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  color: #667085;
}

.minecraft-server-page__empty--details {
  min-height: 520px;
}

.minecraft-server-page__detail-text :deep(.is-obfuscated) {
  letter-spacing: 0.04em;
}

.minecraft-server-page__status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border-top: 1px solid #d8dde6;
  background: rgba(255, 255, 255, 0.9);
  color: #475467;
  font-size: 12px;
  line-height: 1.6;
  flex-shrink: 0;
}

.dark .minecraft-server-page {
  background: linear-gradient(180deg, #0f1419 0%, #121820 100%);
}

.dark .minecraft-server-page__panel {
  border-color: #273244;
  background: linear-gradient(180deg, rgba(20, 26, 34, 0.98), rgba(16, 21, 28, 0.98));
  box-shadow: 0 12px 26px rgba(0, 0, 0, 0.24);
}

.dark .minecraft-server-page__panel-title,
.dark .minecraft-server-page__summary-title-row strong,
.dark .minecraft-server-page__detail-title {
  color: #eef2f8;
}

.dark .minecraft-server-page__summary-subtitle,
.dark .minecraft-server-page__summary-text,
.dark .minecraft-server-page__record-item-text,
.dark .minecraft-server-page__list-empty,
.dark .minecraft-server-page__detail-slider-label,
.dark .minecraft-server-page__detail-text,
.dark .minecraft-server-page__empty {
  color: #a9b4c4;
}

.dark .minecraft-server-page__summary-icon {
  border-color: #324055;
  background: linear-gradient(180deg, rgba(24, 30, 39, 0.95), rgba(18, 23, 31, 0.92));
}

.dark .minecraft-server-page__summary-icon--empty {
  color: #d4dde9;
}

.dark .minecraft-server-page__summary-line {
  border-bottom-color: #2a3444;
}

.dark .minecraft-server-page__record-item {
  border-color: #2a3444;
  background: #141b23;
}

.dark .minecraft-server-page__detail-card {
  border-color: #2a3444;
  background: rgba(22, 28, 36, 0.9);
}

.dark .minecraft-server-page__json {
  background: #11161d;
  color: #dbe4f0;
}

.dark .minecraft-server-page__status-bar {
  border-top-color: #273244;
  background: rgba(16, 21, 28, 0.94);
  color: #a9b4c4;
}

@media (max-width: 1100px) {
  .minecraft-server-page__body,
  .minecraft-server-page__config-grid {
    grid-template-columns: 1fr;
  }

  .minecraft-server-page__detail-title--with-action {
    align-items: flex-start;
    flex-direction: column;
  }

  .minecraft-server-page__detail-title-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .minecraft-server-page__field {
    grid-template-columns: 1fr;
    row-gap: 6px;
  }

  .minecraft-server-page__field :deep(.el-form-item__label) {
    line-height: 1.5;
  }

  .minecraft-server-page__status-bar {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 767px) {
  .minecraft-server-page__main {
    padding: 10px 10px 0;
  }

  .minecraft-server-page__panel--config :deep(.el-card__body) {
    padding: 16px;
  }

  .minecraft-server-page__summary {
    grid-template-columns: 1fr;
  }

  .minecraft-server-page__summary-icon-wrap {
    justify-content: flex-start;
  }

  .minecraft-server-page__record-row {
    align-items: stretch;
  }

  .minecraft-server-page__description-box {
    grid-template-columns: 1fr;
  }

  .minecraft-server-page__description-icon-wrap {
    justify-content: flex-start;
  }
}
</style>
