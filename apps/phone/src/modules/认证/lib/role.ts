import type { AuthUserRole } from '@personal-system/domain/auth'

export interface RoleCapabilityItem {
  title: string
  description: string
}

export interface PhoneRoleProfile {
  label: string
  badge: string
  summary: string
  capabilities: RoleCapabilityItem[]
  managementNotice?: string
}

const roleProfiles: Record<AuthUserRole, PhoneRoleProfile> = {
  user: {
    label: '普通用户',
    badge: '用户',
    summary: '手机端优先保留个人高频操作，适合随手查看待办、资料和当前账号状态。',
    capabilities: [
      {
        title: '待办执行',
        description: '随时查看未完成事项，保持日常任务推进。',
      },
      {
        title: '个人资料',
        description: '查看账号、昵称、邮箱和当前登录身份。',
      },
      {
        title: '环境切换',
        description: '开发阶段可在手机端直接切换接口环境并重新登录。',
      },
    ],
  },
  admin: {
    label: '管理员',
    badge: '管理',
    summary: '当前账号具备日常管理权限，手机端已经能识别管理员身份并保留高频个人入口。',
    capabilities: [
      {
        title: '内容维护',
        description: '可继续承接文章、文件等日常维护类工作。',
      },
      {
        title: '管理身份',
        description: '当前登录身份会在手机端明确标记，避免误用普通用户视角。',
      },
      {
        title: '环境联调',
        description: '需要切换本地、局域网或其他服务端时，可直接在手机端调整。',
      },
    ],
    managementNotice: '管理类页面还在继续从 Web 端拆分，当前手机端先保留身份识别、待办和接口环境这些高频能力。',
  },
  super_admin: {
    label: '超级管理员',
    badge: '超管',
    summary: '当前账号具备全局管理权限，手机端已经能区分超管身份并保留核心联调入口。',
    capabilities: [
      {
        title: '全局权限',
        description: '可识别为最高权限账号，便于区分系统级操作视角。',
      },
      {
        title: '系统联调',
        description: '移动端可直接切换接口环境，方便验证后端和原生壳链路。',
      },
      {
        title: '高频自助',
        description: '先保留待办、资料和环境管理，减少每次必须回到电脑端处理的频率。',
      },
    ],
    managementNotice: '系统设置、系统状态、公告等超管页面还没有完整迁到手机端，后续可以继续拆成独立模块。',
  },
}

export function 获取手机角色配置(role?: AuthUserRole | null): PhoneRoleProfile {
  if (!role) {
    return roleProfiles.user
  }
  return roleProfiles[role]
}
