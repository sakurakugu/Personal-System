import type { AuthUserRole } from '@personal-system/domain/auth'

export interface RoleCapabilityItem {
  title: string
}

export interface PhoneRoleProfile {
  label: string
  badge: string
  capabilities: RoleCapabilityItem[]
}

const roleProfiles: Record<AuthUserRole, PhoneRoleProfile> = {
  user: {
    label: '普通用户',
    badge: '用户',
    capabilities: [
      {
        title: '待办执行',
      },
      {
        title: '个人资料',
      },
      {
        title: '环境切换',
      },
    ],
  },
  admin: {
    label: '管理员',
    badge: '管理',
    capabilities: [
      {
        title: '内容维护',
      },
      {
        title: '管理身份',
      },
      {
        title: '环境联调',
      },
    ],
  },
}

export function 获取手机角色配置(role?: AuthUserRole | null): PhoneRoleProfile {
  if (!role) {
    return roleProfiles.user
  }
  return roleProfiles[role]
}
