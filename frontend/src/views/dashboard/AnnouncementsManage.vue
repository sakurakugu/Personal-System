<script setup lang="ts">
/* global Event, TouchEvent, MouseEvent */
import { nextTick, onMounted, reactive, ref } from 'vue'
import {
  ElButton,
  ElCard,
  ElConfigProvider,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElPagination,
  ElSpace,
  ElSwitch,
  ElTag,
  ElMessage,
  ElMessageBox,
  ElIcon,
} from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { BellFilled, Plus, Edit, Delete, Check, Hide } from '@element-plus/icons-vue'
import {
  createAnnouncement,
  deleteAnnouncement,
  fetchAnnouncements as requestAnnouncements,
  updateAnnouncement,
} from '../../features/admin/api'
import type { AnnouncementPayload, AnnouncementRecord } from '../../features/admin/types'
import { getApiErrorMessage } from '../../shared/api'
import BaseDialog from '../../components/BaseDialog.vue'

const loading = ref(false)
const announcements = ref<AnnouncementRecord[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<string | null>(null)
const announcementTitleInputRef = ref<InstanceType<typeof ElInput> | null>(null)
const form = ref<AnnouncementPayload>({
  title: '',
  content: '',
  is_active: true,
})
const formLoading = ref(false)

// 滑动相关状态
const swipeState = reactive<Record<string, {
  offset: number
  startX: number
  startY: number
  isDragging: boolean
  hasMoved: boolean
}>>({})

const SWIPE_THRESHOLD = 80
const MAX_OFFSET = 120

function initSwipeState(id: string) {
  if (!swipeState[id]) {
    swipeState[id] = { offset: 0, startX: 0, startY: 0, isDragging: false, hasMoved: false }
  }
}

function onTouchStart(e: Event, id: string) {
  initSwipeState(id)
  const state = swipeState[id]
  state.isDragging = true

  if (e instanceof TouchEvent) {
    state.startX = e.touches[0].clientX
    state.startY = e.touches[0].clientY
  } else if (e instanceof MouseEvent) {
    state.startX = e.clientX
    state.startY = e.clientY
  }
}

function onTouchMove(e: Event, id: string) {
  const state = swipeState[id]
  if (!state?.isDragging) return

  let clientX = 0
  let clientY = 0
  if (e instanceof TouchEvent) {
    clientX = e.touches[0].clientX
    clientY = e.touches[0].clientY
  } else if (e instanceof MouseEvent) {
    clientX = e.clientX
    clientY = e.clientY
  }

  const deltaX = clientX - state.startX
  const deltaY = clientY - state.startY

  if (Math.abs(deltaY) > Math.abs(deltaX)) return

  if (Math.abs(deltaX) > 5) {
    state.hasMoved = true
  }

  if (e instanceof TouchEvent && Math.abs(deltaX) > 10) {
    e.preventDefault()
  }

  state.offset = Math.max(-MAX_OFFSET, Math.min(MAX_OFFSET, deltaX))
}

function onTouchEnd(id: string) {
  const state = swipeState[id]
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

  const announcement = announcements.value.find(a => a.id === id)
  if (!announcement) {
    state.offset = 0
    return
  }

  // 左滑：删除
  if (state.offset < -SWIPE_THRESHOLD) {
    void handleDeleteAnnouncement(announcement)
    state.offset = 0
    return
  }

  // 右滑：下架/上架
  if (state.offset > SWIPE_THRESHOLD) {
    void toggleStatus(announcement)
    state.offset = 0
    return
  }

  state.offset = 0
}

function getCardStyle(id: string) {
  const state = swipeState[id]
  if (!state) return {}
  return {
    transform: `translateX(${state.offset}px)`,
    transition: state.isDragging ? 'none' : 'transform 0.3s ease',
  }
}

function getLeftActionStyle(id: string) {
  const state = swipeState[id]
  if (!state) return { opacity: 0 }
  const opacity = Math.min(1, Math.max(0, state.offset / SWIPE_THRESHOLD))
  return {
    opacity: opacity,
    transform: `scale(${0.8 + opacity * 0.2})`,
  }
}

function getRightActionStyle(id: string) {
  const state = swipeState[id]
  if (!state) return { opacity: 0 }
  const opacity = Math.min(1, Math.max(0, -state.offset / SWIPE_THRESHOLD))
  return {
    opacity: opacity,
    transform: `scale(${0.8 + opacity * 0.2})`,
  }
}

function handleCardClick(row: AnnouncementRecord, id: string) {
  const state = swipeState[id]
  if (state?.hasMoved) {
    return
  }
  openEditDialog(row)
}

function focusAnnouncementTitleInput() {
  void nextTick(() => {
    announcementTitleInputRef.value?.focus()
    announcementTitleInputRef.value?.input?.focus()
  })
}

function buildAnnouncementPayload(): AnnouncementPayload {
  return {
    title: form.value.title.trim(),
    content: form.value.content.trim(),
    is_active: form.value.is_active,
  }
}

function formatAnnouncementDate(date: string) {
  return new Date(date).toLocaleString('zh-CN')
}

async function fetchAnnouncements() {
  loading.value = true
  try {
    const data = await requestAnnouncements(page.value, pageSize.value)
    announcements.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '获取公告列表失败'))
  } finally {
    loading.value = false
  }
}

function 用本地记录更新公告(record: AnnouncementRecord) {
  announcements.value = announcements.value.map((item) => (item.id === record.id ? record : item))
}

function 删除本地公告(id: string) {
  announcements.value = announcements.value.filter((item) => item.id !== id)
  delete swipeState[id]
}

function openCreateDialog() {
  isEdit.value = false
  editId.value = null
  form.value = {
    title: '',
    content: '',
    is_active: true,
  }
  dialogVisible.value = true
}

function openEditDialog(row: AnnouncementRecord) {
  isEdit.value = true
  editId.value = row.id
  form.value = {
    title: row.title,
    content: row.content,
    is_active: row.is_active,
  }
  dialogVisible.value = true
}

async function saveAnnouncement() {
  const payload = buildAnnouncementPayload()

  if (!payload.title) {
    ElMessage.warning('请输入标题')
    return
  }

  formLoading.value = true
  try {
    if (isEdit.value && editId.value) {
      const updated = await updateAnnouncement(editId.value, payload)
      用本地记录更新公告(updated)
      ElMessage.success('公告已更新')
    } else {
      const created = await createAnnouncement(payload)
      total.value += 1
      if (page.value === 1) {
        announcements.value = [created, ...announcements.value].slice(0, pageSize.value)
      }
      initSwipeState(created.id)
      ElMessage.success('公告已创建')
    }
    dialogVisible.value = false
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, isEdit.value ? '更新失败' : '创建失败'))
  } finally {
    formLoading.value = false
  }
}

async function handleDeleteAnnouncement(row: AnnouncementRecord) {
  try {
    await ElMessageBox.confirm(
      `确定要删除公告 "${row.title}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await deleteAnnouncement(row.id)
    ElMessage.success('公告已删除')
    total.value = Math.max(0, total.value - 1)
    删除本地公告(row.id)
    if (announcements.value.length === 0 && page.value > 1) {
      page.value -= 1
      await fetchAnnouncements()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(getApiErrorMessage(error, '删除失败'))
    }
  }
}

async function toggleStatus(row: AnnouncementRecord) {
  try {
    const updated = await updateAnnouncement(row.id, {
      title: row.title,
      content: row.content,
      is_active: !row.is_active,
    })
    用本地记录更新公告(updated)
    ElMessage.success('状态已更新')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '更新失败'))
  }
}

onMounted(() => {
  void fetchAnnouncements()
})
</script>

<template>
  <ElConfigProvider :locale="zhCn">
    <div class="page-container">
      <div class="page-header">
        <h2 class="page-title">
          <span class="page-title-text">
            <ElIcon><BellFilled /></ElIcon>
            <span>公告管理</span>
          </span>
          <ElButton type="primary" :icon="Plus" @click="openCreateDialog">
            新建公告
          </ElButton>
        </h2>
      </div>

      <ElCard class="announcements-card">
        <div class="announcements-body">
          <!-- 宽屏列表视图 -->
          <div class="announcements-table-wrap desktop-view">
            <div v-loading="loading" class="announcements-grid-shell">
              <div class="announcements-grid announcements-grid--head">
                <div class="announcements-grid__cell">标题</div>
                <div class="announcements-grid__cell">内容</div>
                <div class="announcements-grid__cell announcements-grid__cell--status">状态</div>
                <div class="announcements-grid__cell">创建时间</div>
                <div
                  class="announcements-grid__cell announcements-grid__cell--actions announcements-grid__cell--sticky-end"
                >
                  操作
                </div>
              </div>

              <div v-if="announcements.length" class="announcements-grid-body">
                <article
                  v-for="row in announcements"
                  :key="row.id"
                  class="announcements-grid announcements-grid--row"
                >
                  <div class="announcements-grid__cell" data-label="标题">
                    <div class="announcement-title">
                      {{ row.title }}
                    </div>
                  </div>

                  <div class="announcements-grid__cell" data-label="内容">
                    <span
                      :class="[
                        'content-preview',
                        { 'content-preview--placeholder': !row.content },
                      ]"
                    >
                      {{ row.content || '仅标题' }}
                    </span>
                  </div>

                  <div
                    class="announcements-grid__cell announcements-grid__cell--status"
                    data-label="状态"
                  >
                    <ElTag :type="row.is_active ? 'success' : 'info'" size="small">
                      {{ row.is_active ? '生效中' : '已下架' }}
                    </ElTag>
                  </div>

                  <div class="announcements-grid__cell" data-label="创建时间">
                    <span class="announcement-created-at">
                      {{ formatAnnouncementDate(row.created_at) }}
                    </span>
                  </div>

                  <div
                    class="announcements-grid__cell announcements-grid__cell--actions announcements-grid__cell--sticky-end"
                    data-label="操作"
                  >
                    <div class="announcement-actions">
                      <ElButton
                        type="primary"
                        size="small"
                        :icon="Edit"
                        class="announcement-action-button announcement-action-button--edit"
                        @click="openEditDialog(row)"
                      >
                        编辑
                      </ElButton>
                      <ElButton
                        :type="row.is_active ? 'warning' : 'success'"
                        size="small"
                        :class="[
                          'announcement-action-button',
                          row.is_active
                            ? 'announcement-action-button--warning'
                            : 'announcement-action-button--success',
                        ]"
                        @click="toggleStatus(row)"
                      >
                        {{ row.is_active ? '下架' : '上架' }}
                      </ElButton>
                      <ElButton
                        type="danger"
                        size="small"
                        :icon="Delete"
                        class="announcement-action-button announcement-action-button--delete"
                        @click="handleDeleteAnnouncement(row)"
                      >
                        删除
                      </ElButton>
                    </div>
                  </div>
                </article>
              </div>

              <ElEmpty v-else-if="!loading" description="暂无公告" class="announcements-empty" />
            </div>
          </div>

          <!-- 窄屏卡片视图 -->
          <div class="announcements-card-wrap mobile-view">
            <div v-loading="loading" class="announcement-card-list">
              <div
                v-for="row in announcements"
                :key="row.id"
                class="announcement-swipe-item"
                @touchstart.passive="(event) => onTouchStart(event, row.id)"
                @touchmove="(event) => onTouchMove(event, row.id)"
                @touchend="() => onTouchEnd(row.id)"
                @touchcancel="() => onTouchEnd(row.id)"
                @mousedown="(event) => onTouchStart(event, row.id)"
                @mousemove="(event) => onTouchMove(event, row.id)"
                @mouseup="() => onTouchEnd(row.id)"
                @mouseleave="() => onTouchEnd(row.id)"
              >
                <!-- 左侧操作按钮（右滑显示下架/上架） -->
                <div class="swipe-action left-action" :style="getLeftActionStyle(row.id)">
                  <ElIcon :size="24"><component :is="row.is_active ? Hide : Check" /></ElIcon>
                  <span class="action-text">{{ row.is_active ? '下架' : '上架' }}</span>
                </div>

                <!-- 右侧操作按钮（左滑显示删除） -->
                <div class="swipe-action right-action" :style="getRightActionStyle(row.id)">
                  <ElIcon :size="24"><Delete /></ElIcon>
                  <span class="action-text">删除</span>
                </div>

                <!-- 公告卡片 -->
                <ElCard
                  class="announcement-card"
                  :class="{ 'is-active': row.is_active, 'is-inactive': !row.is_active }"
                  :style="getCardStyle(row.id)"
                  @click="handleCardClick(row, row.id)"
                >
                  <!-- 头部：标题 -->
                  <div class="card-header">
                    <div class="card-title">{{ row.title }}</div>
                  </div>

                  <!-- 内容 -->
                  <div v-if="row.content" class="card-content">
                    {{ row.content }}
                  </div>
                  <div v-else class="card-content card-content--placeholder">
                    仅标题
                  </div>

                  <!-- 底部：创建时间 -->
                  <div class="card-footer">
                    <span class="card-time">{{ formatAnnouncementDate(row.created_at) }}</span>
                  </div>
                </ElCard>
              </div>

              <ElEmpty v-if="announcements.length === 0 && !loading" description="暂无公告" />
            </div>
          </div>

          <div class="pagination-wrap">
            <ElPagination
              v-model:current-page="page"
              v-model:page-size="pageSize"
              :total="total"
              layout="total, sizes, prev, pager, next"
              :page-sizes="[10, 20, 50]"
              @change="fetchAnnouncements"
            />
          </div>
        </div>
      </ElCard>

      <!-- 新建/编辑对话框 -->
      <BaseDialog
        v-model="dialogVisible"
        :title="isEdit ? '编辑公告' : '新建公告'"
        width="600px"
        destroy-on-close
        @opened="focusAnnouncementTitleInput"
      >
        <ElForm :model="form" label-width="80px" class="announcement-form">
          <ElFormItem label="标题" required>
            <ElInput
              ref="announcementTitleInputRef"
              v-model="form.title"
              placeholder="请输入公告标题"
              maxlength="200"
              show-word-limit
            />
          </ElFormItem>
          <ElFormItem label="内容">
            <ElInput
              v-model="form.content"
              type="textarea"
              :rows="6"
              placeholder="请输入公告内容（选填）"
            />
          </ElFormItem>
          <ElFormItem label="立即生效">
            <ElSwitch v-model="form.is_active" />
          </ElFormItem>
        </ElForm>
        <template #footer>
          <ElSpace>
            <ElButton @click="dialogVisible = false">取消</ElButton>
            <ElButton type="primary" :loading="formLoading" @click="saveAnnouncement">
              {{ isEdit ? '保存' : '创建' }}
            </ElButton>
          </ElSpace>
        </template>
      </BaseDialog>
    </div>
  </ElConfigProvider>
</template>

<style scoped>
@import '../../styles/media.css';

.page-container {
  height: 100%;
  padding: 24px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: hidden;
}

.page-header {
  flex-shrink: 0;
}

.page-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 0;
}

.page-title-text {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.announcements-card {
  flex: 1;
  min-height: 0;
  border-radius: var(--dashboard-panel-radius, 12px);
  overflow: hidden;
}

.announcements-card :deep(.el-card__body) {
  height: 100%;
  padding: 0;
}

.announcements-body {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* 桌面端视图 */
.desktop-view {
  flex: 1;
  min-height: 0;
  padding: 0;
  overflow: hidden;
}

/* 移动端视图 - 默认隐藏 */
.mobile-view {
  display: none;
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.announcements-table-wrap {
  flex: 1;
  min-height: 0;
  padding: 0;
  overflow: hidden;
}

.announcements-grid-shell {
  --announcement-sticky-shadow-strong: color-mix(
    in srgb,
    var(--text-primary, #333333) 16%,
    transparent
  );
  --announcement-sticky-shadow-soft: color-mix(
    in srgb,
    var(--text-primary, #333333) 8%,
    transparent
  );
  --announcement-row-hover-bg: color-mix(
    in srgb,
    var(--bg-card, #ffffff) 78%,
    var(--bg-hover, #f5f7fa) 22%
  );
  height: 100%;
  min-height: 0;
  background: var(--bg-card, #ffffff);
  border-radius: inherit;
  overflow: auto;
}

.announcements-grid {
  display: grid;
  grid-template-columns: minmax(180px, 1.1fr) minmax(260px, 1.65fr) 100px 160px 248px;
  min-width: 958px;
}

.announcements-grid--head {
  position: sticky;
  top: 0;
  z-index: 2;
}

.announcements-grid--head .announcements-grid__cell {
  min-height: 40px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary, #666666);
  background: var(--bg-hover, #f5f7fa);
  border-bottom: 1px solid var(--border-color, #e8e8e8);
}

.announcements-grid--head .announcements-grid__cell:first-child {
  border-top-left-radius: var(--dashboard-panel-radius, 12px);
}

.announcements-grid--head .announcements-grid__cell:last-child {
  border-top-right-radius: var(--dashboard-panel-radius, 12px);
}

.announcements-grid-body {
  min-width: fit-content;
}

.announcements-grid--row {
  --announcement-row-bg: var(--bg-card, #ffffff);
  isolation: isolate;
}

.announcements-grid--row:nth-child(even) {
  --announcement-row-bg: color-mix(in srgb, var(--bg-card, #ffffff) 94%, var(--text-primary, #333333) 6%);
}

.announcements-grid__cell {
  min-width: 0;
  min-height: 52px;
  padding: 8px 14px;
  display: flex;
  align-items: center;
  background: var(--announcement-row-bg);
  color: var(--text-primary, #333333);
  border-bottom: 1px solid var(--border-color, #e8e8e8);
  transition: background-color 0.2s ease;
}

.announcements-grid--row:hover > .announcements-grid__cell {
  background: var(--announcement-row-hover-bg);
}

.announcements-grid__cell--status {
  justify-content: center;
}

.announcements-grid__cell--actions {
  justify-content: flex-start;
}

.announcements-grid__cell--sticky-end {
  position: sticky;
  right: 0;
  z-index: 1;
}

.announcements-grid__cell--sticky-end::before {
  content: '';
  position: absolute;
  pointer-events: none;
}

.announcements-grid__cell--sticky-end::before {
  top: 0;
  bottom: 0;
  left: -16px;
  width: 16px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--announcement-sticky-shadow-soft) 58%,
    var(--announcement-sticky-shadow-strong) 100%
  );
}

.announcements-grid--head .announcements-grid__cell--sticky-end {
  z-index: 3;
}

.announcements-grid--row .announcements-grid__cell--sticky-end {
  background: var(--announcement-row-bg);
}

.announcements-empty {
  min-height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.announcement-title {
  font-weight: 600;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pagination-wrap {
  flex-shrink: 0;
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: flex-end;
  padding: 6px 14px 8px;
  border-top: 1px solid var(--el-border-color);
  background: var(--bg-card, #ffffff);
}

.pagination-wrap :deep(.el-pagination__total) {
  color: var(--text-primary, #333333);
}

.pagination-wrap :deep(.el-pagination__sizes) {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
}

.pagination-wrap :deep(.el-pagination__sizes .el-select) {
  display: inline-flex;
  align-items: center;
  width: 100px !important;
  min-width: 100px;
  flex-shrink: 0;
}

.pagination-wrap :deep(.el-pagination__sizes .el-select__wrapper) {
  width: 100%;
  min-width: 80px;
  justify-content: center;
}

.pagination-wrap :deep(.el-pagination__sizes .el-input__wrapper) {
  display: inline-flex;
  align-items: center;
  width: 100%;
}

.pagination-wrap :deep(.el-pagination__sizes .el-select__selection) {
  justify-content: center;
}

.pagination-wrap :deep(.el-pagination__sizes .el-select__selected-item),
.pagination-wrap :deep(.el-pagination__sizes .el-select__placeholder) {
  width: 100%;
  text-align: center;
  justify-content: center;
}

.content-preview {
  display: inline-block;
  width: 100%;
  line-height: 1.4;
  color: var(--text-secondary, #666666);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.content-preview--placeholder {
  color: color-mix(in srgb, var(--text-secondary, #666666) 72%, transparent);
  font-style: italic;
}

.announcement-created-at {
  display: inline-block;
  white-space: nowrap;
}

.announcement-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: flex-start;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.announcement-action-button {
  margin: 0;
}

.announcement-action-button--edit {
  --el-button-text-color: #ffffff;
  --el-button-bg-color: var(--el-color-primary);
  --el-button-border-color: var(--el-color-primary);
  --el-button-hover-text-color: #ffffff;
  --el-button-hover-bg-color: var(--el-color-primary-light-3);
  --el-button-hover-border-color: var(--el-color-primary-light-3);
  --el-button-active-text-color: #ffffff;
  --el-button-active-bg-color: var(--el-color-primary-dark-2);
  --el-button-active-border-color: var(--el-color-primary-dark-2);
}

.announcement-action-button--success {
  --el-button-text-color: #ffffff;
  --el-button-bg-color: #67c23a;
  --el-button-border-color: #67c23a;
  --el-button-hover-text-color: #ffffff;
  --el-button-hover-bg-color: #85ce61;
  --el-button-hover-border-color: #85ce61;
  --el-button-active-text-color: #ffffff;
  --el-button-active-bg-color: #5daf34;
  --el-button-active-border-color: #5daf34;
}

.announcement-action-button--warning {
  --el-button-text-color: #ffffff;
  --el-button-bg-color: #e6a23c;
  --el-button-border-color: #e6a23c;
  --el-button-hover-text-color: #ffffff;
  --el-button-hover-bg-color: #ebb563;
  --el-button-hover-border-color: #ebb563;
  --el-button-active-text-color: #ffffff;
  --el-button-active-bg-color: #cf9236;
  --el-button-active-border-color: #cf9236;
}

.announcement-action-button--delete {
  --el-button-text-color: #ffffff;
  --el-button-bg-color: #f56c6c;
  --el-button-border-color: #f56c6c;
  --el-button-hover-text-color: #ffffff;
  --el-button-hover-bg-color: #f78989;
  --el-button-hover-border-color: #f78989;
  --el-button-active-text-color: #ffffff;
  --el-button-active-bg-color: #dd6161;
  --el-button-active-border-color: #dd6161;
}

.announcement-form :deep(.el-input__count),
.announcement-form :deep(.el-input__count-inner) {
  color: var(--text-primary, #333333);
}

.announcement-form :deep(.el-input__count-inner) {
  background: transparent;
}

/* ===== 移动端卡片样式 ===== */
.announcement-card-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
}

/* 滑动容器 */
.announcement-swipe-item {
  position: relative;
  touch-action: pan-y;
  user-select: none;
}

/* 滑动操作按钮 */
.swipe-action {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  border-radius: 12px;
  transition: opacity 0.2s ease, transform 0.2s ease;
  pointer-events: none;
}

.left-action {
  left: 0;
  background: linear-gradient(90deg, var(--el-color-success) 0%, var(--el-color-success-light-3) 100%);
}

.right-action {
  right: 0;
  background: linear-gradient(270deg, #f56c6c 0%, #f89898 100%);
}

.action-text {
  margin-top: 4px;
  font-size: 11px;
  white-space: nowrap;
}

/* 公告卡片 */
.announcement-card {
  border-radius: 12px;
  position: relative;
  z-index: 1;
  background: white;
  cursor: pointer;
  overflow: hidden;
  border-left: 3px solid #909399;
}

.announcement-card.is-active {
  border-left-color: var(--el-color-primary);
}

.announcement-card.is-inactive {
  border-left-color: #909399;
}

.announcement-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.announcement-card:active {
  cursor: grabbing;
}

.announcement-card :deep(.el-card__body) {
  padding: 12px 16px;
}

.dark .announcement-card {
  background: var(--el-bg-color-overlay);
  --el-card-bg-color: var(--el-bg-color-overlay);
}

.dark .announcement-card.is-active {
  border-left: 3px solid var(--el-color-primary) !important;
}

.dark .announcement-card.is-inactive {
  border-left: 3px solid #909399 !important;
}

/* 卡片头部 */
.card-header {
  margin-bottom: 8px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

/* 卡片内容 */
.card-content {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.card-content--placeholder {
  color: #999;
  font-style: italic;
}

.dark .card-content {
  color: #aaa;
}

.dark .card-content--placeholder {
  color: #777;
}

/* 卡片底部 */
.card-footer {
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.card-time {
  font-size: 12px;
  color: #999;
  text-align: right;
}

.dark .card-time {
  color: #777;
}

/* 响应式布局 */
@media (--mobile-viewport) {
  .page-container {
    padding: 24px;
    gap: 12px;
  }

  .page-title {
    align-items: center;
    flex-direction: row;
    flex-wrap: wrap;
  }

  /* 宽屏视图隐藏 */
  .desktop-view {
    display: none;
  }

  /* 窄屏视图显示 */
  .mobile-view {
    display: block;
  }

  .pagination-wrap {
    justify-content: center;
    padding: 6px 12px 8px;
  }
}

@media (min-width: 769px) {
  .desktop-view {
    display: block;
  }

  .mobile-view {
    display: none;
  }
}
</style>

