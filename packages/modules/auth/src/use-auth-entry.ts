import { 是否启用开发者登录, useAuthStore, type AuthUserRole } from '@personal-system/domain/auth'
import { computed, reactive, ref, watch, type Ref } from 'vue'

export interface AuthEntryRedirectHandler {
  getRedirectPath: () => string
  navigate: (path: string) => Promise<unknown>
}

export interface AuthEntryRegisterOptions {
  isReachable?: Ref<boolean>
  isRegisterEnabled?: Ref<boolean>
}

export interface AuthEntryMessages {
  developerLoginFailed?: string
  loginFailed?: string
  passwordMismatch?: string
  redirectFailed?: string
  registerDisabled?: string
  registerFailed?: string
  serverUnreachable?: string
}

export interface UseAuthEntryOptions {
  messages?: AuthEntryMessages
  redirectHandler: AuthEntryRedirectHandler
  registerOptions?: AuthEntryRegisterOptions
}

const DEFAULT_MESSAGES: Required<AuthEntryMessages> = {
  developerLoginFailed: '开发者登录失败',
  loginFailed: '登录失败，请检查用户名和密码',
  passwordMismatch: '两次输入的密码不一致',
  redirectFailed: '登录成功，但进入页面失败，请刷新后重试',
  registerDisabled: '当前未开放注册',
  registerFailed: '注册失败，请检查输入内容',
  serverUnreachable: '未连接服务器',
}

export function useAuthEntry(options: UseAuthEntryOptions) {
  const auth = useAuthStore()
  const activeTab = ref<'login' | 'register'>('login')
  const errorMessage = ref('')
  const loading = ref(false)
  const isDevMode = 是否启用开发者登录()
  const loginForm = reactive({
    username: '',
    password: '',
  })
  const registerForm = reactive({
    username: '',
    nickname: '',
    email: '',
    password: '',
    confirmPassword: '',
  })

  const messages = {
    ...DEFAULT_MESSAGES,
    ...options.messages,
  }

  const canRegister = computed(() => {
    const registerEnabled = options.registerOptions?.isRegisterEnabled?.value ?? true
    const reachable = options.registerOptions?.isReachable?.value ?? true
    return registerEnabled && reachable
  })

  watch(
    canRegister,
    (enabled) => {
      if (!enabled && activeTab.value !== 'login') {
        activeTab.value = 'login'
      }
    },
    { immediate: true },
  )

  function clearError() {
    errorMessage.value = ''
  }

  function resetRegisterForm() {
    registerForm.username = ''
    registerForm.nickname = ''
    registerForm.email = ''
    registerForm.password = ''
    registerForm.confirmPassword = ''
  }

  async function navigateAfterAuth() {
    await options.redirectHandler.navigate(options.redirectHandler.getRedirectPath())
  }

  async function handleLogin() {
    clearError()
    loading.value = true

    try {
      await auth.login(loginForm.username, loginForm.password)
    } catch (error: any) {
      errorMessage.value = error?.response?.data?.detail || messages.loginFailed
      loading.value = false
      return
    }

    try {
      await navigateAfterAuth()
    } catch {
      errorMessage.value = messages.redirectFailed
    } finally {
      loading.value = false
    }
  }

  async function handleDeveloperLogin(role: AuthUserRole) {
    clearError()
    loading.value = true

    try {
      await auth.developerLogin(role)
    } catch (error: any) {
      errorMessage.value = error?.response?.data?.detail || messages.developerLoginFailed
      loading.value = false
      return
    }

    try {
      await navigateAfterAuth()
    } catch {
      errorMessage.value = messages.redirectFailed
    } finally {
      loading.value = false
    }
  }

  async function handleRegister() {
    const reachable = options.registerOptions?.isReachable?.value ?? true
    const registerEnabled = options.registerOptions?.isRegisterEnabled?.value ?? true

    if (!reachable) {
      errorMessage.value = messages.serverUnreachable
      return
    }
    if (!registerEnabled) {
      errorMessage.value = messages.registerDisabled
      return
    }
    if (registerForm.password !== registerForm.confirmPassword) {
      errorMessage.value = messages.passwordMismatch
      return
    }

    clearError()
    loading.value = true

    try {
      await auth.register(
        registerForm.username,
        registerForm.email,
        registerForm.password,
        registerForm.nickname.trim() || undefined,
      )
      activeTab.value = 'login'
      loginForm.username = registerForm.username
      resetRegisterForm()
    } catch (error: any) {
      errorMessage.value = error?.response?.data?.detail || messages.registerFailed
    } finally {
      loading.value = false
    }
  }

  return {
    activeTab,
    canRegister,
    errorMessage,
    isDevMode,
    loading,
    loginForm,
    registerForm,
    clearError,
    handleDeveloperLogin,
    handleLogin,
    handleRegister,
    resetRegisterForm,
  }
}
