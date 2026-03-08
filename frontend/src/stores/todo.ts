import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../utils/api'

export interface Todo {
  id: string
  title: string
  description: string | null
  status: string
  priority: number
  due_date: string | null
  created_at: string
  updated_at: string
}

export const useTodoStore = defineStore('todo', () => {
  const todos = ref<Todo[]>([])
  const loading = ref(false)

  async function fetchTodos() {
    loading.value = true
    try {
      const { data } = await api.get('/todos')
      todos.value = data
    } finally {
      loading.value = false
    }
  }

  async function addTodo(body: { title: string; description?: string; priority?: number; due_date?: string }) {
    const { data } = await api.post('/todos', body)
    todos.value.unshift(data)
    return data
  }

  async function updateTodo(id: string, body: Partial<Todo>) {
    const { data } = await api.patch(`/todos/${id}`, body)
    const idx = todos.value.findIndex(t => t.id === id)
    if (idx !== -1) todos.value[idx] = data
    return data
  }

  async function deleteTodo(id: string) {
    await api.delete(`/todos/${id}`)
    todos.value = todos.value.filter(t => t.id !== id)
  }

  return { todos, loading, fetchTodos, addTodo, updateTodo, deleteTodo }
})
