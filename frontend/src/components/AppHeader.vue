<script setup lang="ts">
import { ElAvatar, ElButton, ElDropdown, ElDropdownItem, ElDropdownMenu, ElIcon, ElInput, ElOption, ElSelect } from 'element-plus'
import { HomeFilled, Search } from '@element-plus/icons-vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useArticleStore } from '../stores/article'
import api from '../utils/api'

const emit = defineEmits<{ 'show-login': [] }>()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const articleStore = useArticleStore()

const search = ref('')
const categoryFilter = ref<string | null>(null)
const categories = ref<{ id: string; name: string; slug: string }[]>([])
const categoryOptions = ref<{ label: string; value: string }[]>([])

// 获取分类列表
async function fetchCategories() {
  try {
    const { data } = await api.get('/categories')
    categories.value = data
  } catch {
    categories.value = []
  }
}

// 从 URL 同步搜索参数
function syncFromUrl() {
  const query = route.query
  search.value = (query.search as string) || ''
  categoryFilter.value = (query.category as string) || null
}

// 执行搜索
function doSearch() {
  const query: Record<string, string> = {}
  if (search.value) query.search = search.value
  if (categoryFilter.value) query.category = categoryFilter.value

  // 如果已经在博客首页，直接更新文章列表
  if (route.path === '/blog' || route.path === '/') {
    articleStore.fetchArticles(1, query)
    // 更新 URL 但不跳转
    router.replace({ path: '/blog', query: Object.keys(query).length ? query : undefined })
  } else {
    // 跳转到博客首页并带搜索参数
    router.push({ path: '/blog', query: Object.keys(query).length ? query : undefined })
  }
}

watch(categories, (cats) => {
  categoryOptions.value = [
    { label: '全部分类', value: '' },
    ...cats.map(c => ({ label: c.name, value: c.slug })),
  ]
}, { immediate: true })

onMounted(() => {
  fetchCategories()
  syncFromUrl()
})

const isAuthed = computed(() => auth.isAuthenticated)
const displayName = computed(() => auth.user?.nickname || auth.user?.username || '')

const menuOptions = computed(() => {
  const items = [
    { label: '个人资料', key: 'profile' },
    { label: '个人看板', key: 'dashboard' },
    { label: '我的文章', key: 'articles' },
    { label: '我的待办', key: 'todos' },
    { type: 'divider' as const, key: 'd1', label: '' },
    { label: '退出登录', key: 'logout' },
  ]
  if (auth.isAdmin) {
    items.splice(3, 0, { label: '系统状态', key: 'system' })
  }
  if (auth.isSuperAdmin) {
    items.splice(4, 0, { label: '用户管理', key: 'users' })
    items.splice(5, 0, { label: '系统设置', key: 'settings' })
  }
  return items
})

function handleMenu(key: string) {
  switch (key) {
    case 'profile': router.push('/dashboard/profile'); break
    case 'dashboard': router.push('/dashboard'); break
    case 'articles': router.push('/dashboard/articles'); break
    case 'todos': router.push('/dashboard/todos'); break
    case 'system': router.push('/dashboard/system'); break
    case 'users': router.push('/dashboard/users'); break
    case 'settings': router.push('/dashboard/settings'); break
    case 'logout':
      auth.logout()
      router.push('/blog')
      break
  }
}
</script>

<template>
  <header class="app-header">
    <div class="header-inner">
      <router-link to="/blog" class="logo">
        <ElIcon><HomeFilled /></ElIcon>
        <span>Sakurakuguの小窝</span>
      </router-link>

      <nav class="nav-links">
        <router-link to="/blog">首页</router-link>
      </nav>

      <!-- 搜索栏 -->
      <div class="header-search">
        <ElInput
          v-model="search"
          placeholder="搜索文章..."
          clearable
          :prefix-icon="Search"
          @keyup.enter="doSearch"
          @clear="doSearch"
        />
        <ElSelect
          v-model="categoryFilter"
          placeholder="分类"
          clearable
          @change="doSearch"
        >
          <ElOption v-for="item in categoryOptions" :key="item.value" :label="item.label" :value="item.value" />
        </ElSelect>
      </div>

      <!-- 占位元素，用于平衡布局让搜索栏居中 -->
      <div class="header-spacer"></div>
      <div class="header-right">
        <template v-if="isAuthed">
          <ElDropdown trigger="click" @command="handleMenu">
            <ElButton circle text>
              <ElAvatar size="small" :style="{ backgroundColor: '#18a058' }">
                {{ displayName.charAt(0).toUpperCase() }}
              </ElAvatar>
            </ElButton>
            <template #dropdown>
              <ElDropdownMenu>
                <template v-for="item in menuOptions" :key="item.key">
                  <ElDropdownItem v-if="item.type === 'divider'" divided />
                  <ElDropdownItem v-else :command="item.key">
                    {{ item.label }}
                  </ElDropdownItem>
                </template>
              </ElDropdownMenu>
            </template>
          </ElDropdown>
        </template>
        <template v-else>
          <ElButton type="primary" size="small" @click="emit('show-login')">
            登录
          </ElButton>
        </template>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 16px;
  height: 56px;
  display: flex;
  align-items: center;
  gap: 24px;
}

.logo {
  font-size: 20px;
  font-weight: 700;
  color: #18a058 !important;
  text-decoration: none !important;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.nav-links {
  display: flex;
  gap: 16px;
  width: 120px;
}

.header-search {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

.header-search :deep(.el-input) {
  width: 260px;
}

.header-search :deep(.el-select) {
  width: 120px;
}

.header-spacer {
  width: 260px;
  display: flex;
  justify-content: flex-end;
}

.nav-links a {
  color: #555;
  font-size: 14px;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  color: #18a058;
}

.header-right {
  display: flex;
  align-items: center;
}
</style>
