import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import App from './App.vue'
import router from './router'
import { initializeAppShell } from './app/bootstrap'
import 'element-plus/dist/index.css'
import './styles/app.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(ElementPlus)
app.use(router)
void initializeAppShell(pinia, router)
app.mount('#app')
