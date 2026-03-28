import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import { initializeAppShell } from './app/bootstrap'
import router from './router'
import './styles/app.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus)
void initializeAppShell(pinia)
app.mount('#app')
