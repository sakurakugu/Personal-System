<script setup lang="ts">
import { Connection, CopyDocument, DataAnalysis, Monitor, Plus, Position, RefreshRight } from '@element-plus/icons-vue'
import { ElAlert, ElButton, ElCard, ElDescriptions, ElDescriptionsItem, ElForm, ElFormItem, ElInput, ElMessage, ElOption, ElSelect, ElSpace, ElTag } from 'element-plus'
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { WebviewWindow } from '@tauri-apps/api/webviewWindow'
import { 查询我的世界服务器, type 我的世界服务器查询结果, type 我的世界服务器版本 } from '@/shared/minecraft-server'
import { isTauri } from '@tauri-apps/api/core'
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
const 结果 = ref<我的世界服务器查询结果 | null>(null)
const 当前状态 = ref('等待输入服务器地址。')

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

const 玩家概览 = computed(() => {
  if (!结果.value) {
    return '-'
  }
  const online = 结果.value.playersOnline
  const max = 结果.value.playersMax
  if (online == null && max == null) {
    return '-'
  }
  return `${online ?? '-'} / ${max ?? '-'}`
})

const 是否可打开独立窗口 = computed(() => isTauri())
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

let 扰动计时器: number | null = null
const 扰动种子 = ref(0)

启动扰动计时器()
onBeforeUnmount(() => {
  停止扰动计时器()
})

初始化路由参数()

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

function 填充示例地址(address: string, edition: 我的世界服务器版本) {
  表单.address = address
  表单.edition = edition
}

function 重置() {
  表单.address = ''
  表单.edition = 'auto'
  表单.timeout = 3
  错误信息.value = ''
  结果.value = null
  当前状态.value = '已重置。'
}

async function 打开独立窗口() {
  if (!是否可打开独立窗口.value) {
    return
  }
  const label = `minecraft-tool-${Date.now()}`
  const url = `/tools/minecraft-server${表单.address.trim() ? `?address=${encodeURIComponent(表单.address.trim())}&edition=${encodeURIComponent(表单.edition)}` : ''}`
  const window = new WebviewWindow(label, {
    title: '我的世界服务器查询',
    url,
    width: 1080,
    height: 780,
    minWidth: 860,
    minHeight: 620,
    center: true,
    focus: true,
  })

  void window.once('tauri://error', (event) => {
    错误信息.value = `打开独立窗口失败：${String(event.payload)}`
  })
}

async function 复制描述纯文本() {
  try {
    await navigator.clipboard.writeText(描述纯文本.value)
    ElMessage.success('描述纯文本已复制')
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
    <section class="minecraft-server-page__hero">
      <div>
        <span class="minecraft-server-page__eyebrow">桌面工具</span>
        <h1>我的世界服务器查询</h1>
        <p>
          输入服务器地址后直接查看在线状态、延迟、版本与玩家数。这个页面适合嵌入主应用使用，也支持新开独立窗口。
        </p>
      </div>
      <ElSpace wrap>
        <ElButton plain @click="填充示例地址('play.hypixel.net', 'java')">
          Java 示例
        </ElButton>
        <ElButton plain @click="填充示例地址('mco.mineplex.com:19132', 'bedrock')">
          Bedrock 示例
        </ElButton>
        <ElButton :disabled="!是否可打开独立窗口" @click="打开独立窗口">
          <template #icon><Plus /></template>
          独立窗口打开
        </ElButton>
      </ElSpace>
    </section>

    <ElAlert
      v-if="错误信息"
      class="minecraft-server-page__alert"
      type="error"
      :title="错误信息"
      show-icon
      :closable="false"
    />

    <div class="minecraft-server-page__layout">
      <ElCard class="minecraft-server-page__panel" shadow="never">
        <template #header>
          <div class="minecraft-server-page__panel-header">
            <span class="minecraft-server-page__panel-title">
              <Connection />
              查询配置
            </span>
            <ElTag effect="plain">{{ 当前状态 }}</ElTag>
          </div>
        </template>

        <ElForm label-position="top" class="minecraft-server-page__form">
          <ElFormItem label="服务器地址">
            <ElInput
              v-model="表单.address"
              placeholder="例如 play.example.com 或 play.example.com:25565"
              clearable
              @keyup.enter="执行查询"
            />
          </ElFormItem>

          <div class="minecraft-server-page__grid">
            <ElFormItem label="协议">
              <ElSelect v-model="表单.edition">
                <ElOption
                  v-for="item in 协议选项"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </ElSelect>
              <p class="minecraft-server-page__field-tip">
                {{ 协议选项.find((item) => item.value === 表单.edition)?.description }}
              </p>
            </ElFormItem>

            <ElFormItem label="超时（秒）">
              <ElInput v-model.number="表单.timeout" type="number" min="1" max="15" step="0.5" />
            </ElFormItem>
          </div>

          <div class="minecraft-server-page__actions">
            <ElButton type="primary" :loading="查询中" :disabled="!表单.address.trim()" @click="执行查询">
              <template #icon><RefreshRight /></template>
              开始查询
            </ElButton>
            <ElButton :disabled="查询中" @click="重置">重置</ElButton>
          </div>
        </ElForm>
      </ElCard>

      <ElCard class="minecraft-server-page__panel" shadow="never">
        <template #header>
          <div class="minecraft-server-page__panel-header">
            <span class="minecraft-server-page__panel-title">
              <DataAnalysis />
              查询结果
            </span>
            <ElTag :type="结果?.online ? 'success' : 'info'" effect="plain">
              {{ 结果 ? (结果.online ? '在线' : '离线') : '未查询' }}
            </ElTag>
          </div>
        </template>

        <div v-if="!结果" class="minecraft-server-page__empty">
          还没有查询结果，请先输入服务器地址。
        </div>

        <template v-else>
          <div class="minecraft-server-page__summary">
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

          <ElDescriptions :column="2" border>
            <ElDescriptionsItem label="地址">{{ 结果.requestedAddress }}</ElDescriptionsItem>
            <ElDescriptionsItem label="主机">{{ 结果.host }}</ElDescriptionsItem>
            <ElDescriptionsItem label="状态">
              <ElTag :type="结果.online ? 'success' : 'danger'" effect="plain">
                {{ 结果.online ? '在线' : '离线' }}
              </ElTag>
            </ElDescriptionsItem>
            <ElDescriptionsItem label="协议">{{ 结果.resolvedEdition || '-' }}</ElDescriptionsItem>
            <ElDescriptionsItem label="端口">{{ 结果.resolvedPort ?? 结果.requestedPort ?? '-' }}</ElDescriptionsItem>
            <ElDescriptionsItem label="延迟">{{ 结果.latencyMs != null ? `${结果.latencyMs} ms` : '-' }}</ElDescriptionsItem>
            <ElDescriptionsItem label="版本">{{ 结果.versionName || '-' }}</ElDescriptionsItem>
            <ElDescriptionsItem label="协议版本">{{ 结果.protocolVersion ?? '-' }}</ElDescriptionsItem>
            <ElDescriptionsItem label="玩家数">{{ 玩家概览 }}</ElDescriptionsItem>
            <ElDescriptionsItem label="品牌">{{ 结果.brand || '-' }}</ElDescriptionsItem>
            <ElDescriptionsItem label="地图">{{ 结果.mapName || '-' }}</ElDescriptionsItem>
            <ElDescriptionsItem label="模式">{{ 结果.gameMode || '-' }}</ElDescriptionsItem>
          </ElDescriptions>

          <div class="minecraft-server-page__detail-grid">
            <section class="minecraft-server-page__detail-card">
              <div class="minecraft-server-page__detail-title minecraft-server-page__detail-title--with-action">
                <span class="minecraft-server-page__detail-title-label">
                  <Monitor />
                  服务器描述
                </span>
                <ElButton text @click="复制描述纯文本">
                  <template #icon><CopyDocument /></template>
                  复制纯文本
                </ElButton>
              </div>
              <div class="minecraft-server-page__detail-text">
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
            </section>

            <section class="minecraft-server-page__detail-card">
              <div class="minecraft-server-page__detail-title">
                <Position />
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
          </div>
        </template>
      </ElCard>
    </div>
  </div>
</template>

<style scoped>
.minecraft-server-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 100%;
  padding: 18px;
  box-sizing: border-box;
  background:
    radial-gradient(circle at top left, rgb(var(--el-color-primary-rgb) / 0.1), transparent 28%),
    linear-gradient(180deg, #f6faf8 0%, #eef4f1 100%);
}

.minecraft-server-page__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 24px 28px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.14);
  border-radius: 24px;
  background:
    linear-gradient(140deg, rgb(var(--el-color-primary-rgb) / 0.12), rgb(var(--el-color-primary-rgb) / 0.03)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(255, 255, 255, 0.99));
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.minecraft-server-page__eyebrow {
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

.minecraft-server-page__hero h1 {
  margin: 16px 0 10px;
  font-size: 34px;
  line-height: 1.15;
  color: #102418;
}

.minecraft-server-page__hero p {
  margin: 0;
  max-width: 760px;
  color: var(--el-text-color-secondary);
  line-height: 1.9;
}

.minecraft-server-page__alert {
  flex-shrink: 0;
}

.minecraft-server-page__layout {
  display: grid;
  grid-template-columns: minmax(340px, 420px) minmax(0, 1fr);
  gap: 16px;
  min-height: 0;
}

.minecraft-server-page__panel {
  border-radius: 24px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.12);
  background:
    linear-gradient(160deg, rgba(255, 255, 255, 0.97), rgba(247, 251, 248, 0.98)),
    linear-gradient(135deg, rgb(var(--el-color-primary-rgb) / 0.06), transparent 50%);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.05);
}

.minecraft-server-page__panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.minecraft-server-page__panel-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: #102418;
}

.minecraft-server-page__form {
  display: grid;
  gap: 8px;
}

.minecraft-server-page__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.minecraft-server-page__field-tip {
  margin: 8px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.6;
}

.minecraft-server-page__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 4px;
}

.minecraft-server-page__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 280px;
  color: var(--el-text-color-secondary);
}

.minecraft-server-page__summary {
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr);
  gap: 14px;
  align-items: center;
  margin-bottom: 16px;
}

.minecraft-server-page__summary-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
}

.minecraft-server-page__summary-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  border: 1px solid #d6e3da;
  background: linear-gradient(180deg, #ffffff, #edf5ef);
  image-rendering: pixelated;
  object-fit: contain;
}

.minecraft-server-page__summary-icon--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 800;
  color: #1c5b36;
}

.minecraft-server-page__summary-main {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.minecraft-server-page__summary-title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.minecraft-server-page__summary-title-row strong {
  font-size: 20px;
  line-height: 1.2;
  color: #102418;
}

.minecraft-server-page__summary-subtitle {
  color: var(--el-text-color-secondary);
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.minecraft-server-page__detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.minecraft-server-page__detail-card {
  display: grid;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid #dce7df;
  border-radius: 18px;
  background: rgba(246, 251, 248, 0.78);
}

.minecraft-server-page__detail-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: #173322;
}

.minecraft-server-page__detail-title--with-action {
  justify-content: space-between;
}

.minecraft-server-page__detail-title-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.minecraft-server-page__detail-text {
  min-height: 72px;
  white-space: pre-wrap;
  line-height: 1.8;
  color: var(--el-text-color-regular);
  overflow-wrap: anywhere;
}

.minecraft-server-page__motd-line {
  min-height: 1.8em;
}

.minecraft-server-page__detail-text :deep(.is-obfuscated) {
  letter-spacing: 0.04em;
}

.dark .minecraft-server-page {
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--el-color-primary-light-5) 12%, transparent), transparent 28%),
    linear-gradient(180deg, #111916 0%, #0f1513 100%);
}

.dark .minecraft-server-page__hero,
.dark .minecraft-server-page__panel {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent);
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent), color-mix(in srgb, var(--el-color-primary-light-5) 5%, transparent)),
    rgba(18, 25, 22, 0.9);
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.24);
}

.dark .minecraft-server-page__hero h1,
.dark .minecraft-server-page__panel-title,
.dark .minecraft-server-page__detail-title,
.dark .minecraft-server-page__summary-title-row strong {
  color: #eef8f1;
}

.dark .minecraft-server-page__detail-card {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent);
  background: rgba(20, 30, 24, 0.76);
}

.dark .minecraft-server-page__summary-icon {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 18%, transparent);
  background: linear-gradient(180deg, rgba(22, 32, 26, 0.95), rgba(16, 24, 20, 0.92));
}

.dark .minecraft-server-page__summary-icon--empty {
  color: #82d6a1;
}

@media (max-width: 1100px) {
  .minecraft-server-page__layout,
  .minecraft-server-page__detail-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .minecraft-server-page {
    padding: 14px;
  }

  .minecraft-server-page__hero {
    flex-direction: column;
    padding: 18px;
  }

  .minecraft-server-page__hero h1 {
    font-size: 28px;
  }

  .minecraft-server-page__grid {
    grid-template-columns: 1fr;
  }
}
</style>
