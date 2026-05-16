<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  ElButton, ElCard, ElEmpty, ElForm, ElFormItem, ElIcon, ElInput, ElMessage, ElMessageBox,
  ElPagination, ElPopconfirm, ElSpace, ElSkeleton, ElTabPane, ElTabs, ElTag, ElTooltip,
} from 'element-plus'
import { ChatDotRound, Delete, DocumentChecked, Edit, Plus, RefreshLeft } from '@element-plus/icons-vue'
import { getApiErrorMessage } from '@personal-system/api'
import {
  deleteMomentImage,
  fetchMomentImages,
  reorderMomentImages,
  uploadMomentImage,
} from '../api'
import { resolveManagedFileUrl } from '../managedFile'
import { useMomentStore } from '../store'
import type { MomentImageRecord, UserMoment } from '../types'
import { useSaveShortcut } from '../useSaveShortcut'
import MomentImageComposer from '../components/MomentImageComposer.vue'

const store = useMomentStore()

const draftForm = ref({
  title: '',
  content: '',
})
const momentImages = ref<MomentImageRecord[]>([])

const loadingDraft = ref(false)
const momentsInitialLoading = ref(true)
const momentsRefreshing = ref(false)
const momentImagesLoading = ref(false)
const momentImagesUploading = ref(false)
const momentImagesExpanded = ref(false)
const 动态图片上限 = 20
const currentListMode = ref<'active' | 'deleted'>('active')
const editingMoment = ref<UserMoment | null>(null)

const contentLength = computed(() => draftForm.value.content.length)
const isOverLimit = computed(() => contentLength.value > 1000)
const currentMomentDraftId = computed(() => store.draft?.id || '')
const isEditingPublishedMoment = computed(() => editingMoment.value !== null)
const currentEditorMomentId = computed(() => (isEditingPublishedMoment.value ? editingMoment.value?.id || '' : currentMomentDraftId.value))
const isRecycleBinMode = computed(() => currentListMode.value === 'deleted')
const momentsEmptyDescription = computed(() => (isRecycleBinMode.value ? '回收站里还没有动态' : '还没有发布过动态'))

useSaveShortcut({
  enabled: () => !store.saving,
  onSave: handleSaveDraft,
})

async function loadDraft() {
  loadingDraft.value = true
  try {
    const draft = await store.fetchDraft()
    if (draft) {
      draftForm.value.title = draft.title || ''
      draftForm.value.content = draft.content
      await loadMomentImages(draft.id)
      if (momentImages.value.length > 0) {
        momentImagesExpanded.value = true
      }
      return
    }
    draftForm.value = { title: '', content: '' }
    momentImages.value = []
    momentImagesExpanded.value = false
  } finally {
    loadingDraft.value = false
  }
}

async function loadMomentImages(momentId: string) {
  if (!momentId) {
    momentImages.value = []
    return
  }

  momentImagesLoading.value = true
  try {
    momentImages.value = await fetchMomentImages(momentId)
  } catch (error) {
    momentImages.value = []
    ElMessage.error(getApiErrorMessage(error, '加载动态图片失败'))
  } finally {
    momentImagesLoading.value = false
  }
}

async function ensureMomentDraftForImageUpload(): Promise<string> {
  if (currentEditorMomentId.value) {
    return currentEditorMomentId.value
  }

  const draft = await store.saveDraft({
    title: draftForm.value.title,
    content: draftForm.value.content,
  })
  return draft.id
}

let saveTimeout: number | null = null

function autoSave() {
  if (isEditingPublishedMoment.value) {
    if (saveTimeout) {
      window.clearTimeout(saveTimeout)
      saveTimeout = null
    }
    return
  }
  if (saveTimeout) {
    window.clearTimeout(saveTimeout)
  }
  saveTimeout = window.setTimeout(async () => {
    if (isEditingPublishedMoment.value) {
      return
    }
    if (draftForm.value.content.trim() || draftForm.value.title.trim()) {
      await store.saveDraft({
        title: draftForm.value.title,
        content: draftForm.value.content,
      })
    }
  }, 1000)
}

const showMomentsSkeleton = computed(() => momentsInitialLoading.value && store.moments.length === 0)

async function loadMoments(page = 1, options: { silent?: boolean } = {}) {
  const silent = options.silent ?? !momentsInitialLoading.value
  if (silent) {
    momentsRefreshing.value = true
  } else {
    momentsInitialLoading.value = true
  }
  try {
    await store.fetchMyMoments(page, isRecycleBinMode.value)
  } finally {
    if (silent) {
      momentsRefreshing.value = false
    } else {
      momentsInitialLoading.value = false
    }
  }
}

async function handleSaveDraft() {
  if (isEditingPublishedMoment.value) {
    await handleUpdateMoment()
    return
  }
  if (!draftForm.value.content.trim()) {
    ElMessage.warning('内容不能为空')
    return
  }
  await store.saveDraft({
    title: draftForm.value.title,
    content: draftForm.value.content,
  })
  ElMessage.success('草稿已保存')
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
    await store.publish({
      title: draftForm.value.title,
      content: draftForm.value.content,
    })
    ElMessage.success('发布成功')
    draftForm.value = { title: '', content: '' }
    momentImages.value = []
    momentImagesExpanded.value = false
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '发布失败'))
  }
}

async function handleUpdateMoment() {
  if (!editingMoment.value) {
    return
  }
  if (!draftForm.value.content.trim()) {
    ElMessage.warning('内容不能为空')
    return
  }
  if (isOverLimit.value) {
    ElMessage.warning('内容超过1000字限制')
    return
  }
  try {
    await store.updateMoment(editingMoment.value.id, {
      title: draftForm.value.title,
      content: draftForm.value.content,
    })
    ElMessage.success('动态已更新')
    editingMoment.value = null
    await loadDraft()
    await loadMoments(Math.max(store.page, 1), { silent: true })
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '更新动态失败'))
  }
}

async function handleClearDraft() {
  try {
    await ElMessageBox.confirm('确定要清空草稿吗？', '确认', { type: 'warning' })
    if (currentMomentDraftId.value && momentImages.value.length > 0) {
      await Promise.allSettled(
        momentImages.value.map((image) => deleteMomentImage(currentMomentDraftId.value, image.id)),
      )
    }
    draftForm.value = { title: '', content: '' }
    await store.saveDraft({ title: '', content: '' })
    momentImages.value = []
    momentImagesExpanded.value = false
    ElMessage.success('草稿已清空')
  } catch {
  }
}

async function handleEditMoment(moment: UserMoment) {
  if (saveTimeout) {
    window.clearTimeout(saveTimeout)
    saveTimeout = null
  }
  editingMoment.value = moment
  draftForm.value = {
    title: moment.title || '',
    content: moment.content,
  }
  momentImagesExpanded.value = moment.images.length > 0
  await loadMomentImages(moment.id)
}

async function handleCancelEditing() {
  if (saveTimeout) {
    window.clearTimeout(saveTimeout)
    saveTimeout = null
  }
  editingMoment.value = null
  await loadDraft()
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
      await uploadMomentImage(momentId, file)
    }
    await loadMomentImages(momentId)
    ElMessage.success(`已上传 ${filesToUpload.length} 张图片`)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '图片上传失败'))
  } finally {
    momentImagesUploading.value = false
  }
}

async function handleMomentImageDelete(imageId: string) {
  if (!currentEditorMomentId.value) {
    return
  }

  try {
    await deleteMomentImage(currentEditorMomentId.value, imageId)
    momentImages.value = momentImages.value.filter((image) => image.id !== imageId)
    ElMessage.success('图片已删除')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '删除图片失败'))
  }
}

async function handleMomentImageReorder(imageIds: string[]) {
  if (!currentEditorMomentId.value) {
    return
  }

  try {
    momentImages.value = await reorderMomentImages(currentEditorMomentId.value, imageIds)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '图片排序失败'))
  }
}

function 获取动态图片预览地址(image: MomentImageRecord) {
  return resolveManagedFileUrl(image.thumbnail_url || image.preview_url || image.url)
}

async function handleDelete(id: string) {
  try {
    await store.deleteMoment(id, isRecycleBinMode.value)
    ElMessage.success(isRecycleBinMode.value ? '已永久删除' : '已移入回收站')
    await loadMoments(Math.max(store.page, 1), { silent: true })
  } catch {
    ElMessage.error(isRecycleBinMode.value ? '删除动态失败' : '移入回收站失败')
  }
}

async function handleRestore(id: string) {
  try {
    await store.restoreMoment(id)
    ElMessage.success('已恢复动态')
    await loadMoments(Math.max(store.page, 1), { silent: true })
  } catch {
    ElMessage.error('恢复动态失败')
  }
}

function formatDate(date: string) {
  return new Date(date).toLocaleString('zh-CN')
}

async function handlePageChange(p: number) {
  await loadMoments(p, { silent: true })
}

function handleListModeChange() {
  void loadMoments(1, { silent: false })
}

onMounted(() => {
  void loadDraft()
  void loadMoments()
})

onBeforeUnmount(() => {
  if (saveTimeout) {
    window.clearTimeout(saveTimeout)
    saveTimeout = null
  }
})
</script>

<template>
  <div class="page-container">
    <h2 style="display: flex; align-items: center; gap: 8px; margin-bottom: 24px">
      <ElIcon><ChatDotRound /></ElIcon>
      <span>动态管理</span>
    </h2>

    <ElCard shadow="hover" style="margin-bottom: 24px">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span style="font-weight: 500">
            <ElIcon><DocumentChecked /></ElIcon>
            {{ isEditingPublishedMoment ? '编辑已发布动态' : '写动态（草稿自动保存）' }}
          </span>
          <ElSpace>
            <ElTooltip :content="isEditingPublishedMoment ? '退出当前编辑并回到草稿' : '自动获取上次未发布的内容'">
              <ElButton text :icon="RefreshLeft" :loading="loadingDraft" @click="isEditingPublishedMoment ? handleCancelEditing() : loadDraft()">
                {{ isEditingPublishedMoment ? '回到草稿' : '刷新草稿' }}
              </ElButton>
            </ElTooltip>
          </ElSpace>
        </div>
      </template>

      <ElSkeleton :loading="loadingDraft" animated>
        <ElForm label-position="top">
          <ElFormItem label="标题（可选）">
            <ElInput
              v-model="draftForm.title"
              placeholder="给你的动态起个标题..."
              maxlength="100"
              show-word-limit
              @input="autoSave"
            />
          </ElFormItem>

          <ElFormItem label="内容 (Markdown)">
            <ElInput
              v-model="draftForm.content"
              type="textarea"
              placeholder="在此编写 Markdown 内容，最多1000字..."
              :rows="8"
              style="font-family: 'Fira Code', monospace"
              @input="autoSave"
            />
            <div style="display: flex; justify-content: flex-end; margin-top: 4px">
              <ElTag :type="isOverLimit ? 'danger' : 'info'" size="small">
                {{ contentLength }} / 1000 字
              </ElTag>
            </div>
          </ElFormItem>

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

          <ElSpace>
            <ElButton
              type="primary"
              :disabled="isOverLimit || !draftForm.content.trim()"
              @click="isEditingPublishedMoment ? handleUpdateMoment() : handlePublish()"
            >
              <ElIcon><Plus /></ElIcon>
              {{ isEditingPublishedMoment ? '保存修改' : '发布' }}
            </ElButton>
            <ElButton v-if="!isEditingPublishedMoment" :loading="store.saving" @click="handleSaveDraft">
              保存草稿
            </ElButton>
            <ElButton v-else @click="handleCancelEditing">
              取消编辑
            </ElButton>
            <ElPopconfirm
              v-if="!isEditingPublishedMoment"
              title="确定要清空草稿吗？"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="handleClearDraft"
            >
              <template #reference>
                <ElButton>清空</ElButton>
              </template>
            </ElPopconfirm>
          </ElSpace>
        </ElForm>
      </ElSkeleton>
    </ElCard>

    <ElCard shadow="hover">
      <template #header>
        <span style="font-weight: 500">已发布的动态</span>
      </template>

      <ElSkeleton :loading="showMomentsSkeleton" animated :rows="3">
        <ElTabs v-model="currentListMode" @tab-change="handleListModeChange">
          <ElTabPane label="已发布" name="active" />
          <ElTabPane label="回收站" name="deleted" />
        </ElTabs>

        <div v-if="store.moments.length === 0" v-loading="momentsRefreshing">
          <ElEmpty :description="momentsEmptyDescription" />
        </div>

        <div v-else v-loading="momentsRefreshing">
          <div
            v-for="moment in store.moments"
            :key="moment.id"
            style="
              padding: 16px;
              border-bottom: 1px solid var(--el-border-color-lighter);
              display: flex;
              align-items: flex-start;
              justify-content: space-between;
              gap: 16px;
            "
          >
            <div style="flex: 1; min-width: 0">
              <div style="font-weight: 500; margin-bottom: 8px; font-size: 16px">
                {{ moment.title || '无标题' }}
              </div>
              <div
                style="
                  color: var(--el-text-color-regular);
                  font-size: 14px;
                  line-height: 1.6;
                  margin-bottom: 8px;
                  white-space: pre-wrap;
                  word-break: break-word;
                "
              >
                {{ moment.content.length > 200 ? moment.content.slice(0, 200) + '...' : moment.content }}
              </div>
              <div v-if="moment.images.length > 0" style="display: flex; gap: 8px; overflow-x: auto; margin-bottom: 8px">
                <img
                  v-for="image in moment.images.slice(0, 3)"
                  :key="image.id"
                  :src="获取动态图片预览地址(image)"
                  :alt="image.original_name"
                  style="width: 72px; height: 72px; border-radius: 12px; object-fit: cover; flex: 0 0 auto"
                >
              </div>
              <div style="color: var(--el-text-color-secondary); font-size: 12px">
                {{ isRecycleBinMode ? '删除于' : '发布于' }} {{ formatDate(isRecycleBinMode ? moment.deleted_at! : moment.published_at!) }}
              </div>
              <div style="color: var(--el-text-color-secondary); font-size: 12px; margin-top: 4px">
                浏览 {{ moment.view_count }} · 点赞 {{ moment.like_count }}
              </div>
            </div>

            <ElSpace>
              <ElButton v-if="!isRecycleBinMode" text :icon="Edit" size="small" @click="handleEditMoment(moment)">
                重新编辑
              </ElButton>
              <ElButton v-if="isRecycleBinMode" text size="small" @click="handleRestore(moment.id)">
                恢复
              </ElButton>
              <ElPopconfirm
                :title="isRecycleBinMode ? '确定要永久删除这条动态吗？' : '确定要删除这条动态吗？'"
                confirm-button-text="确定"
                cancel-button-text="取消"
                @confirm="handleDelete(moment.id)"
              >
                <template #reference>
                  <ElButton type="danger" text :icon="Delete" size="small">
                    {{ isRecycleBinMode ? '彻底删除' : '删除' }}
                  </ElButton>
                </template>
              </ElPopconfirm>
            </ElSpace>
          </div>

          <div v-if="store.pages > 1" style="display: flex; justify-content: center; margin-top: 16px">
            <ElPagination
              :current-page="store.page"
              :page-size="10"
              :total="store.total"
              layout="prev, pager, next"
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </ElSkeleton>
    </ElCard>
  </div>
</template>

<style scoped>
.page-container {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

:deep(.el-card__header) {
  padding: 12px 16px;
  background-color: var(--el-fill-color-light);
}

.dark :deep(.el-card__header) {
  background-color: var(--el-fill-color-darker);
}
</style>
