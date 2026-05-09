import { useRouter } from 'vue-router'
import { useDesktopTabsStore } from '../stores/tabs'

export interface OpenDesktopRouteOptions {
  newTab?: boolean
  preserveCurrentTab?: boolean
  replace?: boolean
}

export function useDesktopRouteTabs() {
  const router = useRouter()
  const tabsStore = useDesktopTabsStore()

  async function openDesktopRoute(path: string, options: OpenDesktopRouteOptions = {}) {
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
    openDesktopRoute,
  }
}
