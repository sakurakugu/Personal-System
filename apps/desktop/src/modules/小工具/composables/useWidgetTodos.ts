import { fetchPublicWidgetSummary } from '@/shared/widget-summary'
import { getConfiguredActiveBaseUrl } from '@personal-system/api'
import { useAuthStore } from '@personal-system/domain/auth'
import { type Todo, useTodoStore } from '@personal-system/domain/todos'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'

function mapSummaryItemToTodo(item: {
  id: string
  title: string
  importance: number
  urgency: number
  end_date: string | null
  is_pinned: boolean
}): Todo {
  const now = new Date().toISOString()

  return {
    id: String(item.id),
    title: item.title,
    description: null,
    status: 'todo',
    importance: item.importance,
    urgency: item.urgency,
    start_date: null,
    end_date: item.end_date,
    is_pinned: item.is_pinned,
    is_deleted: false,
    deleted_at: null,
    tags: null,
    recurrence_type: 'none',
    recurrence_interval: 1,
    recurrence_count: 0,
    times_per_interval: 1,
    interval_progress: 0,
    progress_reset_at: null,
    created_at: item.end_date ?? now,
    updated_at: item.end_date ?? now,
  }
}

export function useWidgetTodos() {
  const todoStore = useTodoStore()
  const auth = useAuthStore()
  const loading = ref(false)
  const creatingTodo = ref(false)
  const todoDraft = ref('')

  const activeTodos = computed(() => todoStore.todos.filter((todo) => !todo.is_deleted))
  const orderedTodos = computed(() => [...activeTodos.value]
    .filter((todo) => todo.status === 'todo')
    .sort((left, right) => {
      if (left.is_pinned !== right.is_pinned) {
        return left.is_pinned ? -1 : 1
      }
      const leftDate = left.end_date ?? left.created_at
      const rightDate = right.end_date ?? right.created_at
      return String(leftDate).localeCompare(String(rightDate))
    }))

  function formatEndDate(value: string | null) {
    if (!value) {
      return '无截止日期'
    }
    return value.slice(0, 10)
  }

  function isOverdue(value: string | null) {
    return Boolean(value && value < new Date().toISOString().slice(0, 10))
  }

  async function loadTodos() {
    loading.value = true
    try {
      if (auth.isAuthenticated) {
        await todoStore.fetchTodos()
        return
      }
      const summary = await fetchPublicWidgetSummary({
        apiBaseUrl: getConfiguredActiveBaseUrl(),
      })
      todoStore.todos = summary.items.map(mapSummaryItemToTodo)
    } catch (error) {
      console.error('加载待办失败', error)
      ElMessage.error('加载待办失败')
    } finally {
      loading.value = false
    }
  }

  async function createTodo() {
    const title = todoDraft.value.trim()
    if (!title) {
      ElMessage.warning('请输入待办内容')
      return
    }
    if (!auth.isAuthenticated) {
      ElMessage.warning('公开小工具模式下暂不支持新增待办')
      return
    }

    creatingTodo.value = true
    try {
      await todoStore.addTodo({
        title,
        importance: 0,
        urgency: 0,
        recurrence_type: 'none',
        recurrence_interval: 1,
        recurrence_count: 0,
        times_per_interval: 1,
      })
      todoDraft.value = ''
      ElMessage.success('已添加待办')
    } catch (error) {
      console.error('新增待办失败', error)
      ElMessage.error('新增待办失败')
    } finally {
      creatingTodo.value = false
    }
  }

  async function handleToggleComplete(id: string) {
    if (!auth.isAuthenticated) {
      ElMessage.warning('公开小工具模式下暂不支持修改待办')
      return
    }

    try {
      await todoStore.toggleComplete(id)
    } catch (error) {
      console.error('更新待办状态失败', error)
      ElMessage.error('更新待办状态失败')
    }
  }

  async function handleTogglePin(id: string) {
    if (!auth.isAuthenticated) {
      ElMessage.warning('公开小工具模式下暂不支持修改待办')
      return
    }

    try {
      await todoStore.togglePin(id)
    } catch (error) {
      console.error('更新置顶状态失败', error)
      ElMessage.error('更新置顶状态失败')
    }
  }

  onMounted(() => {
    void loadTodos()
  })

  return {
    creatingTodo,
    loading,
    orderedTodos,
    todoDraft,
    createTodo,
    formatEndDate,
    handleToggleComplete,
    handleTogglePin,
    isOverdue,
    loadTodos,
  }
}
