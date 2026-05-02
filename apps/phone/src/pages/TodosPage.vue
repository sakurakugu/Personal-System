<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useTodoStore } from '@personal-system/domain/todos'

const todoStore = useTodoStore()
const loading = ref(false)
const errorMessage = ref('')

const todos = computed(() => todoStore.todos)

function formatTime(value: string | null): string {
  if (!value) {
    return '未设置时间'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return '时间无效'
  }
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

async function loadTodos() {
  loading.value = true
  errorMessage.value = ''

  try {
    await todoStore.fetchTodos()
  } catch {
    errorMessage.value = '待办加载失败'
  } finally {
    loading.value = false
  }
}

async function toggleTodo(todoId: string, status: 'todo' | 'done') {
  if (status === 'done') {
    await todoStore.uncompleteTodo(todoId)
    return
  }
  await todoStore.completeTodo(todoId)
}

onMounted(() => {
  void loadTodos()
})
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">待办</p>
        <h1 class="page-title">我的待办</h1>
      </div>
      <button class="ghost-button" type="button" :disabled="loading" @click="loadTodos">
        {{ loading ? '刷新中…' : '刷新' }}
      </button>
    </header>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <div v-if="!todos.length && !loading" class="empty-card">
      暂无待办，后续可继续补充手机端新建与筛选能力。
    </div>

    <div v-else class="stack">
      <article v-for="todo in todos" :key="todo.id" class="todo-card" :class="{ 'todo-card--done': todo.status === 'done' }">
        <div class="todo-card__head">
          <h2 class="todo-card__title">{{ todo.title }}</h2>
          <button class="chip-button" type="button" @click="toggleTodo(todo.id, todo.status)">
            {{ todo.status === 'done' ? '恢复' : '完成' }}
          </button>
        </div>

        <p v-if="todo.description" class="todo-card__desc">{{ todo.description }}</p>

        <div class="todo-card__meta">
          <span>{{ todo.is_pinned ? '已置顶' : '未置顶' }}</span>
          <span>{{ formatTime(todo.end_date) }}</span>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.empty-card,
.todo-card {
  padding: 20px;
  border: 1px solid var(--theme-card-border);
  border-radius: 24px;
  background: var(--theme-card-bg);
  backdrop-filter: blur(14px);
  box-shadow: var(--theme-card-shadow);
}

.empty-card {
  color: var(--text-tertiary);
}

.todo-card {
  display: grid;
  gap: 12px;
}

.todo-card--done {
  opacity: 0.72;
}

.todo-card__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.todo-card__title {
  margin: 0;
  font-size: 1rem;
}

.todo-card__desc {
  margin: 0;
  color: var(--text-secondary);
}

.todo-card__meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  color: var(--text-tertiary);
  font-size: 0.88rem;
}
</style>
