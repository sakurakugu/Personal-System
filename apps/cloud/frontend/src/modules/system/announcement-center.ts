import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { fetchPublicAnnouncements } from './api'
import type { AnnouncementRecord } from './types'

const 已关闭公告存储键 = 'closedAnnouncements'
const 公告状态变更事件 = 'announcement-closed'
const 默认公告拉取数量 = 10

const announcements = ref<AnnouncementRecord[]>([])
const loading = ref(false)
const expandedMap = ref<Record<string, boolean>>({})
const closedIds = ref<string[]>(读取已关闭公告())

let 已完成拉取 = false
let 拉取任务: Promise<void> | null = null

function 读取已关闭公告(): string[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = JSON.parse(window.localStorage.getItem(已关闭公告存储键) || '[]')
    return Array.isArray(raw) ? raw.map(String) : []
  } catch {
    return []
  }
}

function 同步已关闭公告() {
  closedIds.value = 读取已关闭公告()
}

function 写入已关闭公告(ids: string[]) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(已关闭公告存储键, JSON.stringify(ids))
}

function 广播公告状态变更() {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(公告状态变更事件))
}

async function 拉取公告(force = false) {
  if (拉取任务) return 拉取任务
  if (已完成拉取 && !force) return

  loading.value = true
  拉取任务 = (async () => {
    try {
      announcements.value = await fetchPublicAnnouncements(默认公告拉取数量)
      已完成拉取 = true
    } catch {
      announcements.value = []
    } finally {
      loading.value = false
      拉取任务 = null
    }
  })()

  return 拉取任务
}

export function useAnnouncementCenter() {
  const visibleAnnouncements = computed(() => {
    return announcements.value.filter(item => !closedIds.value.includes(String(item.id)))
  })

  const hasUnreadAnnouncement = computed(() => visibleAnnouncements.value.length > 0)

  function toggleAnnouncement(id: string) {
    expandedMap.value[id] = !expandedMap.value[id]
  }

  function isExpanded(id: string) {
    return !!expandedMap.value[id]
  }

  function closeAnnouncement(id: string) {
    const normalizedId = String(id)
    if (closedIds.value.includes(normalizedId)) return
    const nextIds = [...closedIds.value, normalizedId]
    closedIds.value = nextIds
    写入已关闭公告(nextIds)
    广播公告状态变更()
  }

  function 处理存储变更(event: StorageEvent) {
    if (event.key === 已关闭公告存储键) {
      同步已关闭公告()
    }
  }

  function 处理公告状态变更() {
    同步已关闭公告()
  }

  onMounted(() => {
    同步已关闭公告()
    void 拉取公告()
    if (typeof window !== 'undefined') {
      window.addEventListener('storage', 处理存储变更)
      window.addEventListener(公告状态变更事件, 处理公告状态变更)
    }
  })

  onBeforeUnmount(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('storage', 处理存储变更)
      window.removeEventListener(公告状态变更事件, 处理公告状态变更)
    }
  })

  return {
    announcements,
    visibleAnnouncements,
    hasUnreadAnnouncement,
    loading,
    ensureAnnouncementsLoaded: 拉取公告,
    refreshAnnouncements: () => 拉取公告(true),
    toggleAnnouncement,
    isExpanded,
    closeAnnouncement,
  }
}
