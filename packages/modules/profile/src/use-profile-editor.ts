import { useAuthStore } from '@personal-system/domain/auth'
import { computed, ref } from 'vue'

export interface ProfileEditorMessages {
  deleteAccountFailed?: string
  deleteAccountSuccess?: string
  emailInvalid?: string
  fieldsRequired?: string
  passwordChangeFailed?: string
  passwordChangeSuccess?: string
  passwordIncomplete?: string
  passwordMismatch?: string
  passwordTooShort?: string
  profileSaveFailed?: string
  profileSaveSuccess?: string
  deletePasswordRequired?: string
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
  deleteAccountFailed: '注销账户失败',
  deleteAccountSuccess: '账户已注销',
  deletePasswordRequired: '请输入密码',
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

export function useProfileEditor(options: ProfileEditorOptions) {
  const auth = useAuthStore()
  const savingProfile = ref(false)
  const savingPassword = ref(false)
  const deletingAccount = ref(false)
  const deleteDialogVisible = ref(false)
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
  const deleteAccountForm = ref({
    password: '',
  })

  const messages = {
    ...DEFAULT_MESSAGES,
    ...options.messages,
  }

  const canDeleteAccount = computed(() => !auth.isSuperAdmin)
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

  function openDeleteDialog() {
    deleteAccountForm.value = { password: '' }
    deleteDialogVisible.value = true
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
      await auth.updateProfile({
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
      await auth.changePassword(passwordForm.value.current_password, passwordForm.value.new_password)
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

  async function deleteAccount() {
    if (!deleteAccountForm.value.password) {
      options.notifier.error(messages.deletePasswordRequired)
      return false
    }

    deletingAccount.value = true
    try {
      await auth.deleteAccount(deleteAccountForm.value.password)
      deleteDialogVisible.value = false
      options.notifier.success(messages.deleteAccountSuccess)
      return true
    } catch (error: any) {
      options.notifier.error(error?.response?.data?.detail || messages.deleteAccountFailed)
      return false
    } finally {
      deletingAccount.value = false
    }
  }

  return {
    auth,
    avatarPreviewUrl,
    canDeleteAccount,
    deleteAccount,
    deleteAccountForm,
    deleteDialogVisible,
    deletingAccount,
    emailInvalid,
    openDeleteDialog,
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
