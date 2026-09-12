import { 使用认证存储 } from '@personal-system/domain/auth'
import { computed, ref } from 'vue'

export interface ProfileEditorMessages {
  emailInvalid?: string
  fieldsRequired?: string
  passwordChangeFailed?: string
  passwordChangeSuccess?: string
  passwordIncomplete?: string
  passwordMismatch?: string
  passwordTooShort?: string
  profileSaveFailed?: string
  profileSaveSuccess?: string
}

export interface ProfileEditorNotifier {
  error: (message: string) => void
  success: (message: string) => void
}

export interface ProfileEditorOptions {
  notifier: ProfileEditorNotifier
  messages?: ProfileEditorMessages
}

const DEFAULT_MESSAGES: Required<ProfileEditorMessages> = {
  emailInvalid: '邮箱格式不正确',
  fieldsRequired: '用户名和邮箱不能为空',
  passwordChangeFailed: '修改密码失败',
  passwordChangeSuccess: '密码修改成功',
  passwordIncomplete: '请填写完整密码信息',
  passwordMismatch: '两次输入的新密码不一致',
  passwordTooShort: '新密码至少 6 位',
  profileSaveFailed: '保存失败',
  profileSaveSuccess: '个人资料已更新',
}

export function 使用个人资料编辑器(options: ProfileEditorOptions) {
  const auth = 使用认证存储()
  const savingProfile = ref(false)
  const savingPassword = ref(false)
  const profileForm = ref({
    avatar_url: '',
    bio: '',
    email: '',
    nickname: '',
    username: '',
  })
  const passwordForm = ref({
    confirm_password: '',
    current_password: '',
    new_password: '',
  })

  const messages = {
    ...DEFAULT_MESSAGES,
    ...options.messages,
  }

  const avatarPreviewUrl = computed(() => profileForm.value.avatar_url.trim() || null)
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  const emailInvalid = computed(() => {
    const value = profileForm.value.email.trim()
    return !!value && !emailRegex.test(value)
  })

  function syncFormFromUser() {
    profileForm.value = {
      username: auth.user?.username || '',
      nickname: auth.user?.nickname || '',
      email: auth.user?.email || '',
      avatar_url: auth.user?.avatar_url || '',
      bio: auth.user?.bio || '',
    }
  }

  function resetPasswordForm() {
    passwordForm.value = {
      current_password: '',
      new_password: '',
      confirm_password: '',
    }
  }

  async function saveProfile() {
    if (!profileForm.value.username.trim() || !profileForm.value.email.trim()) {
      options.notifier.error(messages.fieldsRequired)
      return false
    }
    if (emailInvalid.value) {
      options.notifier.error(messages.emailInvalid)
      return false
    }

    savingProfile.value = true
    try {
      await auth.更新个人资料({
        username: profileForm.value.username.trim(),
        nickname: profileForm.value.nickname.trim() || null,
        email: profileForm.value.email.trim(),
        avatar_url: profileForm.value.avatar_url.trim() || null,
        bio: profileForm.value.bio.trim() || null,
      })
      syncFormFromUser()
      options.notifier.success(messages.profileSaveSuccess)
      return true
    } catch (error: any) {
      options.notifier.error(error?.response?.data?.detail || messages.profileSaveFailed)
      return false
    } finally {
      savingProfile.value = false
    }
  }

  async function changePassword() {
    if (!passwordForm.value.current_password || !passwordForm.value.new_password || !passwordForm.value.confirm_password) {
      options.notifier.error(messages.passwordIncomplete)
      return false
    }
    if (passwordForm.value.new_password.length < 6) {
      options.notifier.error(messages.passwordTooShort)
      return false
    }
    if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
      options.notifier.error(messages.passwordMismatch)
      return false
    }

    savingPassword.value = true
    try {
      await auth.修改密码(passwordForm.value.current_password, passwordForm.value.new_password)
      resetPasswordForm()
      options.notifier.success(messages.passwordChangeSuccess)
      return true
    } catch (error: any) {
      options.notifier.error(error?.response?.data?.detail || messages.passwordChangeFailed)
      return false
    } finally {
      savingPassword.value = false
    }
  }

  return {
    auth,
    avatarPreviewUrl,
    emailInvalid,
    passwordForm,
    profileForm,
    resetPasswordForm,
    saveProfile,
    savingPassword,
    savingProfile,
    changePassword,
    syncFormFromUser,
  }
}
