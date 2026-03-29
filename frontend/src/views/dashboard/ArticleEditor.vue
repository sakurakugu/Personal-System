<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ElButton, ElForm, ElFormItem, ElIcon, ElInput, ElMessage, ElOption, ElRadioButton, ElRadioGroup, ElSelect, ElSkeleton,
} from 'element-plus'
import { EditPen, DocumentAdd } from '@element-plus/icons-vue'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import {
  createArticle,
  fetchCategories,
  fetchMyArticleById,
  fetchTags,
  updateArticle,
} from '../../features/articles/api'
import type { ArticleEditorPayload } from '../../features/articles/types'
import { useThemeStore } from '../../stores/theme'
import { getApiErrorMessage } from '../../utils/api'

const route = useRoute()
const router = useRouter()
const themeStore = useThemeStore()

const isEdit = ref(false)
const loading = ref(false)
const saving = ref(false)
const editorId = 'article-editor'
const editorTheme = computed(() => (themeStore.isDark ? 'dark' : 'light'))

interface SelectOption {
  label: string
  value: string
}

const form = ref<ArticleEditorPayload>({
  title: '',
  content: '',
  excerpt: '',
  cover_url: '',
  status: 'private',
  category_id: null as string | null,
  tag_ids: [] as string[],
})

const categories = ref<SelectOption[]>([])
const tags = ref<SelectOption[]>([])

onMounted(async () => {
  const [categoryRecords, tagRecords] = await Promise.all([
    fetchCategories(),
    fetchTags(),
  ])
  categories.value = categoryRecords.map((category) => ({ label: category.name, value: category.id }))
  tags.value = tagRecords.map((tag) => ({ label: tag.name, value: tag.id }))

  const id = route.params.id as string
  if (id) {
    isEdit.value = true
    loading.value = true
    try {
      const full = await fetchMyArticleById(id)
      form.value = {
        title: full.title,
        content: full.content,
        excerpt: full.excerpt || '',
        cover_url: full.cover_url || '',
        status: full.status,
        category_id: full.category?.id || null,
        tag_ids: full.tags.map((tag) => tag.id),
      }
    } finally {
      loading.value = false
    }
  }
})

async function save() {
  if (!form.value.title.trim()) {
    ElMessage.warning('请填写标题')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await updateArticle(String(route.params.id), form.value)
      ElMessage.success('更新成功')
    } else {
      await createArticle(form.value)
      ElMessage.success('创建成功')
    }
    router.push('/dashboard/articles')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '保存失败'))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <h2 style="display: flex; align-items: center; gap: 8px; margin-bottom: 24px">
      <ElIcon><component :is="isEdit ? EditPen : DocumentAdd" /></ElIcon>
      <span>{{ isEdit ? '编辑文章' : '写文章' }}</span>
    </h2>
    <ElSkeleton :loading="loading" animated>
      <ElForm label-position="top">
        <ElFormItem label="标题">
          <ElInput v-model="form.title" placeholder="文章标题" />
        </ElFormItem>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px">
          <ElFormItem label="分类">
            <ElSelect v-model="form.category_id" placeholder="选择分类" clearable>
              <ElOption v-for="item in categories" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="标签">
            <ElSelect v-model="form.tag_ids" placeholder="选择标签" multiple clearable>
              <ElOption v-for="item in tags" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
        </div>

        <ElFormItem label="封面图 URL">
          <ElInput v-model="form.cover_url" placeholder="https://..." />
        </ElFormItem>

        <ElFormItem label="摘要">
          <ElInput v-model="form.excerpt" type="textarea" placeholder="文章摘要（可选）" :rows="2" />
        </ElFormItem>

        <ElFormItem label="正文 (Markdown)">
          <div class="editor-wrapper">
            <MdEditor
              :id="editorId"
              v-model="form.content"
              class="article-md-editor"
              :theme="editorTheme"
              preview-theme="github"
              code-theme="github"
              language="zh-CN"
              placeholder="在此编写 Markdown 内容..."
              :toolbars-exclude="['github', 'save', 'catalog']"
            />
          </div>
        </ElFormItem>

        <div class="article-editor-actions">
          <ElFormItem label="状态" class="article-editor-status">
            <ElRadioGroup v-model="form.status">
              <ElRadioButton value="private">私有</ElRadioButton>
              <ElRadioButton value="login_required">登录可见</ElRadioButton>
              <ElRadioButton value="public">公开</ElRadioButton>
            </ElRadioGroup>
          </ElFormItem>

          <div class="article-editor-buttons">
            <ElButton type="primary" :loading="saving" @click="save">
              {{ isEdit ? '更新' : '创建' }}
            </ElButton>
            <ElButton @click="router.back()">取消</ElButton>
          </div>
        </div>
      </ElForm>
    </ElSkeleton>
  </div>
</template>

<style scoped>
.page-container {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

.editor-wrapper {
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  background: transparent;
}

.article-md-editor {
  width: 100%;
  height: 720px;
}

.article-md-editor:deep(.md-editor) {
  width: 100%;
  border: none;
  background: transparent;
  border-radius: 12px;
}

.article-md-editor:deep(.md-editor-toolbar),
.article-md-editor:deep(.md-editor-footer) {
  background: var(--el-bg-color-overlay);
  color: var(--el-text-color-primary);
}

.article-md-editor:deep(.md-editor-toolbar) {
  border: none;
}

.article-md-editor:deep(.md-editor-toolbar-wrapper) {
  background: var(--el-bg-color-overlay);
}

.article-md-editor:deep(.md-editor-toolbar svg),
.article-md-editor:deep(.md-editor-footer svg) {
  color: var(--el-text-color-primary);
}

.article-md-editor:deep(.md-editor-toolbar-item),
.article-md-editor:deep(.md-editor-toolbar-item button),
.article-md-editor:deep(.md-editor-toolbar-item span),
.article-md-editor:deep(.md-editor-toolbar-item i) {
  color: var(--el-text-color-primary);
}

.article-md-editor:deep(.md-editor-content) {
  display: flex;
  width: 100%;
  min-width: 0;
  border-inline: none;
}

.article-md-editor:deep(.md-editor-footer) {
  display: flex;
  align-items: center;
  min-height: 24px;
  border: none;
  border-bottom-right-radius: 12px;
  border-bottom-left-radius: 12px;
}

.article-md-editor:deep(.md-editor-footer-left),
.article-md-editor:deep(.md-editor-footer-right) {
  display: flex;
  align-items: center;
}

.article-md-editor:deep(.md-editor-input-wrapper),
.article-md-editor:deep(.md-editor-preview-wrapper) {
  flex: 1 1 0;
  min-width: 0;
}

.article-md-editor:deep(.md-editor-footer-item) {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding-block: 0;
}

.article-md-editor:deep(.md-editor-footer-label) {
  display: inline-flex;
  align-items: center;
}

.article-md-editor:deep(.md-editor-footer-left),
.article-md-editor:deep(.md-editor-footer-right),
.article-md-editor:deep(.md-editor-footer-item span),
.article-md-editor:deep(.md-editor-footer-label) {
  color: var(--el-text-color-secondary);
  line-height: 1;
}

.article-md-editor:deep(.md-editor-input-wrapper),
.article-md-editor:deep(.md-editor-preview-wrapper) {
  font-size: 14px;
}

.article-editor-actions {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.article-editor-status {
  margin-bottom: 0;
}

.article-editor-buttons {
  display: flex;
  align-items: center;
  gap: 12px;
}

:global(.dark) .article-md-editor:deep(.md-editor-toolbar-item),
:global(.dark) .article-md-editor:deep(.md-editor-toolbar-item button),
:global(.dark) .article-md-editor:deep(.md-editor-toolbar-item span),
:global(.dark) .article-md-editor:deep(.md-editor-toolbar-item i) {
  color: #fff;
}

@media (max-width: 768px) {
  .page-container {
    padding: 16px;
  }

  .article-md-editor {
    height: 560px;
  }

  .article-editor-actions {
    align-items: stretch;
  }

  .article-editor-buttons {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
