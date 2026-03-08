<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import {
  NCard, NButton, NInput, NSelect, NTag, NSpace, NEmpty, NModal, NForm, NFormItem,
  NDatePicker, useMessage, NPopconfirm,
} from 'naive-ui'
import { useTodoStore, type Todo } from '../../stores/todo'

const todoStore = useTodoStore()
const message = useMessage()

const showAdd = ref(false)
const newTodo = ref({ title: '', description: '', priority: 2, due_date: null as number | null })

onMounted(() => todoStore.fetchTodos())

const statusGroups = computed(() => ({
  todo: todoStore.todos.filter(t => t.status === 'todo'),
  in_progress: todoStore.todos.filter(t => t.status === 'in_progress'),
  done: todoStore.todos.filter(t => t.status === 'done'),
}))

const priorityOptions = [
  { label: '🔴 高', value: 1 },
  { label: '🟡 中', value: 2 },
  { label: '🟢 低', value: 3 },
]

const statusLabel: Record<string, string> = {
  todo: '📋 待办',
  in_progress: '🔄 进行中',
  done: '✅ 已完成',
}

const priorityTag: Record<number, string> = { 1: 'error', 2: 'warning', 3: 'success' }

async function addTodo() {
  if (!newTodo.value.title.trim()) return
  try {
    await todoStore.addTodo({
      title: newTodo.value.title,
      description: newTodo.value.description || undefined,
      priority: newTodo.value.priority,
      due_date: newTodo.value.due_date ? new Date(newTodo.value.due_date).toISOString() : undefined,
    })
    showAdd.value = false
    newTodo.value = { title: '', description: '', priority: 2, due_date: null }
    message.success('创建成功')
  } catch { message.error('创建失败') }
}

async function changeStatus(todo: Todo, status: string) {
  await todoStore.updateTodo(todo.id, { status })
}

async function removeTodo(id: string) {
  await todoStore.deleteTodo(id)
  message.success('已删除')
}
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px">
      <h2>📋 待办事项</h2>
      <NButton type="primary" @click="showAdd = true">+ 新建</NButton>
    </div>

    <div class="kanban">
      <div v-for="key in ['todo', 'in_progress', 'done']" :key="key" class="kanban-col">
        <h3>{{ statusLabel[key] }} ({{ statusGroups[key as keyof typeof statusGroups].length }})</h3>
        <div class="kanban-items">
          <NCard v-for="t in statusGroups[key as keyof typeof statusGroups]" :key="t.id" size="small" class="todo-card">
            <div style="display: flex; justify-content: space-between; align-items: start">
              <strong>{{ t.title }}</strong>
              <NTag :type="(priorityTag[t.priority] as any)" size="tiny">P{{ t.priority }}</NTag>
            </div>
            <p v-if="t.description" style="font-size: 12px; color: #888; margin: 4px 0">{{ t.description }}</p>
            <p v-if="t.due_date" style="font-size: 11px; color: #aaa">截止: {{ new Date(t.due_date).toLocaleDateString() }}</p>
            <NSpace size="small" style="margin-top: 8px">
              <NButton v-if="key !== 'in_progress'" size="tiny" @click="changeStatus(t, 'in_progress')">进行中</NButton>
              <NButton v-if="key !== 'done'" size="tiny" type="success" @click="changeStatus(t, 'done')">完成</NButton>
              <NButton v-if="key !== 'todo'" size="tiny" @click="changeStatus(t, 'todo')">待办</NButton>
              <NPopconfirm @positive-click="removeTodo(t.id)">
                <template #trigger><NButton size="tiny" type="error" quaternary>删除</NButton></template>
                确定删除？
              </NPopconfirm>
            </NSpace>
          </NCard>
          <NEmpty v-if="statusGroups[key as keyof typeof statusGroups].length === 0" description="空" size="small" />
        </div>
      </div>
    </div>

    <NModal v-model:show="showAdd" preset="card" title="新建待办" style="width: 420px; max-width: 90vw">
      <NForm @submit.prevent="addTodo">
        <NFormItem label="标题">
          <NInput v-model:value="newTodo.title" placeholder="待办标题" />
        </NFormItem>
        <NFormItem label="描述">
          <NInput v-model:value="newTodo.description" type="textarea" placeholder="可选描述" />
        </NFormItem>
        <NFormItem label="优先级">
          <NSelect v-model:value="newTodo.priority" :options="priorityOptions" />
        </NFormItem>
        <NFormItem label="截止日期">
          <NDatePicker v-model:value="newTodo.due_date" type="date" clearable style="width: 100%" />
        </NFormItem>
        <NButton type="primary" block attr-type="submit">创建</NButton>
      </NForm>
    </NModal>
  </div>
</template>

<style scoped>
.kanban {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 768px) {
  .kanban { grid-template-columns: 1fr; }
}

.kanban-col h3 {
  margin-bottom: 12px;
  font-size: 14px;
}

.kanban-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 100px;
  background: #fafafa;
  border-radius: 8px;
  padding: 8px;
}

.todo-card {
  border-left: 3px solid #18a058;
}
</style>
