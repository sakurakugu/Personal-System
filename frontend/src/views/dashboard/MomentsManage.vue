<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import {
  ElButton, ElCard, ElEmpty, ElForm, ElFormItem, ElIcon, ElInput, ElMessage, ElMessageBox,
  ElPagination, ElPopconfirm, ElSpace, ElSkeleton, ElTag, ElTooltip,
} from 'element-plus'
import { ChatDotRound, Delete, DocumentChecked, Plus, RefreshLeft } from '@element-plus/icons-vue'
import { useMomentStore } from '../../stores/moment'

const store = useMomentStore()

// 草稿表单
const draftForm = ref({
  title: '',
  content: '',
})

const loadingDraft = ref(false)

// 计算字数
const contentLength = computed(() => draftForm.value.content.length)
const isOverLimit = computed(() => contentLength.value > 1000)

// 获取草稿
async function loadDraft() {
  loadingDraft.value = true
  try {
    const draft = await store.fetchDraft()
    if (draft) {
      draftForm.value.title = draft.title || ''
      draftForm.value.content = draft.content
    }
  } finally {
    loadingDraft.value = false
  }
}

// 自动保存草稿（防抖）
let saveTimeout: ReturnType<typeof window.setTimeout> | null = null
function autoSave() {
  if (saveTimeout) window.clearTimeout(saveTimeout)
  saveTimeout = window.setTimeout(async () => {
    // 只有有内容时才自动保存
    if (draftForm.value.content.trim() || draftForm.value.title.trim()) {
      await store.saveDraft({
        title: draftForm.value.title,
        content: draftForm.value.content,
      })
    }
  }, 1000)
}

// 手动保存草稿
async function handleSaveDraft() {
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

// 发布动态
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
    // 清空表单
    draftForm.value = { title: '', content: '' }
    // 刷新列表
    await store.fetchMyMoments()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '发布失败')
  }
}

// 清空草稿
async function handleClearDraft() {
  try {
    await ElMessageBox.confirm('确定要清空草稿吗？', '确认', { type: 'warning' })
    draftForm.value = { title: '', content: '' }
    // 保存空草稿（相当于删除）
    await store.saveDraft({ title: '', content: '' })
    ElMessage.success('草稿已清空')
  } catch {
    // 用户取消
  }
}

// 删除动态
async function handleDelete(id: string) {
  try {
    await ElMessageBox.confirm('确定要删除这条动态吗？', '确认', { type: 'warning' })
    await store.deleteMoment(id)
    ElMessage.success('删除成功')
  } catch {
    // 用户取消
  }
}

// 格式化日期
function formatDate(date: string) {
  return new Date(date).toLocaleString('zh-CN')
}

// 分页
async function handlePageChange(p: number) {
  await store.fetchMyMoments(p)
}

onMounted(() => {
  loadDraft()
  store.fetchMyMoments()
})
</script>

<template>
  <div class="page-container">
    <h2 style="display: flex; align-items: center; gap: 8px; margin-bottom: 24px">
      <ElIcon><ChatDotRound /></ElIcon>
      <span>动态管理</span>
    </h2>

    <!-- 草稿编辑区 -->
    <ElCard shadow="hover" style="margin-bottom: 24px">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span style="font-weight: 500">
            <ElIcon><DocumentChecked /></ElIcon>
            写动态（草稿自动保存）
          </span>
          <ElSpace>
            <ElTooltip content="自动获取上次未发布的内容">
              <ElButton text :icon="RefreshLeft" :loading="loadingDraft" @click="loadDraft">
                刷新草稿
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

          <ElSpace>
            <ElButton type="primary" :disabled="isOverLimit || !draftForm.content.trim()" @click="handlePublish">
              <ElIcon><Plus /></ElIcon>
              发布
            </ElButton>
            <ElButton :loading="store.saving" @click="handleSaveDraft">
              保存草稿
            </ElButton>
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
          </ElSpace>
        </ElForm>
      </ElSkeleton>
    </ElCard>

    <!-- 已发布动态列表 -->
    <ElCard shadow="hover">
      <template #header>
        <span style="font-weight: 500">已发布的动态</span>
      </template>

      <ElSkeleton :loading="store.loading" animated :rows="3">
        <div v-if="store.moments.length === 0">
          <ElEmpty description="还没有发布过动态" />
        </div>

        <div v-else>
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
              <div style="color: var(--el-text-color-secondary); font-size: 12px">
                发布于 {{ formatDate(moment.published_at!) }}
              </div>
            </div>

            <ElPopconfirm
              title="确定要删除这条动态吗？"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="handleDelete(moment.id)"
            >
              <template #reference>
                <ElButton type="danger" text :icon="Delete" size="small">
                  删除
                </ElButton>
              </template>
            </ElPopconfirm>
          </div>

          <!-- 分页 -->
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
