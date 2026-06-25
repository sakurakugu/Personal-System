import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { 是否API未授权错误 } from '@personal-system/api'
import {
  修改当前用户密码,
  删除当前用户账号,
  注册 as 请求注册,
  更新当前用户,
} from './api'
import { 获取已配置的认证会话驱动, 获取已配置的开发者登录处理器 } from './context'
import { 是否启用开发者登录 } from './runtime'
import type { AuthUser, AuthUserRole, ProfileUpdatePayload } from './types'

export const 使用认证存储 = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const isLoading = ref(false)
  const sessionChecked = ref(false)
  let restoreTask: Promise<void> | null = null

  const isAuthenticated = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const userRole = computed(() => user.value?.role || 'guest')

  function 清除会话() {
    const sessionDriver = 获取已配置的认证会话驱动()
    user.value = null
    sessionChecked.value = true
    void sessionDriver.清除会话?.()
  }

  async function 登录(username: string, password: string) {
    const sessionDriver = 获取已配置的认证会话驱动()
    const loginResult = await sessionDriver.登录({ username, password })
    if (loginResult) {
      user.value = loginResult
      sessionChecked.value = true
      return
    }
    await 获取用户()
  }

  async function 开发者登录(role: AuthUserRole) {
    if (!是否启用开发者登录()) {
      throw new Error('当前环境不支持开发者登录')
    }
    const performDeveloperLogin = 获取已配置的开发者登录处理器()
    if (!performDeveloperLogin) {
      throw new Error('当前应用未配置开发者登录能力')
    }
    await performDeveloperLogin(role)
    await 获取用户()
  }

  async function 注册(username: string, email: string, password: string, nickname?: string) {
    await 请求注册({ username, email, password, nickname })
  }

  async function 获取用户() {
    const sessionDriver = 获取已配置的认证会话驱动()
    const data = await sessionDriver.获取当前用户()
    user.value = data
    sessionChecked.value = true
  }

  function 需要时恢复用户(): Promise<void> {
    if (user.value || sessionChecked.value) {
      return Promise.resolve()
    }
    if (restoreTask) {
      return restoreTask
    }
    restoreTask = (async () => {
      try {
        await 获取用户()
      } catch (error) {
        if (是否API未授权错误(error)) {
          清除会话()
          return
        }
        user.value = null
        sessionChecked.value = false
        console.warn('恢复登录状态失败，已保留本地会话等待下次重试', error)
      } finally {
        restoreTask = null
      }
    })()
    return restoreTask
  }

  async function 更新个人资料(payload: ProfileUpdatePayload) {
    const data = await 更新当前用户(payload)
    user.value = data
    return data
  }

  async function 修改密码(currentPassword: string, newPassword: string) {
    await 修改当前用户密码(currentPassword, newPassword)
    清除会话()
  }

  async function 删除账户(password: string) {
    await 删除当前用户账号(password)
    清除会话()
  }

  async function 登出() {
    const sessionDriver = 获取已配置的认证会话驱动()
    try {
      await sessionDriver.登出()
    } finally {
      清除会话()
    }
  }

  return {
    user,
    isLoading,
    sessionChecked,
    isAuthenticated,
    isAdmin,
    userRole,
    清除会话,
    登录,
    开发者登录,
    注册,
    获取用户,
    需要时恢复用户,
    更新个人资料,
    修改密码,
    删除账户,
    登出,
  }
})
