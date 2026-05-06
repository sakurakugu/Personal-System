import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import App from './App.vue'
import router from './router'
import { initializeAppShell } from './app/bootstrap'
import 'element-plus/dist/index.css'
import './styles/tokens.css'
import './styles/app.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(ElementPlus)
app.use(router)

async function bootstrap() {
  try {
    await initializeAppShell(pinia)
  } catch (error) {
    console.error('桌面端初始化失败', error)
  } finally {
    app.mount('#app')
  }
}

void bootstrap()
