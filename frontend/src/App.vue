<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useThemeStore } from './stores/theme'
import AppHeader from './components/AppHeader.vue'
import LoginModal from './components/LoginModal.vue'
import { ref } from 'vue'

const auth = useAuthStore()
const theme = useThemeStore()
const route = useRoute()
const showLogin = ref(false)
const loginTab = ref<'login' | 'register'>('login')

onMounted(async () => {
  theme.initTheme()
  theme.listenToSystemTheme()
  if (auth.accessToken) {
    await auth.fetchUser()
  }
})

// If redirected with ?login=1, show login modal
watch(() => route.query.login, (val) => {
  if (val === '1') {
    loginTab.value = 'login'
    showLogin.value = true
  }
})

function openAuth(tab?: 'login' | 'register') {
  if (tab) loginTab.value = tab
  showLogin.value = true
}
</script>

<template>
  <div class="app-container">
    <AppHeader @show-login="openAuth" />
    <main class="main-content">
      <RouterView />
    </main>
    <footer class="app-footer">
      <div class="footer-inner">
        <!-- <span class="copyright">© 2026 </span> -->
        <span class="beian">备案号待填写</span>
      </div>
    </footer>
    <LoginModal v-model:show="showLogin" :initial-tab="loginTab" />
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f5f7fa;
  color: #333;
  min-height: 100vh;
  transition: background-color 0.3s, color 0.3s;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
}

/* 页脚样式 */
.app-footer {
  background: #fff;
  border-top: 1px solid #e8e8e8;
  padding: 8px;
  text-align: center;
}

.footer-inner {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  font-size: 13px;
  color: #888;
}

.dark .app-footer {
  background: var(--bg-secondary);
  border-top-color: var(--border-color);
}

.dark .footer-inner {
  color: var(--text-tertiary);
}

a {
  color: #18a058;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

/* ========== 夜间模式样式 ========== */

/* 基础变量 */
:root {
  --bg-primary: #f5f7fa;
  --bg-secondary: #ffffff;
  --bg-card: #ffffff;
  --bg-hover: #f5f7fa;
  --text-primary: #333333;
  --text-secondary: #666666;
  --text-tertiary: #888888;
  --border-color: #e8e8e8;
  --header-bg: #ffffff;
  --sidebar-bg: #ffffff;
  --input-bg: #ffffff;
  --code-bg: #f5f7fa;
}

/* 夜间模式变量 */
.dark {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-card: #1e293b;
  --bg-hover: #334155;
  --text-primary: #f1f5f9;
  --text-secondary: #cbd5e1;
  --text-tertiary: #94a3b8;
  --border-color: #334155;
  --header-bg: #1e293b;
  --sidebar-bg: #1e293b;
  --input-bg: #334155;
  --code-bg: #334155;
}

/* 应用夜间模式 */
.dark body {
  background: var(--bg-primary);
  color: var(--text-primary);
}

.dark .app-container {
  background: var(--bg-primary);
}

/* Element Plus 夜间模式覆盖 */
.dark .el-card {
  background-color: var(--bg-card) !important;
  border-color: var(--border-color) !important;
  color: var(--text-primary) !important;
}

.dark .el-card__header {
  border-bottom-color: var(--border-color) !important;
}

.dark .el-input__wrapper {
  background-color: var(--input-bg) !important;
  box-shadow: 0 0 0 1px var(--border-color) inset !important;
}

.dark .el-input__inner {
  color: var(--text-primary) !important;
}

.dark .el-button {
  background-color: transparent;
  border-color: var(--border-color);
  color: var(--text-primary);
}

.dark .el-button--primary {
  background-color: #18a058;
  border-color: #18a058;
}

.dark .el-menu {
  background-color: var(--sidebar-bg) !important;
  border-right-color: var(--border-color) !important;
}

.dark .el-menu-item {
  color: var(--text-secondary) !important;
}

.dark .el-menu-item:hover {
  background-color: var(--bg-hover) !important;
}

.dark .el-menu-item.is-active {
  color: #18a058 !important;
  background-color: rgba(24, 160, 88, 0.1) !important;
}

.dark .el-table {
  background-color: var(--bg-card) !important;
  color: var(--text-primary) !important;
}

.dark .el-table th,
.dark .el-table tr,
.dark .el-table__row {
  background-color: var(--bg-card) !important;
}

.dark .el-table td,
.dark .el-table th.is-leaf {
  border-bottom-color: var(--border-color) !important;
}

.dark .el-table__header th,
.dark .el-table__header-wrapper th {
  background-color: var(--bg-hover) !important;
  color: var(--text-primary) !important;
}

.dark .el-table--striped .el-table__body tr.el-table__row--striped td {
  background-color: rgba(255, 255, 255, 0.02) !important;
}

.dark .el-table--enable-row-hover .el-table__body tr:hover > td {
  background-color: var(--bg-hover) !important;
}

.dark .el-pagination {
  color: var(--text-primary);
}

.dark .el-pagination button {
  background-color: var(--bg-card) !important;
  color: var(--text-primary) !important;
}

.dark .el-pager li {
  background-color: var(--bg-card) !important;
  color: var(--text-primary) !important;
}

.dark .el-dialog {
  background-color: var(--bg-card) !important;
}

.dark .el-dialog__title {
  color: var(--text-primary) !important;
}

.dark .el-dropdown-menu {
  background-color: var(--bg-card) !important;
  border-color: var(--border-color) !important;
}

.dark .el-dropdown-menu__item {
  color: var(--text-primary) !important;
}

.dark .el-dropdown-menu__item:hover {
  background-color: var(--bg-hover) !important;
}

.dark .el-tag {
  background-color: var(--bg-hover) !important;
  border-color: var(--border-color) !important;
  color: var(--text-primary) !important;
}

.dark .el-tag--info {
  background-color: var(--bg-hover) !important;
  color: var(--text-secondary) !important;
}

.dark .el-empty__description {
  color: var(--text-secondary) !important;
}

.dark .el-text {
  color: var(--text-secondary) !important;
}

.dark .el-text.el-text--info {
  color: var(--text-tertiary) !important;
}

.dark .el-form-item__label {
  color: var(--text-primary) !important;
}

.dark .el-radio {
  color: var(--text-primary) !important;
}

.dark .el-checkbox {
  color: var(--text-primary) !important;
}

.dark .el-select-dropdown {
  background-color: var(--bg-card) !important;
  border-color: var(--border-color) !important;
}

.dark .el-select-dropdown__item {
  color: var(--text-primary) !important;
}

.dark .el-select-dropdown__item:hover {
  background-color: var(--bg-hover) !important;
}

.dark .el-textarea__inner {
  background-color: var(--input-bg) !important;
  color: var(--text-primary) !important;
  border-color: var(--border-color) !important;
}

.dark .el-tabs__item {
  color: var(--text-secondary) !important;
}

.dark .el-tabs__item.is-active {
  color: #18a058 !important;
}

.dark .el-tabs__active-bar {
  background-color: #18a058 !important;
}

.dark .el-divider__text {
  background-color: var(--bg-card) !important;
  color: var(--text-secondary) !important;
}

/* 修复 el-table 固定列和背景 */
.dark .el-table__body-wrapper,
.dark .el-table__header-wrapper {
  background-color: var(--bg-card) !important;
}

.dark .el-table__fixed,
.dark .el-table__fixed-right {
  background-color: var(--bg-card) !important;
}

.dark .el-table__fixed-header-wrapper th,
.dark .el-table__fixed-body-wrapper td {
  background-color: var(--bg-card) !important;
  border-bottom-color: var(--border-color) !important;
}

/* 页面标题颜色 */
.dark h1,
.dark h2,
.dark h3,
.dark h4,
.dark h5,
.dark h6 {
  color: var(--text-primary);
}

/* 修复 Loading 遮罩 */
.dark .el-loading-mask {
  background-color: rgba(15, 23, 42, 0.8) !important;
}
</style>
