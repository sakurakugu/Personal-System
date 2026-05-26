<script setup lang="ts">
import { ElFormItem, ElInput } from 'element-plus'

interface LoginFormModel {
  username: string
  password: string
}

interface Props {
  form: LoginFormModel
  inputClass?: string
  itemClass?: string
  labelPosition?: 'top' | 'left' | 'right'
  passwordPlaceholder?: string
  usernamePlaceholder?: string
}

withDefaults(defineProps<Props>(), {
  inputClass: '',
  itemClass: '',
  labelPosition: 'top',
  passwordPlaceholder: '请输入密码',
  usernamePlaceholder: '请输入用户名',
})
</script>

<template>
  <ElFormItem label="用户名" :class="itemClass">
    <ElInput
      v-model="form.username"
      :class="inputClass"
      autocomplete="username"
      clearable
      :placeholder="usernamePlaceholder"
    />
  </ElFormItem>

  <ElFormItem label="密码" :class="itemClass">
    <ElInput
      v-model="form.password"
      :class="inputClass"
      autocomplete="current-password"
      :placeholder="passwordPlaceholder"
      show-password
      type="password"
    />
  </ElFormItem>
</template>
