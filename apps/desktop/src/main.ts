import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import { 配置全局消息 } from '@personal-system/app-core'
import App from './App.vue'
import router from './router'
import { 初始化应用外壳 } from './app/bootstrap'
import 'element-plus/dist/index.css'
import '@personal-system/theme/base.css'
import 'virtual:uno.css'
import './styles/tokens.css'
import './styles/app.css'

const app = createApp(App)
const pinia = createPinia()

配置全局消息()
app.use(pinia)
app.use(ElementPlus)
app.use(router)

async function bootstrap() {
  try {
    await 初始化应用外壳(pinia)
  } catch (error) {
    console.error('桌面端初始化失败', error)
  } finally {
    app.mount('#app')
  }
}

void bootstrap()
