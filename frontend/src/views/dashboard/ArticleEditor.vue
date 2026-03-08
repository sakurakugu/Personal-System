<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton, NInput, NSelect, NSpace, NForm, NFormItem, NSpin, useMessage,
} from 'naive-ui'
import api from '../../utils/api'

const route = useRoute()
const router = useRouter()
const message = useMessage()

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
      // We need to fetch by ID; use slug lookup or direct
      const { data } = await api.get(`/articles/my/list`, { params: { page: 1, page_size: 100 } })
      const article = data.items.find((a: any) => a.id === id)
      if (article) {
        // Get full content
        const { data: full } = await api.get(`/articles/${article.slug}`)
        form.value = {
          title: full.title,
          content: full.content,
          excerpt: full.excerpt || '',
          cover_url: full.cover_url || '',
          status: full.status,
          category_id: full.category?.id || null,
          tag_ids: full.tags.map((t: any) => t.id),
        }
      }
    } finally {
      loading.value = false
    }
  }
})

async function save() {
  if (!form.value.title.trim()) {
    message.warning('请填写标题')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await api.patch(`/articles/${route.params.id}`, form.value)
      message.success('更新成功')
    } else {
      await api.post('/articles', form.value)
      message.success('创建成功')
    }
    router.push('/dashboard/articles')
  } catch (e: any) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <h2 style="margin-bottom: 24px">{{ isEdit ? '✏️ 编辑文章' : '📝 写文章' }}</h2>
    <NSpin :show="loading">
      <NForm label-placement="top">
        <NFormItem label="标题">
          <NInput v-model:value="form.title" placeholder="文章标题" />
        </NFormItem>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px">
          <NFormItem label="分类">
            <NSelect v-model:value="form.category_id" :options="categories" placeholder="选择分类" clearable />
          </NFormItem>
          <NFormItem label="标签">
            <NSelect v-model:value="form.tag_ids" :options="tags" placeholder="选择标签" multiple clearable />
          </NFormItem>
        </div>

        <NFormItem label="封面图 URL">
          <NInput v-model:value="form.cover_url" placeholder="https://..." />
        </NFormItem>

        <NFormItem label="摘要">
          <NInput v-model:value="form.excerpt" type="textarea" placeholder="文章摘要（可选）" :rows="2" />
        </NFormItem>

        <NFormItem label="正文 (Markdown)">
          <NInput
            v-model:value="form.content"
            type="textarea"
            placeholder="在此编写 Markdown 内容..."
            :rows="20"
            style="font-family: 'Fira Code', monospace"
          />
        </NFormItem>

        <NFormItem label="状态">
          <NSelect
            v-model:value="form.status"
            :options="[{ label: '草稿', value: 'draft' }, { label: '发布', value: 'published' }]"
            style="width: 150px"
          />
        </NFormItem>

        <NSpace>
          <NButton type="primary" :loading="saving" @click="save">
            {{ isEdit ? '更新' : '发布' }}
          </NButton>
          <NButton @click="router.back()">取消</NButton>
        </NSpace>
      </NForm>
    </NSpin>
  </div>
</template>
