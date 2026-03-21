<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ElButton, ElForm, ElFormItem, ElIcon, ElInput, ElMessage, ElOption, ElSelect, ElSkeleton, ElSpace,
} from 'element-plus'
import { EditPen, DocumentAdd } from '@element-plus/icons-vue'
import api from '../../utils/api'

const route = useRoute()
const router = useRouter()

const isEdit = ref(false)
const loading = ref(false)
const saving = ref(false)

const form = ref({
  title: '',
  content: '',
  excerpt: '',
  cover_url: '',
  status: 'draft',
  category_id: null as string | null,
  tag_ids: [] as string[],
})

const categories = ref<{ label: string; value: string }[]>([])
const tags = ref<{ label: string; value: string }[]>([])

onMounted(async () => {
  // Fetch categories and tags
  const [catRes, tagRes] = await Promise.all([
    api.get('/categories'),
    api.get('/tags'),
  ])
  categories.value = catRes.data.map((c: any) => ({ label: c.name, value: c.id }))
  tags.value = tagRes.data.map((t: any) => ({ label: t.name, value: t.id }))

  // If editing existing article
  const id = route.params.id as string
  if (id) {
    isEdit.value = true
    loading.value = true
    try {
      // Use the new endpoint to get article by ID (supports both draft and published)
      const { data: full } = await api.get(`/articles/my/${id}`)
      form.value = {
        title: full.title,
        content: full.content,
        excerpt: full.excerpt || '',
        cover_url: full.cover_url || '',
        status: full.status,
        category_id: full.category?.id || null,
        tag_ids: full.tags.map((t: any) => t.id),
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
      await api.patch(`/articles/${route.params.id}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await api.post('/articles', form.value)
      ElMessage.success('创建成功')
    }
    router.push('/dashboard/articles')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
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
          <ElInput
            v-model="form.content"
            type="textarea"
            placeholder="在此编写 Markdown 内容..."
            :rows="20"
            style="font-family: 'Fira Code', monospace"
          />
        </ElFormItem>

        <ElFormItem label="状态">
          <ElSelect v-model="form.status" style="width: 150px">
            <ElOption label="草稿" value="draft" />
            <ElOption label="发布" value="published" />
          </ElSelect>
        </ElFormItem>

        <ElSpace>
          <ElButton type="primary" :loading="saving" @click="save">
            {{ isEdit ? '更新' : '发布' }}
          </ElButton>
          <ElButton @click="router.back()">取消</ElButton>
        </ElSpace>
      </ElForm>
    </ElSkeleton>
  </div>
</template>
