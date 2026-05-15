import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import { initializeAppShell } from './app/bootstrap'
import DesktopWidgetPage from './modules/widget/pages/DesktopWidgetPage.vue'
import 'element-plus/dist/index.css'
import '@personal-system/theme/base.css'
import './styles/tokens.css'
import './styles/app.css'

const app = createApp(DesktopWidgetPage)
const pinia = createPinia()

app.use(pinia)
app.use(ElementPlus)

async function bootstrap() {
  try {
    await initializeAppShell(pinia)
  } catch (error) {
    console.error('桌面小工具初始化失败', error)
  } finally {
    app.mount('#app')
  }
}

void bootstrap()
