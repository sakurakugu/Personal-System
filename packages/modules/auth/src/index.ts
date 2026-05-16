export { default as AuthCredentialsFields } from './components/认证凭证字段.vue'
export { default as DesktopWidgetTokenCard } from './components/桌面小工具令牌卡片.vue'
export { default as DeviceSessionsPage } from './components/设备会话页面.vue'
export { default as AuthEntryCard } from './components/认证入口卡片.vue'
export { default as AuthDeveloperLoginButtons } from './components/认证开发者登录按钮.vue'
export { default as AuthRegisterFields } from './components/认证注册字段.vue'
export * from './dev-login'
export * from './module'
export * from './use-auth-entry'

// 向后兼容别名
export { 开发者登录操作 as developerLoginActions } from './dev-login'
export { 创建认证模块 as createAuthModule } from './module'
export { 使用认证入口 as useAuthEntry } from './use-auth-entry'
