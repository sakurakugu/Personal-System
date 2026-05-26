<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElButton, ElCard, ElInput, ElMessage, ElPopconfirm, ElSkeleton, ElSpace, ElTooltip } from 'element-plus'
import { Plus, RefreshLeft } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import { UniversalAvatar } from '@personal-system/ui'
import { 使用认证存储 } from '@personal-system/domain/auth'
import {
  删除动态图片,
  获取动态图片,
  重新排序动态图片,
  上传动态图片,
} from '../api'
import { 使用动态存储 } from '../store'
import MomentImageComposer from './动态图片编辑器.vue'
import type { MomentImageRecord } from '../types'

const props = withDefaults(defineProps<{
  title?: string
  compact?: boolean
  overlayMode?: boolean
}>(), {
  title: '编写动态',
  compact: false,
  overlayMode: false,
})

const emit = defineEmits<{
  published: []
  saved: []
}>()

const auth = 使用认证存储()
const momentStore = 使用动态存储()
const route = useRoute()
const router = useRouter()

const draftForm = ref({
  title: '',
  content: '',
})
const loadingDraft = ref(false)
const momentImages = ref<MomentImageRecord[]>([])
const momentImagesLoading = ref(false)
const momentImagesUploading = ref(false)
const momentImagesExpanded = ref(false)
const 动态图片上限 = 20

const avatarText = computed(() => (auth.user?.nickname?.trim() || auth.user?.username || '你').slice(0, 1).toUpperCase())
const isOverLimit = computed(() => draftForm.value.content.length > 1000)
const currentMomentDraftId = computed(() => momentStore.draft?.id || '')
const 文章编辑页路径 = computed(() => (route.path.startsWith('/dashboard') ? '/dashboard/articles/edit' : '/articles/edit'))

let saveTimeout: number | null = null

function 获取API错误消息(error: unknown, fallback: string) {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = Reflect.get(error, 'response')
    if (typeof response === 'object' && response !== null && 'data' in response) {
      const data = Reflect.get(response, 'data')
      if (typeof data === 'object' && data !== null && 'detail' in data) {
        const detail = Reflect.get(data, 'detail')
        if (typeof detail === 'string' && detail.trim()) {
          return detail
        }
      }
    }
  }
  if (error instanceof Error && error.message.trim()) {
    return error.message
  }
  return fallback
}

async function loadDraft() {
  loadingDraft.value = true
  try {
    const draft = await momentStore.获取草稿()
    draftForm.value.title = draft?.title || ''
    draftForm.value.content = draft?.content || ''
    if (draft?.id) {
      await loadMomentImages(draft.id)
      momentImagesExpanded.value = momentImages.value.length > 0
    } else {
      momentImages.value = []
      momentImagesExpanded.value = false
    }
    console.info('[MomentComposer] 草稿已加载', { hasDraft: Boolean(draft?.id) })
  } catch (error) {
    console.error('[MomentComposer] 加载草稿失败', error)
    ElMessage.error(获取API错误消息(error, '加载草稿失败'))
  } finally {
    loadingDraft.value = false
  }
}

async function loadMomentImages(momentId: string) {
  if (!momentId) {
    momentImages.value = []
    momentImagesLoading.value = false
    return
  }

  momentImagesLoading.value = true
  try {
    momentImages.value = await 获取动态图片(momentId)
  } catch (error) {
    momentImages.value = []
    console.error('[MomentComposer] 加载动态图片失败', error)
    ElMessage.error(获取API错误消息(error, '加载动态图片失败'))
  } finally {
    momentImagesLoading.value = false
  }
}

async function ensureMomentDraftForImageUpload(): Promise<string> {
  if (currentMomentDraftId.value) {
    return currentMomentDraftId.value
  }

  const draft = await momentStore.保存草稿({
    title: draftForm.value.title,
    content: draftForm.value.content,
  })
  console.info('[MomentComposer] 已创建图片上传草稿', { draftId: draft.id })
  return draft.id
}

async function 保存草稿到服务器(allowEmpty = false) {
  const title = draftForm.value.title.trim()
  const content = draftForm.value.content.trim()
  if (!allowEmpty && !title && !content) {
    return
  }

  await momentStore.保存草稿({
    title: draftForm.value.title,
    content: draftForm.value.content,
  })
  emit('saved')
}

function autoSave() {
  if (saveTimeout) window.clearTimeout(saveTimeout)
  saveTimeout = window.setTimeout(async () => {
    if (draftForm.value.content.trim() || draftForm.value.title.trim()) {
      try {
        await 保存草稿到服务器()
      } catch (error) {
        console.error('[MomentComposer] 自动保存草稿失败', error)
      }
    }
  }, 1000)
}

async function handleSaveDraft() {
  if (!draftForm.value.content.trim()) {
    ElMessage.warning('内容不能为空')
    return
  }
  try {
    await 保存草稿到服务器()
    console.info('[MomentComposer] 草稿已手动保存')
    ElMessage.success('草稿已保存')
  } catch (error) {
    console.error('[MomentComposer] 保存草稿失败', error)
    ElMessage.error(获取API错误消息(error, '保存草稿失败'))
  }
}

async function handlePublish() {
  if (!draftForm.value.content.trim()) {
    ElMessage.warning('内容不能为空')
    return
  }
  if (isOverLimit.value) {
    ElMessage.warning('内容超过1000字限制')
    return
  }

  try {
    const published = await momentStore.发布({
      title: draftForm.value.title,
      content: draftForm.value.content,
    })
    console.info('[MomentComposer] 动态已发布', { momentId: published.id })
    ElMessage.success('发布成功')
    draftForm.value = { title: '', content: '' }
    momentImages.value = []
    momentImagesExpanded.value = false
    emit('published')
  } catch (error) {
    console.error('[MomentComposer] 发布动态失败', error)
    ElMessage.error(获取API错误消息(error, '发布动态失败'))
  }
}

async function handleClearDraft() {
  try {
    if (currentMomentDraftId.value && momentImages.value.length > 0) {
      await Promise.allSettled(
        momentImages.value.map((image) => 删除动态图片(currentMomentDraftId.value, image.id)),
      )
    }
    draftForm.value = { title: '', content: '' }
    await momentStore.保存草稿({ title: '', content: '' })
    momentImages.value = []
    momentImagesExpanded.value = false
    console.info('[MomentComposer] 草稿已清空')
    ElMessage.success('草稿已清空')
  } catch (error) {
    console.error('[MomentComposer] 清空草稿失败', error)
    ElMessage.error(获取API错误消息(error, '清空草稿失败'))
  }
}

async function handleCreateArticle() {
  try {
    await router.push(文章编辑页路径.value)
  } catch (error) {
    console.error('[MomentComposer] 跳转新增文章页面失败', error)
    ElMessage.error('打开新增文章页面失败')
  }
}

async function handleMomentImageUpload(files: globalThis.File[]) {
  const imageFiles = files.filter((file) => file.type.startsWith('image/'))
  if (imageFiles.length === 0) {
    ElMessage.warning('只能上传图片文件')
    return
  }

  const remainingCount = 动态图片上限 - momentImages.value.length
  if (remainingCount <= 0) {
    ElMessage.warning(`单条动态最多只能上传 ${动态图片上限} 张图片`)
    return
  }

  const filesToUpload = imageFiles.slice(0, remainingCount)
  if (filesToUpload.length < imageFiles.length) {
    ElMessage.warning(`最多还能上传 ${remainingCount} 张图片`)
  }

  momentImagesExpanded.value = true
  momentImagesUploading.value = true
  try {
    const momentId = await ensureMomentDraftForImageUpload()
    for (const file of filesToUpload) {
      await 上传动态图片(momentId, file)
    }
    await loadMomentImages(momentId)
    console.info('[MomentComposer] 动态图片上传完成', { count: filesToUpload.length })
    ElMessage.success(`已上传 ${filesToUpload.length} 张图片`)
  } catch (error) {
    console.error('[MomentComposer] 上传动态图片失败', error)
    ElMessage.error(获取API错误消息(error, '图片上传失败'))
  } finally {
    momentImagesUploading.value = false
  }
}

async function handleMomentImageDelete(imageId: string) {
  if (!currentMomentDraftId.value) {
    return
  }

  try {
    await 删除动态图片(currentMomentDraftId.value, imageId)
    momentImages.value = momentImages.value.filter((image) => image.id !== imageId)
    console.info('[MomentComposer] 动态图片已删除', { imageId })
    ElMessage.success('图片已删除')
  } catch (error) {
    console.error('[MomentComposer] 删除动态图片失败', error)
    ElMessage.error(获取API错误消息(error, '删除图片失败'))
  }
}

async function handleMomentImageReorder(imageIds: string[]) {
  if (!currentMomentDraftId.value) {
    return
  }

  try {
    momentImages.value = await 重新排序动态图片(currentMomentDraftId.value, imageIds)
    console.info('[MomentComposer] 动态图片已重新排序', { count: imageIds.length })
  } catch (error) {
    console.error('[MomentComposer] 动态图片排序失败', error)
    ElMessage.error(获取API错误消息(error, '图片排序失败'))
  }
}

onMounted(() => {
  void loadDraft()
})

onBeforeUnmount(() => {
  if (saveTimeout) {
    window.clearTimeout(saveTimeout)
    saveTimeout = null
  }
})

defineExpose({
  保存草稿: 保存草稿到服务器,
})
</script>

<template>
  <ElCard
    class="moment-compose-card"
    :class="{
      'moment-compose-card--compact': compact,
      'moment-compose-card--overlay': overlayMode,
    }"
    shadow="never"
  >
    <ElSkeleton :loading="loadingDraft" animated>
      <div class="moment-compose-header">
        <div class="moment-compose-title">
          <span class="moment-compose-title__bar" aria-hidden="true" />
          <span>{{ title }}</span>
        </div>
        <ElSpace>
          <ElTooltip content="自动获取上次未发布的内容">
            <ElButton text :icon="RefreshLeft" :loading="loadingDraft" @click="loadDraft">
              刷新草稿
            </ElButton>
          </ElTooltip>
          <ElButton text :icon="Plus" @click="handleCreateArticle">
            新增文章
          </ElButton>
        </ElSpace>
      </div>

      <div class="moment-compose-main">
        <div class="moment-compose-avatar">
          <UniversalAvatar
            :src="auth.user?.avatar_url"
            :text="avatarText"
            :size="40"
            alt="当前用户头像"
            class="moment-compose-avatar__image"
          />
        </div>
        <div class="moment-compose-form">
          <div class="moment-compose-fields">
            <div class="moment-compose-editor" :class="{ 'moment-compose-editor--over-limit': isOverLimit }">
              <ElInput
                v-model="draftForm.title"
                class="moment-compose-title-input"
                placeholder="标题（可选）"
                maxlength="100"
                @input="autoSave"
              />
              <div class="moment-compose-editor__divider" aria-hidden="true" />
              <div class="moment-compose-content-field">
              <ElInput
                v-model="draftForm.content"
                class="moment-compose-content-input"
                type="textarea"
                :autosize="{ minRows: compact ? 5 : 4 }"
                resize="none"
                placeholder="分享一下你现在在想什么？"
                maxlength="1000"
                @input="autoSave"
              />
              </div>
              <div class="moment-compose-editor__divider" aria-hidden="true" />
              <div class="moment-compose-content-meta">
                <span
                  class="moment-compose-content-count"
                  :class="{ 'moment-compose-content-count--danger': isOverLimit }"
                >
                  {{ draftForm.content.length }}/1000
                </span>
              </div>
            </div>
            <MomentImageComposer
              :expanded="momentImagesExpanded"
              :items="momentImages"
              :loading="momentImagesLoading"
              :uploading="momentImagesUploading"
              :max-count="动态图片上限"
              @toggle="momentImagesExpanded = !momentImagesExpanded"
              @upload-files="handleMomentImageUpload"
              @delete="handleMomentImageDelete"
              @reorder="handleMomentImageReorder"
            />
          </div>
          <div class="moment-compose-footer">
            <div class="moment-compose-actions">
              <ElButton :loading="momentStore.saving" @click="handleSaveDraft">保存草稿</ElButton>
              <ElPopconfirm
                title="确定要清空草稿吗？"
                confirm-button-text="确定"
                cancel-button-text="取消"
                @confirm="handleClearDraft"
              >
                <template #reference>
                  <ElButton>清空</ElButton>
                </template>
              </ElPopconfirm>
              <ElButton type="primary" :disabled="isOverLimit || !draftForm.content.trim()" @click="handlePublish">
                发布
              </ElButton>
            </div>
          </div>
        </div>
      </div>
    </ElSkeleton>
  </ElCard>
</template>

<style scoped>
.moment-compose-card {
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.1);
  border-radius: var(--radius-large);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
  backdrop-filter: blur(10px);
}

.moment-compose-card--overlay {
  background: var(--card-bg-transparent, rgba(255, 255, 255, 0.68));
  border: 1px solid rgba(255, 255, 255, 0.45);
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
  backdrop-filter: blur(18px);
}

.moment-compose-card :deep(.el-card__body) {
  padding: 16px 18px;
}

.moment-compose-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgb(var(--el-color-primary-rgb) / 0.08);
}

.moment-compose-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 1.125rem;
  font-weight: 700;
  line-height: 1.5;
  color: #102418;
}

.moment-compose-title__bar {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--primary);
  flex: 0 0 auto;
}

.moment-compose-main {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.moment-compose-avatar {
  flex: 0 0 auto;
}

.moment-compose-avatar__image {
  border: 3px solid rgba(255, 255, 255, 0.82);
}

.moment-compose-form {
  display: flex;
  flex-direction: column;
  gap: 0;
  flex: 1;
  min-width: 0;
}

.moment-compose-fields {
  display: grid;
  gap: 12px;
  padding-bottom: 12px;
}

.moment-compose-form :deep(.el-input),
.moment-compose-form :deep(.el-textarea) {
  --el-input-bg-color: var(--moment-compose-editor-surface);
  --el-fill-color-blank: var(--moment-compose-editor-surface);
  --el-input-hover-border-color: rgb(var(--el-color-primary-rgb) / 0.18);
  --el-input-focus-border-color: rgb(var(--el-color-primary-rgb) / 0.18);
}

.moment-compose-title-input {
  margin-bottom: 0;
}

.moment-compose-editor {
  --moment-compose-editor-surface: var(--el-color-primary-light-9);
  --moment-compose-content-surface: var(--el-color-primary-light-9);
  --moment-compose-editor-divider: var(--el-color-primary-light-5);
  --moment-compose-editor-divider-active: var(--el-color-primary-light-3);
  display: flex;
  flex-direction: column;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.08);
  border-radius: 0.5rem;
  background: var(--moment-compose-editor-surface);
  overflow: hidden;
  transition:
    border-color 0.18s ease,
    background-color 0.18s ease;
}

.moment-compose-editor:hover,
.moment-compose-editor:focus-within {
  border-color: rgb(var(--el-color-primary-rgb) / 0.18);
  background: var(--moment-compose-editor-surface);
}

.moment-compose-editor__divider {
  position: relative;
  height: 1px;
  margin: 0 16px;
  background: var(--moment-compose-editor-surface);
  transition: background-color 0.18s ease;
}

.moment-compose-editor__divider::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--moment-compose-editor-divider);
  transition: background-color 0.18s ease;
}

.moment-compose-editor:hover .moment-compose-editor__divider::before,
.moment-compose-editor:focus-within .moment-compose-editor__divider::before {
  background: var(--moment-compose-editor-divider-active);
}

.moment-compose-content-field {
  display: flex;
  flex-direction: column;
  background: var(--moment-compose-content-surface);
}

.moment-compose-content-meta {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 8px 16px 10px;
  background: var(--moment-compose-content-surface);
  color: var(--text-secondary);
  transition:
    background-color 0.18s ease,
    color 0.18s ease;
}

.moment-compose-content-count {
  font-size: 12px;
  line-height: 1;
}

.moment-compose-content-count--danger {
  color: var(--el-color-danger);
}

.moment-compose-form :deep(.el-input__wrapper),
.moment-compose-form :deep(.el-textarea__inner) {
  border: none;
  box-shadow: none;
  background: var(--moment-compose-editor-surface);
  transition:
    border-color 0.18s ease,
    background-color 0.18s ease;
}

.moment-compose-form :deep(.el-input__wrapper) {
  min-height: 44px;
  border-radius: 0;
  padding: 0 16px;
}

.moment-compose-form :deep(.el-textarea__inner) {
  border-radius: 0;
  padding: 14px 16px;
  line-height: 1.7;
  overflow-y: hidden;
  background: var(--moment-compose-content-surface);
}

.moment-compose-title-input :deep(.el-input__inner) {
  font-size: 17px;
  font-weight: 700;
  line-height: 1.5;
}

.moment-compose-title-input :deep(.el-input__wrapper) {
  background: var(--moment-compose-editor-surface);
  padding-top: 4px;
  padding-bottom: 4px;
}

.moment-compose-form :deep(.el-input__wrapper:hover),
.moment-compose-form :deep(.el-input__wrapper.is-focus),
.moment-compose-form :deep(.el-textarea__inner:hover),
.moment-compose-form :deep(.el-textarea__inner:focus) {
  background: var(--moment-compose-editor-surface);
}

.moment-compose-form :deep(.el-input__wrapper:hover),
.moment-compose-form :deep(.el-input__wrapper.is-focus-within),
.moment-compose-form :deep(.el-textarea__inner:hover),
.moment-compose-form :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}

.moment-compose-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-top: 12px;
}

.moment-compose-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.moment-compose-footer :deep(.el-button) {
  border-radius: 0.5rem;
}

.moment-compose-card--compact :deep(.el-card__body) {
  padding: 14px;
}

.dark .moment-compose-card {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent);
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent), color-mix(in srgb, var(--el-color-primary-light-5) 5%, transparent)),
    rgba(18, 25, 22, 0.9);
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.24);
}

.dark .moment-compose-card--overlay {
  background: var(--card-bg-transparent, rgba(15, 23, 42, 0.62));
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.dark .moment-compose-title {
  color: #eef8f1;
}

.dark .moment-compose-header {
  border-bottom-color: color-mix(in srgb, var(--el-color-primary-light-5) 10%, transparent);
}

.dark .moment-compose-form :deep(.el-input__wrapper),
.dark .moment-compose-form :deep(.el-textarea__inner) {
  background: var(--moment-compose-content-surface);
  color: var(--text-secondary);
}

.dark .moment-compose-editor {
  --moment-compose-editor-surface: color-mix(in srgb, var(--el-color-primary) 14%, #121916);
  --moment-compose-content-surface: color-mix(in srgb, var(--el-color-primary) 14%, #121916);
  --moment-compose-editor-divider: var(--el-color-primary-light-5);
  --moment-compose-editor-divider-active: var(--el-color-primary-light-3);
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 10%, transparent);
  background: var(--moment-compose-editor-surface);
}

.dark .moment-compose-editor:hover,
.dark .moment-compose-editor:focus-within {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 18%, transparent);
  background: var(--moment-compose-editor-surface);
}

.dark .moment-compose-content-meta {
  background: var(--moment-compose-content-surface);
  color: var(--text-secondary);
}

.dark .moment-compose-form :deep(.el-input),
.dark .moment-compose-form :deep(.el-textarea) {
  --el-input-bg-color: var(--moment-compose-content-surface);
  --el-fill-color-blank: var(--moment-compose-content-surface);
}

.dark .moment-compose-form :deep(.el-input__wrapper:hover),
.dark .moment-compose-form :deep(.el-input__wrapper.is-focus),
.dark .moment-compose-form :deep(.el-textarea__inner:hover),
.dark .moment-compose-form :deep(.el-textarea__inner:focus) {
  background: var(--moment-compose-content-surface);
}

@media (max-width: 767px) {
  .moment-compose-main,
  .moment-compose-header,
  .moment-compose-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .moment-compose-avatar {
    align-self: flex-start;
  }
}
</style>
