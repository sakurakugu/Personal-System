import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import { 配置全局消息 } from '@personal-system/app-core'
import App from './App.vue'
import router from './router'
import { 初始化应用外壳 } from './app/bootstrap'
import 'element-plus/dist/index.css'
import '@personal-system/theme/base.css'
import './styles/tokens.css'
import './styles/theme.css'
import './styles/app.css'

const app = createApp(App)
const pinia = createPinia()

配置全局消息()
app.use(pinia)
app.use(ElementPlus)
app.use(router)
void 初始化应用外壳(pinia, router)
app.mount('#app')
