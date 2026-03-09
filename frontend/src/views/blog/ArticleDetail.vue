<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  NCard, NSpace, NTag, NText, NDivider, NButton, NInput, NSpin, NEmpty, useMessage,
} from 'naive-ui'
import { ElIcon } from 'element-plus'
import { View } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import { useArticleStore } from '../../stores/article'
import { useAuthStore } from '../../stores/auth'
import api from '../../utils/api'

const route = useRoute()
const message = useMessage()
const articleStore = useArticleStore()
const auth = useAuthStore()

const md = new MarkdownIt({
  html: true,
  linkify: true,
  highlight(str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try { return hljs.highlight(str, { language: lang }).value } catch {}
    }
    return ''
  },
})

interface Comment {
  id: string
  content: string
  user: { username: string } | null
  guest_name: string | null
  created_at: string
  replies: Comment[]
}

const comments = ref<Comment[]>([])
const newComment = ref('')
const guestName = ref('')
const loadingComment = ref(false)

const renderedContent = computed(() => {
  if (!articleStore.current) return ''
  return md.render(articleStore.current.content)
})

onMounted(async () => {
  const slug = route.params.slug as string
  await articleStore.fetchBySlug(slug)
  if (articleStore.current) {
    await loadComments()
    try { await api.post('/stats/pageview', { path: `/blog/${slug}`, article_id: articleStore.current.id }) } catch {}
  }
})

async function loadComments() {
  if (!articleStore.current) return
  try {
    const { data } = await api.get('/comments', { params: { article_id: articleStore.current.id } })
    comments.value = data
  } catch {}
}

async function submitComment() {
  if (!articleStore.current || !newComment.value.trim()) return
  loadingComment.value = true
  try {
    await api.post('/comments', {
      article_id: articleStore.current.id,
      content: newComment.value,
      guest_name: auth.isAuthenticated ? undefined : (guestName.value || '匿名'),
    })
    newComment.value = ''
    message.success('评论已提交')
    await loadComments()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '评论失败')
  } finally {
    loadingComment.value = false
  }
}
</script>

<template>
  <div class="article-detail">
    <NSpin :show="articleStore.loading">
      <template v-if="articleStore.current">
        <NCard>
          <h1 class="title">{{ articleStore.current.title }}</h1>
          <div class="meta">
            <NSpace size="small" align="center">
              <NText depth="3">{{ articleStore.current.author.username }}</NText>
              <NText depth="3">·</NText>
              <NText depth="3">{{ new Date(articleStore.current.published_at || articleStore.current.created_at).toLocaleDateString() }}</NText>
              <NText depth="3" style="display: inline-flex; align-items: center; gap: 4px">
                <span>·</span>
                <ElIcon><View /></ElIcon>
                <span>{{ articleStore.current.view_count }}</span>
              </NText>
            </NSpace>
            <NSpace size="small" style="margin-top: 8px">
              <NTag v-if="articleStore.current.category" type="info" size="small">{{ articleStore.current.category.name }}</NTag>
              <NTag v-for="tag in articleStore.current.tags" :key="tag.id" size="small">{{ tag.name }}</NTag>
            </NSpace>
          </div>

          <NDivider />

          <div class="markdown-body" v-html="renderedContent" />
        </NCard>

        <!-- 评论区 -->
        <NCard title="评论" style="margin-top: 24px">
          <div v-if="comments.length" class="comment-list">
            <div v-for="c in comments" :key="c.id" class="comment-item">
              <div class="comment-header">
                <NText strong>{{ c.user?.username || c.guest_name || '匿名' }}</NText>
                <NText depth="3" style="font-size: 12px; margin-left: 8px">{{ new Date(c.created_at).toLocaleString() }}</NText>
              </div>
              <p class="comment-content">{{ c.content }}</p>
              <div v-if="c.replies?.length" class="replies">
                <div v-for="r in c.replies" :key="r.id" class="comment-item reply">
                  <div class="comment-header">
                    <NText strong>{{ r.user?.username || r.guest_name || '匿名' }}</NText>
                    <NText depth="3" style="font-size: 12px; margin-left: 8px">{{ new Date(r.created_at).toLocaleString() }}</NText>
                  </div>
                  <p class="comment-content">{{ r.content }}</p>
                </div>
              </div>
            </div>
          </div>
          <NEmpty v-else description="暂无评论，来抢沙发吧！" />

          <NDivider />

          <div class="comment-form">
            <NInput
              v-if="!auth.isAuthenticated"
              v-model:value="guestName"
              placeholder="你的名字（可选）"
              style="margin-bottom: 8px"
            />
            <NInput
              v-model:value="newComment"
              type="textarea"
              placeholder="写下你的评论..."
              :rows="3"
            />
            <NButton
              type="primary"
              style="margin-top: 8px"
              :loading="loadingComment"
              @click="submitComment"
            >
              发表评论
            </NButton>
          </div>
        </NCard>
      </template>
      <NEmpty v-else-if="!articleStore.loading" description="文章不存在" />
    </NSpin>
  </div>
</template>

<style scoped>
.article-detail {
  max-width: 800px;
  margin: 0 auto;
}

.title {
  font-size: 28px;
  margin-bottom: 12px;
}

.meta {
  margin-bottom: 8px;
}

.markdown-body {
  line-height: 1.8;
  font-size: 15px;
}

.markdown-body :deep(pre) {
  background: #f6f8fa;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
}

.markdown-body :deep(code) {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 13px;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
}

.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: 4px;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-item {
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
}

.comment-header {
  margin-bottom: 4px;
}

.comment-content {
  font-size: 14px;
  color: #444;
  margin: 0;
}

.replies {
  margin-top: 12px;
  padding-left: 20px;
  border-left: 2px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reply {
  background: #f0f4f0;
}
</style>
