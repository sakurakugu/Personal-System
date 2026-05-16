export * from './display'
export * from './use-profile-editor'
export { default as ProfilePage } from './pages/个人页面.vue'

// 向后兼容别名
export { 获取个人资料角色显示 as getProfileRoleDisplay, 获取个人资料显示名称 as getProfileDisplayName, 获取个人资料账户状态标签 as getProfileAccountStatusLabel, 格式化个人资料日期时间 as formatProfileDateTime } from './display'
export { 使用个人资料编辑器 as useProfileEditor } from './use-profile-editor'
