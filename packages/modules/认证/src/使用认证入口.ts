import { 是否启用开发者登录, 使用认证存储, type AuthUserRole } from '@personal-system/domain/auth'
import { reactive, ref } from 'vue'
export interface AuthEntryRedirectHandler { getRedirectPath: () => string; navigate: (path: string) => Promise<unknown> }
export interface AuthEntryMessages { developerLoginFailed?: string; loginFailed?: string; redirectFailed?: string }
export interface UseAuthEntryOptions { messages?: AuthEntryMessages; redirectHandler: AuthEntryRedirectHandler }
export function 使用认证入口(options: UseAuthEntryOptions) {
  const auth = 使用认证存储(); const errorMessage = ref(''); const loading = ref(false); const isDevMode = 是否启用开发者登录(); const loginForm = reactive({ username: '', password: '' })
  const messages = { developerLoginFailed: '开发者登录失败', loginFailed: '登录失败，请检查用户名和密码', redirectFailed: '登录成功，但进入页面失败，请刷新后重试', ...options.messages }
  const clearError = () => { errorMessage.value = '' }
  const navigate = async () => options.redirectHandler.navigate(options.redirectHandler.getRedirectPath())
  async function handleLogin() { clearError(); loading.value = true; try { await auth.登录(loginForm.username, loginForm.password) } catch (error: any) { errorMessage.value = error?.response?.data?.detail || messages.loginFailed; loading.value = false; return } try { await navigate() } catch { errorMessage.value = messages.redirectFailed } finally { loading.value = false } }
  async function handleDeveloperLogin(role: AuthUserRole) { clearError(); loading.value = true; try { await auth.开发者登录(role) } catch (error: any) { errorMessage.value = error?.response?.data?.detail || messages.developerLoginFailed; loading.value = false; return } try { await navigate() } catch { errorMessage.value = messages.redirectFailed } finally { loading.value = false } }
  return { errorMessage, isDevMode, loading, loginForm, clearError, handleDeveloperLogin, handleLogin }
}
