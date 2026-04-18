import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { ElLoading } from 'element-plus'
import App from './App.vue'
import { initializeAppShell } from './app/bootstrap'
import router from './router'
import './styles/element-plus'
import './styles/app.css'

const app = createApp(App)
const pinia = createPinia()

app.use(ElLoading)
app.use(pinia)
app.use(router)
void initializeAppShell(pinia, router)
app.mount('#app')
