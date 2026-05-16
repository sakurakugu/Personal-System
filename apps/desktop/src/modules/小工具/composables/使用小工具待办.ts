import { 获取公开小工具摘要 } from '@/shared/widget-summary'
import { 获取已配置的活跃基地址 } from '@personal-system/api'
import { 使用认证存储 } from '@personal-system/domain/auth'
import { type Todo, 使用待办存储 } from '@personal-system/domain/todos'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'

function 映射摘要项到待办(item: {
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

export function 使用小工具待办() {
  const todoStore = 使用待办存储()
  const auth = 使用认证存储()
  const loading = ref(false)
  const loadedOnce = ref(false)
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

  function 格式化截止日期(value: string | null) {
    if (!value) {
      return '无截止日期'
    }
    return value.slice(0, 10)
  }

  function 是否已逾期(value: string | null) {
    return Boolean(value && value < new Date().toISOString().slice(0, 10))
  }

  async function 加载待办() {
    loading.value = true
    try {
      if (auth.isAuthenticated) {
        await todoStore.fetchTodos()
        return
      }
      const summary = await 获取公开小工具摘要({
        apiBaseUrl: 获取已配置的活跃基地址(),
      })
      todoStore.todos = summary.items.map(映射摘要项到待办)
    } catch (error) {
      console.error('加载待办失败', error)
      ElMessage.error('加载待办失败')
    } finally {
      loadedOnce.value = true
      loading.value = false
    }
  }

  async function 创建待办() {
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

  async function 处理切换完成(id: string) {
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

  async function 处理切换置顶(id: string) {
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
    void 加载待办()
  })

  return {
    creatingTodo,
    loadedOnce,
    loading,
    orderedTodos,
    todoDraft,
    createTodo: 创建待办,
    formatEndDate: 格式化截止日期,
    handleToggleComplete: 处理切换完成,
    handleTogglePin: 处理切换置顶,
    isOverdue: 是否已逾期,
    loadTodos: 加载待办,
  }
}
