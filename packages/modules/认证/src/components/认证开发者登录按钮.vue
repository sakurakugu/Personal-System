<script setup lang="ts">
import type { DeveloperLoginAction } from '../dev-login'
import { ElButton } from 'element-plus'

interface Props {
  actions: DeveloperLoginAction[]
  buttonClass?: string
  loading: boolean
}

withDefaults(defineProps<Props>(), {
  buttonClass: '',
})

const emit = defineEmits<{
  login: []
}>()
</script>

<template>
  <div class="dev-login-row">
    <ElButton
      v-for="action in actions"
      :key="action.label"
      :class="buttonClass"
      :loading="loading"
      @click="emit('login')"
    >
      {{ action.label }}
    </ElButton>
  </div>
</template>

<style scoped>
.dev-login-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
</style>
