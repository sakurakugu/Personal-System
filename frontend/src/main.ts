import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { initializeAppShell } from './app/bootstrap'
import router from './router'
import './styles/element-plus'
import './styles/app.css'
import { setupMdEditorConfig } from './utils/mdEditor'

const app = createApp(App)
const pinia = createPinia()

setupMdEditorConfig()
app.use(pinia)
app.use(router)
void initializeAppShell(pinia, router)
app.mount('#app')
