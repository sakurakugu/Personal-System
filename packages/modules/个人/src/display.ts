import type { AuthUserRole } from '@personal-system/domain/auth'

export interface ProfileRoleDisplay {
  badgeType: 'danger' | 'primary' | 'success'
  label: string
}

export function 获取个人资料角色显示(role?: AuthUserRole | null): ProfileRoleDisplay {
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

export function 获取个人资料显示名称(user: {
  nickname?: string | null
  username?: string | null
} | null | undefined): string {
  return user?.nickname || user?.username || '未命名账号'
}

export function 获取个人资料账户状态标签(isActive?: boolean | null): string {
  return isActive === false ? '已停用' : '正常'
}

export function 格式化个人资料日期时间(value?: string | null): string {
  if (!value) {
    return '未知'
  }
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}
