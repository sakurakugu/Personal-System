import type { AuthUserRole } from '@personal-system/domain/auth'

export interface ProfileRoleDisplay {
  badgeType: 'danger' | 'primary' | 'success'
  label: string
}

export function getProfileRoleDisplay(role?: AuthUserRole | null): ProfileRoleDisplay {
  if (role === 'super_admin') {
    return {
      label: '超级管理员',
      badgeType: 'danger',
    }
  }
  if (role === 'admin') {
    return {
      label: '管理员',
      badgeType: 'primary',
    }
  }
  return {
    label: '普通用户',
    badgeType: 'success',
  }
}

export function getProfileDisplayName(user: {
  nickname?: string | null
  username?: string | null
} | null | undefined): string {
  return user?.nickname || user?.username || '未命名账号'
}

export function getProfileAccountStatusLabel(isActive?: boolean | null): string {
  return isActive === false ? '已停用' : '正常'
}

export function formatProfileDateTime(value?: string | null): string {
  if (!value) {
    return '未知'
  }
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}
