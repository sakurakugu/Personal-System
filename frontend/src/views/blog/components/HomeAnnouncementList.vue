<script setup lang="ts">
import { ArrowDown, BellFilled, Close, Delete } from '@element-plus/icons-vue'
import { ElCard, ElIcon, ElSkeleton } from 'element-plus'
import { computed, onMounted, reactive } from 'vue'
import OverflowMarquee from '../../../components/OverflowMarquee.vue'
import { useAnnouncementCenter } from '../../../features/system/announcement-center'

const {
  visibleAnnouncements,
  loading,
  ensureAnnouncementsLoaded,
  toggleAnnouncement,
  isExpanded,
  closeAnnouncement,
} = useAnnouncementCenter()

const 首页公告 = computed(() => visibleAnnouncements.value.slice(0, 3))
const 公告滑动状态 = reactive<Record<string, {
  offset: number
  startX: number
  startY: number
  isDragging: boolean
  hasMoved: boolean
}>>({})
const 公告滑动阈值 = 72
const 公告最大偏移 = 104

type 公告滑动事件 = globalThis.TouchEvent | globalThis.MouseEvent

onMounted(() => {
  void ensureAnnouncementsLoaded()
})

function hasAnnouncementContent(content: string) {
  return content.trim().length > 0
}

function isSwipeDeleteEnabled(id: string, content: string) {
  return !hasAnnouncementContent(content) || isExpanded(id)
}

function initAnnouncementSwipeState(id: string) {
  if (!公告滑动状态[id]) {
    公告滑动状态[id] = {
      offset: 0,
      startX: 0,
      startY: 0,
      isDragging: false,
      hasMoved: false,
    }
  }
}

function getAnnouncementSwipePoint(event: 公告滑动事件) {
  if ('touches' in event) {
    const touch = event.touches[0]
    if (!touch) {
      return null
    }
    return {
      clientX: touch.clientX,
      clientY: touch.clientY,
    }
  }

  return {
    clientX: event.clientX,
    clientY: event.clientY,
  }
}

function onAnnouncementSwipeStart(event: 公告滑动事件, id: string, content: string) {
  if (!isSwipeDeleteEnabled(id, content)) return
  initAnnouncementSwipeState(id)
  const state = 公告滑动状态[id]
  const point = getAnnouncementSwipePoint(event)
  if (!point) return
  state.isDragging = true
  state.hasMoved = false
  state.startX = point.clientX
  state.startY = point.clientY
}

function onAnnouncementSwipeMove(event: 公告滑动事件, id: string, content: string) {
  if (!isSwipeDeleteEnabled(id, content)) return
  const state = 公告滑动状态[id]
  if (!state?.isDragging) return
  const point = getAnnouncementSwipePoint(event)
  if (!point) return

  const deltaX = point.clientX - state.startX
  const deltaY = point.clientY - state.startY

  if (Math.abs(deltaY) > Math.abs(deltaX)) return

  if (Math.abs(deltaX) > 5) {
    state.hasMoved = true
  }

  if ('touches' in event && Math.abs(deltaX) > 10) {
    event.preventDefault()
  }

  state.offset = Math.max(-公告最大偏移, Math.min(0, deltaX))
}

function onAnnouncementSwipeEnd(id: string, content: string) {
  if (!isSwipeDeleteEnabled(id, content)) return
  const state = 公告滑动状态[id]
  if (!state) return

  const hadMoved = state.hasMoved
  state.isDragging = false

  if (hadMoved) {
    setTimeout(() => {
      state.hasMoved = false
    }, 50)
  } else {
    state.hasMoved = false
  }

  if (state.offset < -公告滑动阈值) {
    state.offset = 0
    closeAnnouncement(id)
    return
  }

  state.offset = 0
}

function getAnnouncementCardStyle(id: string, content: string) {
  if (!isSwipeDeleteEnabled(id, content)) return {}
  const state = 公告滑动状态[id]
  if (!state) return {}

  return {
    transform: `translateX(${state.offset}px)`,
    transition: state.isDragging ? 'none' : 'transform 0.3s ease',
  }
}

function getAnnouncementDeleteActionStyle(id: string, content: string) {
  if (!isSwipeDeleteEnabled(id, content)) {
    return { opacity: 0 }
  }

  const state = 公告滑动状态[id]
  if (!state) {
    return { opacity: 0 }
  }

  const opacity = Math.min(1, Math.max(0, -state.offset / 公告滑动阈值))
  return {
    opacity,
    transform: `scale(${0.86 + opacity * 0.14})`,
  }
}

function handleAnnouncementHeaderClick(id: string, content: string) {
  if (!hasAnnouncementContent(content)) return
  if (公告滑动状态[id]?.hasMoved) return
  toggleAnnouncement(id)
}
</script>

<template>
  <section v-if="loading || 首页公告.length > 0" class="announcements-list">
    <ElSkeleton :loading="loading" animated :rows="2">
      <div
        v-for="item in 首页公告"
        :key="item.id"
        class="announcement-swipe-item"
        :class="{ 'is-swipeable': isSwipeDeleteEnabled(item.id, item.content) }"
        @touchstart.passive="onAnnouncementSwipeStart($event, item.id, item.content)"
        @touchmove="onAnnouncementSwipeMove($event, item.id, item.content)"
        @touchend="onAnnouncementSwipeEnd(item.id, item.content)"
        @touchcancel="onAnnouncementSwipeEnd(item.id, item.content)"
        @mousedown="onAnnouncementSwipeStart($event, item.id, item.content)"
        @mousemove="onAnnouncementSwipeMove($event, item.id, item.content)"
        @mouseup="onAnnouncementSwipeEnd(item.id, item.content)"
        @mouseleave="onAnnouncementSwipeEnd(item.id, item.content)"
      >
        <div
          v-if="isSwipeDeleteEnabled(item.id, item.content)"
          class="announcement-swipe-action announcement-swipe-action-delete"
          :style="getAnnouncementDeleteActionStyle(item.id, item.content)"
        >
          <ElIcon :size="18"><Delete /></ElIcon>
          <span class="announcement-swipe-text">删除</span>
        </div>

        <ElCard
          class="announcement-card"
          :class="{ 'is-swipeable': isSwipeDeleteEnabled(item.id, item.content) }"
          :style="getAnnouncementCardStyle(item.id, item.content)"
          shadow="hover"
        >
          <div
            class="announcement-header"
            :class="{ 'is-static': !hasAnnouncementContent(item.content) }"
            @click="handleAnnouncementHeaderClick(item.id, item.content)"
          >
            <div class="announcement-header-left">
              <ElIcon class="announcement-icon"><BellFilled /></ElIcon>
              <OverflowMarquee
                tag="span"
                class="announcement-title"
                :text="item.title"
              />
            </div>
            <div class="announcement-header-right">
              <span class="announcement-date">{{ new Date(item.created_at).toLocaleDateString() }}</span>
              <ElIcon
                v-if="hasAnnouncementContent(item.content)"
                class="expand-icon"
                :class="{ 'is-expanded': isExpanded(item.id) }"
              >
                <ArrowDown />
              </ElIcon>
              <div
                v-else
                class="announcement-close announcement-close-inline"
                @click.stop="closeAnnouncement(item.id)"
              >
                <ElIcon><Close /></ElIcon>
              </div>
            </div>
          </div>
          <div
            v-if="hasAnnouncementContent(item.content)"
            v-show="isExpanded(item.id)"
            class="announcement-content-wrapper"
          >
            <div class="announcement-content">
              {{ item.content }}
            </div>
            <div class="announcement-close" @click.stop="closeAnnouncement(item.id)">
              <ElIcon><Close /></ElIcon>
            </div>
          </div>
        </ElCard>
      </div>
    </ElSkeleton>
  </section>
</template>

<style scoped>
.announcements-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.announcement-swipe-item {
  position: relative;
}

.announcement-swipe-item.is-swipeable {
  touch-action: pan-y;
  user-select: none;
}

.announcement-swipe-action {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 96px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: #fff;
  border-radius: 12px;
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.announcement-swipe-action-delete {
  background: linear-gradient(270deg, #f56c6c 0%, #f89898 100%);
}

.announcement-swipe-text {
  font-size: 12px;
  white-space: nowrap;
}

.announcement-card {
  border-radius: 12px;
  background: linear-gradient(135deg, #fff9e6 0%, #fff5d6 100%);
  border: 1px solid #f0e0b0;
  transition: box-shadow 0.2s;
}

.dark .announcement-card {
  background: linear-gradient(135deg, #3d3020 0%, #2d2515 100%);
  border-color: #5a4a30;
}

.announcement-card:hover {
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.15);
}

.announcement-card.is-swipeable {
  position: relative;
  z-index: 1;
}

.announcement-card :deep(.el-card__body) {
  padding: 12px 16px;
}

.announcement-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
}

.announcement-header.is-static {
  cursor: default;
}

.announcement-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.announcement-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.announcement-icon {
  color: #e6a23c;
  font-size: 16px;
  flex-shrink: 0;
}

.announcement-title {
  display: block;
  flex: 1;
  min-width: 0;
  font-weight: 600;
  font-size: 15px;
  color: #333;
}

.dark .announcement-title {
  color: #fbbf24;
}

.announcement-date {
  color: #999;
  font-size: 12px;
}

.announcement-content-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e6d5b0;
}

.announcement-content {
  flex: 1;
  color: #666;
  font-size: 14px;
  line-height: 1.6;
}

.dark .announcement-content {
  color: #d1d5db;
}

.expand-icon {
  font-size: 14px;
  color: #e6a23c;
  transition: transform 0.3s ease;
}

.expand-icon.is-expanded {
  transform: rotate(180deg);
}

.announcement-close {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #bbb;
  cursor: pointer;
  transition: color 0.2s;
  font-size: 14px;
  margin-bottom: 2px;
}

.announcement-close:hover {
  color: #888;
}

.dark .announcement-close:hover {
  color: #d1d5db;
}

.announcement-close-inline {
  margin-bottom: 0;
}
</style>
