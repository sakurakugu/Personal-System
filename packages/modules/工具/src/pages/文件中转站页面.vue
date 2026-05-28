<script setup lang="ts">
import {
  Connection,
  CopyDocument,
  Delete,
  Download,
  RefreshRight,
  Upload,
} from '@element-plus/icons-vue'
import { 解析当前API基地址 } from '@personal-system/api'
import { ElButton, ElCard, ElEmpty, ElInput, ElMessage, ElProgress, ElTag } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

type 设备连接状态 = 'connecting' | 'connected' | 'disconnected' | 'failed'
type 传输状态 = 'waiting' | 'sending' | 'receiving' | 'done' | 'error'

type 房间设备 = {
  id: string
  deviceName: string
  connectionState: 设备连接状态
}

type 文件传输记录 = {
  id: string
  direction: 'incoming' | 'outgoing'
  peerId: string
  peerName: string
  fileName: string
  fileSize: number
  mimeType: string
  transferredSize: number
  progress: number
  status: 传输状态
  chunks?: ArrayBuffer[]
  downloadUrl?: string
  errorMessage?: string
}

type 服务端消息 =
  | { type: 'joined'; peerId: string; roomId: string; peers: Array<{ id: string; deviceName: string }> }
  | { type: 'peer-joined'; peer: { id: string; deviceName: string } }
  | { type: 'peer-left'; peerId: string }
  | { type: 'signal'; from: string; signal: WebRTC信令载荷 }
  | { type: 'signal-error'; message: string; to: string }
  | { type: 'error'; message: string }
  | { type: 'pong' }

type WebRTC信令载荷 =
  | { type: 'offer'; description: RTCSessionDescriptionInit }
  | { type: 'answer'; description: RTCSessionDescriptionInit }
  | { type: 'ice-candidate'; candidate: RTCIceCandidateInit }

type 文件元信息消息 = {
  type: 'file-meta'
  transferId: string
  fileName: string
  fileSize: number
  mimeType: string
}

type 文件完成消息 = {
  type: 'file-complete'
  transferId: string
}

const route = useRoute()
const router = useRouter()

const 分片大小 = 16 * 1024
const 最大发送缓冲字节数 = 2 * 1024 * 1024
const 房间ID正则 = /^[a-zA-Z0-9_-]{4,32}$/
const 设备名称存储键 = 'file_transfer_device_name'

const 房间ID = ref(读取初始房间ID())
const 设备名称 = ref(读取初始设备名称())
const 自身设备ID = ref('')
const 已连接 = ref(false)
const 正在连接 = ref(false)
const 设备列表 = ref<房间设备[]>([])
const 选中设备ID = ref('')
const 待发送文件列表 = ref<File[]>([])
const 传输记录列表 = ref<文件传输记录[]>([])
const 数据通道状态版本 = ref(0)

let socket: WebSocket | null = null
let heartbeatTimer: number | null = null

const peerConnections = new Map<string, RTCPeerConnection>()
const dataChannels = new Map<string, RTCDataChannel>()
const incomingTransfers = new Map<string, 文件传输记录>()

const 选中设备 = computed(() => 设备列表.value.find((item) => item.id === 选中设备ID.value) ?? null)
const 可发送文件 = computed(() => {
  const channelStateTick = 数据通道状态版本.value
  const channel = 选中设备ID.value ? dataChannels.get(选中设备ID.value) : null
  return Boolean(channelStateTick >= 0 && channel && channel.readyState === 'open' && 待发送文件列表.value.length)
})
const 房间链接 = computed(() => {
  if (typeof window === 'undefined') {
    return ''
  }
  const url = new URL(window.location.href)
  url.pathname = '/tools/transfer'
  url.search = ''
  url.searchParams.set('room', 房间ID.value)
  return url.toString()
})

function 读取初始房间ID() {
  const queryRoom = Array.isArray(route.query.room) ? route.query.room[0] : route.query.room
  if (queryRoom && 房间ID正则.test(queryRoom)) {
    return queryRoom
  }
  return 生成房间ID()
}

function 读取初始设备名称() {
  if (typeof localStorage !== 'undefined') {
    const cachedName = localStorage.getItem(设备名称存储键)
    if (cachedName) {
      return cachedName
    }
  }
  if (typeof navigator !== 'undefined') {
    const platform = navigator.platform || navigator.userAgent
    if (platform) {
      return `${platform} 设备`
    }
  }
  return '我的设备'
}

function 生成房间ID() {
  const source = crypto.getRandomValues(new Uint8Array(6))
  return Array.from(source, (item) => (item % 36).toString(36)).join('').toUpperCase()
}

function 生成记录ID() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function 规范化房间ID(value: string) {
  return value.trim().replace(/\s+/g, '').slice(0, 32)
}

function 格式化文件大小(size: number) {
  if (size < 1024) {
    return `${size} B`
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`
  }
  if (size < 1024 * 1024 * 1024) {
    return `${(size / 1024 / 1024).toFixed(1)} MB`
  }
  return `${(size / 1024 / 1024 / 1024).toFixed(2)} GB`
}

function 获取WebSocket地址() {
  const apiBase = 解析当前API基地址()
  const url = new URL(apiBase, window.location.origin)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.pathname = `${url.pathname.replace(/\/+$/, '')}/file-transfer/ws`
  url.search = ''
  return url.toString()
}

function 发送WebSocket消息(payload: Record<string, unknown>) {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(payload))
  }
}

async function 复制房间链接() {
  await navigator.clipboard.writeText(房间链接.value)
  ElMessage.success('房间链接已复制')
}

function 刷新房间ID() {
  房间ID.value = 生成房间ID()
  void router.replace({ path: route.path, query: { ...route.query, room: 房间ID.value } })
}

function 更新房间ID(value: string) {
  房间ID.value = 规范化房间ID(value)
}

async function 连接房间() {
  const normalizedRoomId = 规范化房间ID(房间ID.value)
  if (!房间ID正则.test(normalizedRoomId)) {
    ElMessage.warning('房间码需要 4 到 32 位字母、数字、下划线或短横线')
    return
  }
  const normalizedDeviceName = 设备名称.value.trim().slice(0, 48)
  if (!normalizedDeviceName) {
    ElMessage.warning('请填写设备名称')
    return
  }

  断开连接()
  房间ID.value = normalizedRoomId
  设备名称.value = normalizedDeviceName
  localStorage.setItem(设备名称存储键, normalizedDeviceName)
  await router.replace({ path: route.path, query: { ...route.query, room: normalizedRoomId } })

  正在连接.value = true
  socket = new WebSocket(获取WebSocket地址())
  socket.addEventListener('open', () => {
    发送WebSocket消息({
      type: 'join',
      roomId: normalizedRoomId,
      deviceName: normalizedDeviceName,
    })
    heartbeatTimer = window.setInterval(() => 发送WebSocket消息({ type: 'ping' }), 25_000)
  })
  socket.addEventListener('message', (event) => {
    void 处理服务端消息(event.data)
  })
  socket.addEventListener('close', () => {
    正在连接.value = false
    已连接.value = false
    清理连接资源()
  })
  socket.addEventListener('error', () => {
    正在连接.value = false
    ElMessage.error('文件中转信令连接失败')
  })
}

function 断开连接() {
  if (heartbeatTimer !== null) {
    window.clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
  socket?.close()
  socket = null
  已连接.value = false
  正在连接.value = false
  自身设备ID.value = ''
  清理连接资源()
}

function 清理连接资源() {
  peerConnections.forEach((connection) => connection.close())
  peerConnections.clear()
  dataChannels.forEach((channel) => channel.close())
  dataChannels.clear()
  刷新数据通道状态()
  incomingTransfers.clear()
  设备列表.value = []
  选中设备ID.value = ''
}

async function 处理服务端消息(rawData: unknown) {
  if (typeof rawData !== 'string') {
    return
  }
  const message = JSON.parse(rawData) as 服务端消息
  if (message.type === 'joined') {
    自身设备ID.value = message.peerId
    设备列表.value = message.peers.map((peer) => ({
      ...peer,
      connectionState: 'connecting',
    }))
    选中设备ID.value = 设备列表.value[0]?.id ?? ''
    已连接.value = true
    正在连接.value = false
    console.debug('[file-transfer] 已加入房间', {
      roomId: message.roomId,
      peerCount: message.peers.length,
    })
    return
  }
  if (message.type === 'peer-joined') {
    添加或更新设备(message.peer.id, message.peer.deviceName, 'connecting')
    选中设备ID.value ||= message.peer.id
    await 确保对等连接(message.peer.id, true)
    return
  }
  if (message.type === 'peer-left') {
    移除设备(message.peerId)
    return
  }
  if (message.type === 'signal') {
    await 处理WebRTC信令(message.from, message.signal)
    return
  }
  if (message.type === 'signal-error' || message.type === 'error') {
    ElMessage.warning(message.message)
  }
}

function 添加或更新设备(peerId: string, deviceName: string, state?: 设备连接状态) {
  const existing = 设备列表.value.find((item) => item.id === peerId)
  if (existing) {
    existing.deviceName = deviceName
    if (state) {
      existing.connectionState = state
    }
    return
  }
  设备列表.value.push({
    id: peerId,
    deviceName,
    connectionState: state ?? 'connecting',
  })
}

function 更新设备状态(peerId: string, state: 设备连接状态) {
  const peer = 设备列表.value.find((item) => item.id === peerId)
  if (peer) {
    peer.connectionState = state
  }
}

function 移除设备(peerId: string) {
  peerConnections.get(peerId)?.close()
  peerConnections.delete(peerId)
  dataChannels.get(peerId)?.close()
  dataChannels.delete(peerId)
  刷新数据通道状态()
  incomingTransfers.delete(peerId)
  设备列表.value = 设备列表.value.filter((item) => item.id !== peerId)
  if (选中设备ID.value === peerId) {
    选中设备ID.value = 设备列表.value[0]?.id ?? ''
  }
}

async function 确保对等连接(peerId: string, createOffer: boolean) {
  const existing = peerConnections.get(peerId)
  if (existing) {
    return existing
  }

  const connection = new RTCPeerConnection({
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
  })
  peerConnections.set(peerId, connection)

  connection.addEventListener('icecandidate', (event) => {
    if (event.candidate) {
      发送WebSocket消息({
        type: 'signal',
        to: peerId,
        signal: {
          type: 'ice-candidate',
          candidate: event.candidate.toJSON(),
        },
      })
    }
  })
  connection.addEventListener('connectionstatechange', () => {
    const state = connection.connectionState
    if (state === 'connected') {
      更新设备状态(peerId, 'connected')
    } else if (state === 'failed') {
      更新设备状态(peerId, 'failed')
    } else if (state === 'disconnected' || state === 'closed') {
      更新设备状态(peerId, 'disconnected')
    } else {
      更新设备状态(peerId, 'connecting')
    }
  })
  connection.addEventListener('datachannel', (event) => {
    绑定数据通道(peerId, event.channel)
  })

  if (createOffer) {
    const channel = connection.createDataChannel('file-transfer', { ordered: true })
    绑定数据通道(peerId, channel)
    const offer = await connection.createOffer()
    await connection.setLocalDescription(offer)
    发送WebSocket消息({
      type: 'signal',
      to: peerId,
      signal: {
        type: 'offer',
        description: offer,
      },
    })
  }

  return connection
}

function 绑定数据通道(peerId: string, channel: RTCDataChannel) {
  dataChannels.set(peerId, channel)
  刷新数据通道状态()
  channel.binaryType = 'arraybuffer'
  channel.addEventListener('open', () => {
    更新设备状态(peerId, 'connected')
    刷新数据通道状态()
    console.debug('[file-transfer] 数据通道已打开', { peerId })
  })
  channel.addEventListener('close', () => {
    更新设备状态(peerId, 'disconnected')
    刷新数据通道状态()
  })
  channel.addEventListener('error', () => {
    更新设备状态(peerId, 'failed')
    刷新数据通道状态()
  })
  channel.addEventListener('message', (event) => {
    void 处理数据通道消息(peerId, event.data)
  })
}

function 刷新数据通道状态() {
  数据通道状态版本.value += 1
}

async function 处理WebRTC信令(peerId: string, signal: WebRTC信令载荷) {
  const connection = await 确保对等连接(peerId, false)
  if (signal.type === 'offer') {
    await connection.setRemoteDescription(signal.description)
    const answer = await connection.createAnswer()
    await connection.setLocalDescription(answer)
    发送WebSocket消息({
      type: 'signal',
      to: peerId,
      signal: {
        type: 'answer',
        description: answer,
      },
    })
    return
  }
  if (signal.type === 'answer') {
    await connection.setRemoteDescription(signal.description)
    return
  }
  if (signal.type === 'ice-candidate') {
    await connection.addIceCandidate(signal.candidate)
  }
}

async function 处理数据通道消息(peerId: string, rawData: unknown) {
  if (typeof rawData === 'string') {
    处理数据通道文本消息(peerId, JSON.parse(rawData) as 文件元信息消息 | 文件完成消息)
    return
  }
  const transfer = incomingTransfers.get(peerId)
  if (!transfer) {
    return
  }
  const chunk = rawData instanceof ArrayBuffer
    ? rawData
    : await (rawData as Blob).arrayBuffer()
  transfer.chunks?.push(chunk)
  transfer.transferredSize += chunk.byteLength
  transfer.progress = Math.min(100, Math.round((transfer.transferredSize / transfer.fileSize) * 100))
  刷新传输记录(transfer)
}

function 处理数据通道文本消息(peerId: string, message: 文件元信息消息 | 文件完成消息) {
  if (message.type === 'file-meta') {
    const peer = 设备列表.value.find((item) => item.id === peerId)
    const transfer = reactive<文件传输记录>({
      id: message.transferId,
      direction: 'incoming',
      peerId,
      peerName: peer?.deviceName ?? '未知设备',
      fileName: message.fileName,
      fileSize: message.fileSize,
      mimeType: message.mimeType,
      transferredSize: 0,
      progress: 0,
      status: 'receiving',
      chunks: [],
    })
    incomingTransfers.set(peerId, transfer)
    传输记录列表.value.unshift(transfer)
    return
  }
  if (message.type === 'file-complete') {
    const transfer = incomingTransfers.get(peerId)
    if (!transfer || transfer.id !== message.transferId) {
      return
    }
    const blob = new Blob(transfer.chunks ?? [], {
      type: transfer.mimeType || 'application/octet-stream',
    })
    transfer.downloadUrl = URL.createObjectURL(blob)
    transfer.transferredSize = transfer.fileSize
    transfer.progress = 100
    transfer.status = 'done'
    transfer.chunks = []
    incomingTransfers.delete(peerId)
    刷新传输记录(transfer)
  }
}

function 选择文件(event: Event) {
  const input = event.target as HTMLInputElement
  待发送文件列表.value = Array.from(input.files ?? [])
}

function 移除待发送文件(index: number) {
  待发送文件列表.value.splice(index, 1)
}

async function 发送文件列表() {
  if (!选中设备.value) {
    ElMessage.warning('请选择目标设备')
    return
  }
  const channel = dataChannels.get(选中设备.value.id)
  if (!channel || channel.readyState !== 'open') {
    ElMessage.warning('目标设备尚未建立直传通道')
    return
  }
  const files = [...待发送文件列表.value]
  for (const file of files) {
    await 发送单个文件(channel, 选中设备.value, file)
  }
  待发送文件列表.value = []
}

async function 发送单个文件(channel: RTCDataChannel, peer: 房间设备, file: File) {
  const transferId = 生成记录ID()
  const record = reactive<文件传输记录>({
    id: transferId,
    direction: 'outgoing',
    peerId: peer.id,
    peerName: peer.deviceName,
    fileName: file.name,
    fileSize: file.size,
    mimeType: file.type,
    transferredSize: 0,
    progress: 0,
    status: 'sending',
  })
  传输记录列表.value.unshift(record)

  try {
    channel.send(JSON.stringify({
      type: 'file-meta',
      transferId,
      fileName: file.name,
      fileSize: file.size,
      mimeType: file.type,
    } satisfies 文件元信息消息))

    let offset = 0
    while (offset < file.size) {
      await 等待发送缓冲(channel)
      const chunk = await file.slice(offset, offset + 分片大小).arrayBuffer()
      channel.send(chunk)
      offset += chunk.byteLength
      record.transferredSize = offset
      record.progress = Math.min(100, Math.round((offset / file.size) * 100))
      刷新传输记录(record)
    }

    channel.send(JSON.stringify({
      type: 'file-complete',
      transferId,
    } satisfies 文件完成消息))
    record.status = 'done'
    record.progress = 100
    刷新传输记录(record)
  } catch (error) {
    record.status = 'error'
    record.errorMessage = error instanceof Error ? error.message : '发送失败'
    刷新传输记录(record)
  }
}

function 刷新传输记录(record: 文件传输记录) {
  const index = 传输记录列表.value.findIndex((item) => item.id === record.id)
  if (index !== -1) {
    传输记录列表.value[index] = { ...record }
  }
}

async function 等待发送缓冲(channel: RTCDataChannel) {
  while (channel.bufferedAmount > 最大发送缓冲字节数) {
    await new Promise((resolve) => window.setTimeout(resolve, 40))
  }
}

function 清空记录() {
  for (const record of 传输记录列表.value) {
    if (record.downloadUrl) {
      URL.revokeObjectURL(record.downloadUrl)
    }
  }
  传输记录列表.value = []
}

function 状态文案(status: 传输状态) {
  const map: Record<传输状态, string> = {
    waiting: '等待',
    sending: '发送中',
    receiving: '接收中',
    done: '完成',
    error: '失败',
  }
  return map[status]
}

function 设备状态文案(status: 设备连接状态) {
  const map: Record<设备连接状态, string> = {
    connecting: '连接中',
    connected: '已连接',
    disconnected: '已断开',
    failed: '连接失败',
  }
  return map[status]
}

onMounted(() => {
  if (route.query.room) {
    void 连接房间()
  }
})

onBeforeUnmount(() => {
  清空记录()
  断开连接()
})
</script>

<template>
  <div class="transfer-page">
    <section class="transfer-shell">
      <ElCard class="transfer-panel transfer-panel--setup" shadow="never">
        <template #header>
          <div class="panel-header">
            <div>
              <span class="panel-kicker">文件中转站</span>
              <h1>房间直传</h1>
            </div>
            <ElTag :type="已连接 ? 'success' : 'info'" effect="plain">
              {{ 已连接 ? '已连接' : '未连接' }}
            </ElTag>
          </div>
        </template>

        <div class="setup-grid">
          <label class="field-block">
            <span>房间码</span>
            <ElInput
              :model-value="房间ID"
              maxlength="32"
              @update:model-value="更新房间ID"
            >
              <template #append>
                <ElButton :icon="RefreshRight" title="刷新房间码" @click="刷新房间ID" />
              </template>
            </ElInput>
          </label>

          <label class="field-block">
            <span>设备名称</span>
            <ElInput v-model="设备名称" maxlength="48" />
          </label>
        </div>

        <div class="setup-actions">
          <ElButton
            type="primary"
            :icon="Connection"
            :loading="正在连接"
            @click="连接房间"
          >
            {{ 已连接 ? '重新连接' : '连接房间' }}
          </ElButton>
          <ElButton :icon="CopyDocument" :disabled="!房间ID" @click="复制房间链接">
            复制链接
          </ElButton>
          <ElButton v-if="已连接" @click="断开连接">断开</ElButton>
        </div>
      </ElCard>

      <ElCard class="transfer-panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <div>
              <span class="panel-kicker">在线设备</span>
              <h2>{{ 设备列表.length }} 台</h2>
            </div>
          </div>
        </template>

        <div v-if="设备列表.length" class="peer-list">
          <button
            v-for="peer in 设备列表"
            :key="peer.id"
            type="button"
            class="peer-item"
            :class="{ 'is-active': 选中设备ID === peer.id }"
            @click="选中设备ID = peer.id"
          >
            <span class="peer-item__name">{{ peer.deviceName }}</span>
            <ElTag size="small" :type="peer.connectionState === 'connected' ? 'success' : 'info'">
              {{ 设备状态文案(peer.connectionState) }}
            </ElTag>
          </button>
        </div>
        <ElEmpty v-else description="当前房间没有其他设备" />
      </ElCard>
    </section>

    <section class="transfer-workbench">
      <ElCard class="transfer-panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <div>
              <span class="panel-kicker">发送</span>
              <h2>{{ 选中设备?.deviceName ?? '未选择设备' }}</h2>
            </div>
            <ElButton
              type="primary"
              :icon="Upload"
              :disabled="!可发送文件"
              @click="发送文件列表"
            >
              发送文件
            </ElButton>
          </div>
        </template>

        <label class="file-drop">
          <input multiple type="file" @change="选择文件">
          <Upload class="file-drop__icon" />
          <span>选择文件</span>
        </label>

        <div v-if="待发送文件列表.length" class="pending-list">
          <div
            v-for="(file, index) in 待发送文件列表"
            :key="`${file.name}-${file.lastModified}-${index}`"
            class="pending-item"
          >
            <div class="pending-item__body">
              <strong>{{ file.name }}</strong>
              <span>{{ 格式化文件大小(file.size) }}</span>
            </div>
            <ElButton :icon="Delete" text title="移除" @click="移除待发送文件(index)" />
          </div>
        </div>
      </ElCard>

      <ElCard class="transfer-panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <div>
              <span class="panel-kicker">传输记录</span>
              <h2>{{ 传输记录列表.length }} 条</h2>
            </div>
            <ElButton :icon="Delete" :disabled="!传输记录列表.length" @click="清空记录">
              清空
            </ElButton>
          </div>
        </template>

        <div v-if="传输记录列表.length" class="transfer-list">
          <article
            v-for="record in 传输记录列表"
            :key="record.id"
            class="transfer-item"
          >
            <div class="transfer-item__header">
              <div class="transfer-item__title">
                <strong>{{ record.fileName }}</strong>
                <span>{{ record.direction === 'incoming' ? '来自' : '发往' }} {{ record.peerName }}</span>
              </div>
              <ElTag
                size="small"
                :type="record.status === 'done' ? 'success' : record.status === 'error' ? 'danger' : 'info'"
              >
                {{ 状态文案(record.status) }}
              </ElTag>
            </div>
            <ElProgress :percentage="record.progress" :stroke-width="8" />
            <div class="transfer-item__footer">
              <span>{{ 格式化文件大小(record.transferredSize) }} / {{ 格式化文件大小(record.fileSize) }}</span>
              <a
                v-if="record.downloadUrl"
                class="download-link"
                :href="record.downloadUrl"
                :download="record.fileName"
              >
                <Download />
                下载
              </a>
              <span v-else-if="record.errorMessage" class="error-text">{{ record.errorMessage }}</span>
            </div>
          </article>
        </div>
        <ElEmpty v-else description="暂无传输记录" />
      </ElCard>
    </section>
  </div>
</template>

<style scoped>
.transfer-page {
  min-height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
  padding: 18px;
  background:
    linear-gradient(180deg, rgba(248, 250, 252, 0.96), rgba(241, 245, 249, 0.96)),
    radial-gradient(circle at top left, rgb(var(--el-color-primary-rgb) / 0.1), transparent 30%);
}

.transfer-shell,
.transfer-workbench {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
  gap: 14px;
}

.transfer-workbench {
  margin-top: 14px;
  grid-template-columns: minmax(320px, 0.9fr) minmax(0, 1.1fr);
}

.transfer-panel {
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
}

.transfer-panel :deep(.el-card__header) {
  padding: 16px 18px;
}

.transfer-panel :deep(.el-card__body) {
  padding: 18px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.panel-kicker {
  display: block;
  margin-bottom: 4px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-weight: 700;
}

.panel-header h1,
.panel-header h2 {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 22px;
  line-height: 1.2;
}

.setup-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 14px;
}

.field-block {
  display: grid;
  gap: 8px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  font-weight: 700;
}

.setup-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.peer-list {
  display: grid;
  gap: 10px;
}

.peer-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 52px;
  padding: 0 14px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.peer-item:hover,
.peer-item.is-active {
  border-color: rgb(var(--el-color-primary-rgb) / 0.42);
  background: rgb(var(--el-color-primary-rgb) / 0.08);
}

.peer-item__name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 700;
}

.file-drop {
  display: grid;
  place-items: center;
  gap: 10px;
  min-height: 150px;
  border: 1px dashed rgba(100, 116, 139, 0.5);
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.8);
  color: var(--el-text-color-regular);
  cursor: pointer;
}

.file-drop input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.file-drop__icon {
  width: 34px;
  height: 34px;
  color: var(--el-color-primary);
}

.pending-list,
.transfer-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.pending-item,
.transfer-item {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-fill-color-blank);
}

.pending-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
}

.pending-item__body,
.transfer-item__title {
  display: grid;
  min-width: 0;
  gap: 4px;
}

.pending-item strong,
.transfer-item strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-primary);
}

.pending-item span,
.transfer-item span {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.transfer-item {
  display: grid;
  gap: 10px;
  padding: 12px;
}

.transfer-item__header,
.transfer-item__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.download-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--el-color-primary);
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
}

.download-link svg {
  width: 15px;
  height: 15px;
}

.error-text {
  color: var(--el-color-danger);
}

.dark .transfer-page {
  background:
    linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(17, 24, 39, 0.96)),
    radial-gradient(circle at top left, color-mix(in srgb, var(--el-color-primary-light-5) 12%, transparent), transparent 30%);
}

.dark .transfer-panel,
.dark .pending-item,
.dark .transfer-item,
.dark .peer-item {
  border-color: rgba(148, 163, 184, 0.2);
  background: rgba(17, 24, 39, 0.78);
}

.dark .file-drop {
  border-color: rgba(148, 163, 184, 0.34);
  background: rgba(15, 23, 42, 0.68);
}

@media (max-width: 1080px) {
  .transfer-shell,
  .transfer-workbench,
  .setup-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .transfer-page {
    padding: 14px;
  }

  .panel-header,
  .transfer-item__header,
  .transfer-item__footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .setup-actions {
    display: grid;
  }
}
</style>
