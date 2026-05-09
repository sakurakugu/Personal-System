import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export interface LoginGatePayload {
  redirectPath: string
}

export const useLoginGateStore = defineStore('login-gate', () => {
  const visible = ref(false)
  const redirectPath = ref('/')

  const hasPendingRedirect = computed(() => visible.value)

  function open(payload: LoginGatePayload) {
    redirectPath.value = payload.redirectPath
    visible.value = true
  }

  function close() {
    visible.value = false
  }

  return {
    visible,
    redirectPath,
    hasPendingRedirect,
    open,
    close,
  }
})
