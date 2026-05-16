<script setup lang="ts">
import { ElFormItem, ElInput } from 'element-plus'

interface RegisterFormModel {
  confirmPassword: string
  email: string
  nickname: string
  password: string
  username: string
}

interface Props {
  form: RegisterFormModel
  inputClass?: string
  itemClass?: string
}

withDefaults(defineProps<Props>(), {
  inputClass: '',
  itemClass: '',
})
</script>

<template>
  <ElFormItem label="用户名" :class="itemClass">
    <ElInput
      v-model="form.username"
      :class="inputClass"
      autocomplete="username"
      clearable
      placeholder="至少 2 个字符"
    />
  </ElFormItem>

  <ElFormItem label="昵称" :class="itemClass">
    <ElInput
      v-model="form.nickname"
      :class="inputClass"
      clearable
      placeholder="用于展示，可选"
    />
  </ElFormItem>

  <ElFormItem label="邮箱" :class="itemClass">
    <ElInput
      v-model="form.email"
      :class="inputClass"
      autocomplete="email"
      clearable
      placeholder="your@email.com"
    />
  </ElFormItem>

  <ElFormItem label="密码" :class="itemClass">
    <ElInput
      v-model="form.password"
      :class="inputClass"
      autocomplete="new-password"
      placeholder="至少 6 位"
      show-password
      type="password"
    />
  </ElFormItem>

  <ElFormItem label="确认密码" :class="itemClass">
    <ElInput
      v-model="form.confirmPassword"
      :class="inputClass"
      autocomplete="new-password"
      placeholder="再次输入密码"
      show-password
      type="password"
    />
  </ElFormItem>
</template>
