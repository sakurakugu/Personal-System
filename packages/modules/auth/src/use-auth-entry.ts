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

export function 使用认证入口(options: UseAuthEntryOptions) {
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

  function 清除错误() {
    errorMessage.value = ''
  }

  function 重置注册表单() {
    registerForm.username = ''
    registerForm.nickname = ''
    registerForm.email = ''
    registerForm.password = ''
    registerForm.confirmPassword = ''
  }

  async function 认证后导航() {
    await options.redirectHandler.navigate(options.redirectHandler.getRedirectPath())
  }

  async function 处理登录() {
    清除错误()
    loading.value = true

    try {
      await auth.登录(loginForm.username, loginForm.password)
    } catch (error: any) {
      errorMessage.value = error?.response?.data?.detail || messages.loginFailed
      loading.value = false
      return
    }

    try {
      await 认证后导航()
    } catch {
      errorMessage.value = messages.redirectFailed
    } finally {
      loading.value = false
    }
  }

  async function 处理开发者登录(role: AuthUserRole) {
    清除错误()
    loading.value = true

    try {
      await auth.开发者登录(role)
    } catch (error: any) {
      errorMessage.value = error?.response?.data?.detail || messages.developerLoginFailed
      loading.value = false
      return
    }

    try {
      await 认证后导航()
    } catch {
      errorMessage.value = messages.redirectFailed
    } finally {
      loading.value = false
    }
  }

  async function 处理注册() {
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

    清除错误()
    loading.value = true

    try {
      await auth.注册(
        registerForm.username,
        registerForm.email,
        registerForm.password,
        registerForm.nickname.trim() || undefined,
      )
      activeTab.value = 'login'
      loginForm.username = registerForm.username
      重置注册表单()
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
    clearError: 清除错误,
    handleDeveloperLogin: 处理开发者登录,
    handleLogin: 处理登录,
    handleRegister: 处理注册,
    resetRegisterForm: 重置注册表单,
  }
}
