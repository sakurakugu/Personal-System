<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@personal-system/domain/auth'
import { useTodoStore } from '@personal-system/domain/todos'

const auth = useAuthStore()
const todoStore = useTodoStore()

const pendingTodoCount = computed(() => todoStore.todos.filter((todo) => todo.status === 'todo').length)
</script>

<template>
  <section class="page">
    <header class="hero-card">
      <p class="eyebrow">首页</p>
      <h1 class="page-title">{{ auth.user?.nickname || auth.user?.username || '你好' }}</h1>
      <p class="page-subtitle">手机端先聚焦高频路径，不继承 Web 控制台的复杂布局。</p>
    </header>

    <div class="stack">
      <RouterLink class="panel-card panel-link" to="/todos">
        <span class="panel-title">待办</span>
        <strong class="panel-value">{{ pendingTodoCount }}</strong>
        <span class="panel-meta">当前未完成数量</span>
      </RouterLink>

      <RouterLink class="panel-card panel-link" to="/me">
        <span class="panel-title">账号</span>
        <strong class="panel-value">{{ auth.userRole }}</strong>
        <span class="panel-meta">查看个人资料与退出登录</span>
      </RouterLink>
    </div>
  </section>
</template>
