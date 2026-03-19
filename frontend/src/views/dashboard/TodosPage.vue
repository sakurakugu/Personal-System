<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import {
  ElButton,
  ElCard,
  ElDatePicker,
  ElDialog,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElMessage,
  ElOption,
  ElPopconfirm,
  ElSelect,
  ElSpace,
  ElTag,
} from 'element-plus'
import { List, RefreshRight, CircleCheckFilled } from '@element-plus/icons-vue'
import { useTodoStore, type Todo } from '../../stores/todo'

const todoStore = useTodoStore()

const showAdd = ref(false)
const newTodo = ref({ title: '', description: '', priority: 2, due_date: null as Date | null })

onMounted(() => todoStore.fetchTodos())

const statusGroups = computed(() => ({
  todo: todoStore.todos.filter(t => t.status === 'todo'),
  in_progress: todoStore.todos.filter(t => t.status === 'in_progress'),
  done: todoStore.todos.filter(t => t.status === 'done'),
}))

const priorityOptions = [
  { label: '高', value: 1 },
  { label: '中', value: 2 },
  { label: '低', value: 3 },
]

const statusLabel: Record<string, string> = {
  todo: '待办',
  in_progress: '进行中',
  done: '已完成',
}
const statusIcon = {
  todo: List,
  in_progress: RefreshRight,
  done: CircleCheckFilled,
}

const priorityTag: Record<number, 'danger' | 'warning' | 'success'> = { 1: 'danger', 2: 'warning', 3: 'success' }

async function addTodo() {
  if (!newTodo.value.title.trim()) return
  try {
    await todoStore.addTodo({
      title: newTodo.value.title,
      description: newTodo.value.description || undefined,
      priority: newTodo.value.priority,
      due_date: newTodo.value.due_date ? newTodo.value.due_date.toISOString() : undefined,
    })
    showAdd.value = false
    newTodo.value = { title: '', description: '', priority: 2, due_date: null }
    ElMessage.success('创建成功')
  } catch { ElMessage.error('创建失败') }
}

async function changeStatus(todo: Todo, status: string) {
  await todoStore.updateTodo(todo.id, { status })
}

async function removeTodo(id: string) {
  await todoStore.deleteTodo(id)
  ElMessage.success('已删除')
}
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px">
      <h2 style="display: flex; align-items: center; gap: 8px">
        <ElIcon><List /></ElIcon>
        <span>待办事项</span>
      </h2>
      <ElButton type="primary" @click="showAdd = true">+ 新建</ElButton>
    </div>

    <div class="kanban">
      <div v-for="key in ['todo', 'in_progress', 'done']" :key="key" class="kanban-col">
        <h3 style="display: flex; align-items: center; gap: 6px">
          <ElIcon><component :is="statusIcon[key as keyof typeof statusIcon]" /></ElIcon>
          <span>{{ statusLabel[key] }} ({{ statusGroups[key as keyof typeof statusGroups].length }})</span>
        </h3>
        <div class="kanban-items">
          <ElCard v-for="t in statusGroups[key as keyof typeof statusGroups]" :key="t.id" class="todo-card">
            <div style="display: flex; justify-content: space-between; align-items: start">
              <strong>{{ t.title }}</strong>
              <ElTag :type="priorityTag[t.priority]" size="small">P{{ t.priority }}</ElTag>
            </div>
            <p v-if="t.description" style="font-size: 12px; color: #888; margin: 4px 0">{{ t.description }}</p>
            <p v-if="t.due_date" style="font-size: 11px; color: #aaa">截止: {{ new Date(t.due_date).toLocaleDateString() }}</p>
            <ElSpace size="small" style="margin-top: 8px">
              <ElButton v-if="key !== 'in_progress'" size="small" @click="changeStatus(t, 'in_progress')">进行中</ElButton>
              <ElButton v-if="key !== 'done'" size="small" type="success" @click="changeStatus(t, 'done')">完成</ElButton>
              <ElButton v-if="key !== 'todo'" size="small" @click="changeStatus(t, 'todo')">待办</ElButton>
              <ElPopconfirm @confirm="removeTodo(t.id)">
                <template #reference><ElButton size="small" type="danger" text>删除</ElButton></template>
                确定删除？
              </ElPopconfirm>
            </ElSpace>
          </ElCard>
          <div v-if="statusGroups[key as keyof typeof statusGroups].length === 0" class="kanban-empty">
            <ElEmpty description="空" />
          </div>
        </div>
      </div>
    </div>

    <ElDialog
      :model-value="showAdd"
      title="新建待办"
      width="420px"
      style="max-width: 90vw"
      @update:model-value="showAdd = $event"
    >
      <ElForm @submit.prevent="addTodo">
        <ElFormItem label="标题">
          <ElInput v-model="newTodo.title" placeholder="待办标题" />
        </ElFormItem>
        <ElFormItem label="描述">
          <ElInput v-model="newTodo.description" type="textarea" placeholder="可选描述" />
        </ElFormItem>
        <ElFormItem label="优先级">
          <ElSelect v-model="newTodo.priority">
            <ElOption v-for="item in priorityOptions" :key="item.value" :label="item.label" :value="item.value" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="截止日期">
          <ElDatePicker v-model="newTodo.due_date" type="date" clearable style="width: 100%" />
        </ElFormItem>
        <ElButton type="primary" style="width: 100%" native-type="submit">创建</ElButton>
      </ElForm>
    </ElDialog>
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
  min-height: 160px;
  background: #fafafa;
  border-radius: 8px;
  padding: 8px;
}

.kanban-empty {
  flex: 1;
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.todo-card {
  border-left: 3px solid #18a058;
}
</style>
