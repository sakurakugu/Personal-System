import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { ElLoading } from 'element-plus'
import { 配置全局消息 } from '@personal-system/app-core'
import App from './App.vue'
import { 初始化应用外壳 } from './app/bootstrap'
import router from './app/router'
import './shared/styles/element-plus'
import '@personal-system/theme/base.css'
import 'virtual:uno.css'
import './shared/styles/app.css'

const app = createApp(App)
const pinia = createPinia()

配置全局消息()
app.use(ElLoading)
app.use(pinia)
app.use(router)
void 初始化应用外壳(pinia)
app.mount('#app')
