import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { ElLoading } from 'element-plus'
import App from './App.vue'
import { initializeAppShell } from './app/bootstrap'
import router from './app/router'
import './shared/styles/element-plus'
import '@personal-system/theme/base.css'
import './shared/styles/app.css'

const app = createApp(App)
const pinia = createPinia()

app.use(ElLoading)
app.use(pinia)
app.use(router)
void initializeAppShell(pinia)
app.mount('#app')
