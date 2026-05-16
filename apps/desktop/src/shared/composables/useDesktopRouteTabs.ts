import { useRouter } from 'vue-router'
import { 使用桌面标签存储 } from '../stores/tabs'

export interface OpenDesktopRouteOptions {
  newTab?: boolean
  preserveCurrentTab?: boolean
  replace?: boolean
}

export function 使用桌面路由标签() {
  const router = useRouter()
  const tabsStore = 使用桌面标签存储()

  async function 打开桌面路由(path: string, options: OpenDesktopRouteOptions = {}) {
    if (options.newTab) {
      tabsStore.addTab(path)
    } else if (options.preserveCurrentTab) {
      tabsStore.openRoute(path)
    }

    if (router.currentRoute.value.path === path) {
      return
    }

    if (options.replace) {
      await router.replace(path)
      return
    }

    await router.push(path)
  }

  return {
    打开桌面路由,
  }
}
