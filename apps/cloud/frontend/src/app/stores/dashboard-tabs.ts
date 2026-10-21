import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import type { RouteLocationNormalizedLoaded, Router } from 'vue-router'

/** 控制台标签页数据。 */
export interface 控制台标签项 {
  /** 标签唯一标识，用于 KeepAlive 缓存键与交互定位。 */
  id: string
  /** 路由路径（不含查询参数），用于判断标签是否已打开。 */
  path: string
  /** 完整路径（含查询参数），切换标签时用于还原页面地址。 */
  fullPath: string
  /** 标签标题，取自路由 meta.title。 */
  title: string
  /** 页面标识（末级路由记录的 path 模板），用于判断同一标签内是否切换了页面。 */
  页面标识: string
  /** 页面实例版本，页面标识变化或标签刷新时递增，KeepAlive 据此强制重建。 */
  实例版本: number
}

/** 标签页本地持久化结构。 */
interface 标签持久化数据 {
  tabs?: Array<{ path?: unknown; fullPath?: unknown }>
  activePath?: unknown
}

/** 本地持久化存储键。 */
const 标签存储键 = 'dashboard_tabs'

/** 标签全部关闭后回到的默认页面。 */
export const 控制台默认标签路径 = '/dashboard/stats/blog'

/** KeepAlive 缓存上限，关闭标签后的缓存会在这个上限内自然淘汰。 */
export const 控制台标签缓存上限 = 12

/** 标签 ID 自增序号，仅用于生成唯一 id，不参与持久化。 */
let 标签序号 = 0

/**
 * 控制台多标签存储。
 *
 * 设计要点：
 * - 标签通过路径识别，路由变化由 同步路由 落回标签（已存在则激活，不存在则替换当前标签内容）。
 * - 每个标签维护页面标识与实例版本，KeepAlive 以 `标签 id + 页面标识 + 实例版本` 作为缓存键：
 *   切换标签能命中缓存保留状态；刷新标签或同一标签换了页面时缓存键变化，页面会重新创建。
 * - 状态先由调用方完成路由导航，导航成功后再调用 应用关闭标签 等落状态，守卫取消时标签不会误删。
 */
export const 使用控制台标签存储 = defineStore('dashboard-tabs', () => {
  const tabs = ref<控制台标签项[]>([])
  const activeTabId = ref('')
  const 是否已初始化 = ref(false)

  /** 初始化时保存的路由实例，用于标题解析与路径合法性校验。 */
  let 路由实例: Router | null = null

  const 活跃标签 = computed(() => (
    tabs.value.find((标签) => 标签.id === activeTabId.value) ?? null
  ))

  /** 读取路由记录标题，优先使用 meta.title。 */
  function 读取路由标题(记录: { meta?: Record<PropertyKey, unknown>; name?: unknown; path?: string }): string {
    const 标题 = 记录.meta?.title
    if (typeof 标题 === 'string' && 标题.trim()) {
      return 标题
    }
    if (typeof 记录.name === 'string') {
      return 记录.name
    }
    return '未命名页面'
  }

  /** 解析并校验一个后台路由路径，非法（非 /dashboard 子页）时返回 null。 */
  function 解析后台路由(路径: string) {
    if (!路由实例) {
      return null
    }
    try {
      const 解析结果 = 路由实例.resolve(路径)
      const 末级记录 = 解析结果.matched[解析结果.matched.length - 1]
      // 排除 /dashboard 外壳与 /dashboard/stats 之类的重定向记录，只接受真正的后台子页面
      if (!解析结果.path.startsWith('/dashboard/')) {
        return null
      }
      // 未匹配到具体子路由时 vue-router 会命中全局 404 通配记录，这里要求必须挂在 /dashboard 父路由下
      if (!解析结果.matched.some((记录) => 记录.path === '/dashboard')) {
        return null
      }
      if (!末级记录 || 末级记录.redirect !== undefined || !末级记录.components?.default) {
        return null
      }
      return 解析结果
    } catch {
      return null
    }
  }

  /** 取路径对应的页面标识（例如 /dashboard/articles/edit/:id?）。 */
  function 解析页面标识(路径: string): string {
    const 解析结果 = 解析后台路由(路径)
    const 末级记录 = 解析结果?.matched[解析结果.matched.length - 1]
    return 末级记录?.path ?? 路径
  }

  function 创建标签(解析结果: { path: string }, 完整路径: string, 标题: string): 控制台标签项 {
    标签序号 += 1
    return {
      id: `dashboard-tab-${标签序号}`,
      path: 解析结果.path,
      fullPath: 完整路径,
      title: 标题,
      页面标识: 解析页面标识(解析结果.path),
      实例版本: 0,
    }
  }

  /** 根据路径查找已打开的标签。 */
  function 根据路径获取标签(路径: string): 控制台标签项 | null {
    return tabs.value.find((标签) => 标签.path === 路径) ?? null
  }

  /** 根据 id 查找标签。 */
  function 获取标签(标签ID: string): 控制台标签项 | null {
    return tabs.value.find((标签) => 标签.id === 标签ID) ?? null
  }

  /** 读取 localStorage 中的标签并校验，失效路径丢弃。 */
  function 读取持久化数据() {
    let 原始数据: string
    try {
      原始数据 = window.localStorage.getItem(标签存储键) ?? ''
    } catch {
      return
    }
    if (!原始数据) {
      return
    }

    try {
      const 数据 = JSON.parse(原始数据) as 标签持久化数据
      const 已收录路径 = new Set<string>()
      const 恢复标签: 控制台标签项[] = []

      for (const 项 of 数据.tabs ?? []) {
        const 完整路径 = typeof 项?.fullPath === 'string'
          ? 项.fullPath
          : (typeof 项?.path === 'string' ? 项.path : '')
        if (!完整路径) {
          continue
        }
        const 解析结果 = 解析后台路由(完整路径)
        if (!解析结果 || 已收录路径.has(解析结果.path)) {
          continue
        }
        已收录路径.add(解析结果.path)
        恢复标签.push(创建标签(解析结果, 完整路径, 读取路由标题(解析结果)))
      }

      tabs.value = 恢复标签
      const 活跃路径 = typeof 数据.activePath === 'string' ? 数据.activePath : ''
      const 活跃目标 = 恢复标签.find((标签) => (
        标签.fullPath === 活跃路径 || 标签.path === 活跃路径
      ))
      activeTabId.value = (活跃目标 ?? 恢复标签[0])?.id ?? ''
    } catch (错误) {
      console.warn('恢复控制台标签失败，已忽略本地缓存', 错误)
    }
  }

  /** 写入 localStorage，仅在初始化完成后生效，避免恢复过程覆盖缓存。 */
  function 保存持久化数据() {
    if (!是否已初始化.value) {
      return
    }
    try {
      const 数据: 标签持久化数据 = {
        tabs: tabs.value.map((标签) => ({ path: 标签.path, fullPath: 标签.fullPath })),
        activePath: 活跃标签.value?.fullPath ?? '',
      }
      window.localStorage.setItem(标签存储键, JSON.stringify(数据))
    } catch {
      // 隐私模式等场景下 localStorage 不可用时静默忽略
    }
  }

  watch([tabs, activeTabId], 保存持久化数据, { deep: true })

  /**
   * 初始化标签：首次调用时恢复本地缓存，并确保当前 URL 对应的标签存在。
   * 当前 URL 不在缓存中时作为新标签加入。
   */
  function 初始化(router实例: Router, route: RouteLocationNormalizedLoaded) {
    路由实例 = router实例
    if (!是否已初始化.value) {
      是否已初始化.value = true
      读取持久化数据()
    }

    const 解析结果 = 解析后台路由(route.path)
    if (!解析结果) {
      return
    }

    const 已存在标签 = 根据路径获取标签(解析结果.path)
    if (已存在标签) {
      已存在标签.fullPath = route.fullPath
      activeTabId.value = 已存在标签.id
      return
    }

    const 标签 = 创建标签(解析结果, route.fullPath, 读取路由标题(route))
    tabs.value.push(标签)
    activeTabId.value = 标签.id
  }

  /**
   * 路由变化后同步标签：
   * - 目标路径已有标签：激活该标签；
   * - 没有标签：替换当前激活标签的内容（侧栏/顶栏普通导航的默认行为）。
   */
  function 同步路由(route: RouteLocationNormalizedLoaded) {
    if (!是否已初始化.value) {
      return
    }
    const 解析结果 = 解析后台路由(route.path)
    if (!解析结果) {
      return
    }

    const 标题 = 读取路由标题(route)
    const 已存在标签 = 根据路径获取标签(解析结果.path)
    if (已存在标签) {
      已存在标签.fullPath = route.fullPath
      已存在标签.title = 标题
      activeTabId.value = 已存在标签.id
      return
    }

    const 当前标签 = 活跃标签.value
    if (!当前标签) {
      const 标签 = 创建标签(解析结果, route.fullPath, 标题)
      tabs.value.push(标签)
      activeTabId.value = 标签.id
      return
    }

    const 新页面标识 = 解析页面标识(解析结果.path)
    if (当前标签.页面标识 !== 新页面标识) {
      // 同一标签内换成了另一个页面，递增版本让 KeepAlive 重建而不是复用旧页面实例
      当前标签.实例版本 += 1
      当前标签.页面标识 = 新页面标识
    }
    当前标签.path = 解析结果.path
    当前标签.fullPath = route.fullPath
    当前标签.title = 标题
  }

  /** 新增标签（不立即激活，等路由切换后由 同步路由 激活）；路径已打开时直接返回已有标签。 */
  function 新增标签(路径: string = 控制台默认标签路径): 控制台标签项 | null {
    const 解析结果 = 解析后台路由(路径)
    if (!解析结果) {
      return null
    }
    const 已存在标签 = 根据路径获取标签(解析结果.path)
    if (已存在标签) {
      return 已存在标签
    }
    const 标签 = 创建标签(解析结果, 路径, 读取路由标题(解析结果))
    tabs.value.push(标签)
    return 标签
  }

  /** 激活标签，仅修改高亮状态，路由切换由调用方负责。 */
  function 设置活跃标签(标签ID: string): 控制台标签项 | null {
    const 标签 = 获取标签(标签ID)
    if (!标签) {
      return null
    }
    activeTabId.value = 标签.id
    return 标签
  }

  /**
   * 计算关闭某个标签后的导航目标（纯计算，不修改状态）。
   * 调用方先按目标导航，导航成功后再调用 应用关闭标签。
   */
  function 计算关闭结果(标签ID: string): { 是激活标签: boolean; 目标完整路径: string } | null {
    const 索引 = tabs.value.findIndex((标签) => 标签.id === 标签ID)
    if (索引 < 0) {
      return null
    }
    if (activeTabId.value !== 标签ID) {
      return { 是激活标签: false, 目标完整路径: '' }
    }

    const 剩余标签 = tabs.value.filter((标签) => 标签.id !== 标签ID)
    const 下一个标签 = 剩余标签[索引 - 1] ?? 剩余标签[索引] ?? null
    if (下一个标签) {
      return { 是激活标签: true, 目标完整路径: 下一个标签.fullPath }
    }
    return { 是激活标签: true, 目标完整路径: 控制台默认标签路径 }
  }

  /**
   * 应用关闭标签：移除标签并调整激活项。
   * 全部关闭时保留一个默认标签（复用原对象，避免 KeepAlive 缓存键无意义抖动）。
   */
  function 应用关闭标签(标签ID: string): 控制台标签项 | null {
    const 索引 = tabs.value.findIndex((标签) => 标签.id === 标签ID)
    if (索引 < 0) {
      return null
    }

    const 被关闭标签 = tabs.value[索引]
    const 关闭的是激活标签 = activeTabId.value === 标签ID
    tabs.value.splice(索引, 1)

    if (tabs.value.length === 0) {
      const 解析结果 = 解析后台路由(控制台默认标签路径)
      被关闭标签.path = 控制台默认标签路径
      被关闭标签.fullPath = 控制台默认标签路径
      被关闭标签.title = 解析结果 ? 读取路由标题(解析结果) : '博客统计'
      被关闭标签.页面标识 = 解析页面标识(控制台默认标签路径)
      tabs.value = [被关闭标签]
      activeTabId.value = 被关闭标签.id
      return 被关闭标签
    }

    if (关闭的是激活标签) {
      const 下一个标签 = tabs.value[Math.max(索引 - 1, 0)] ?? tabs.value[0]
      activeTabId.value = 下一个标签.id
      return 下一个标签
    }
    return 活跃标签.value
  }

  /** 只保留指定标签（关闭其他）。 */
  function 保留单个标签(标签ID: string): 控制台标签项 | null {
    const 标签 = 获取标签(标签ID)
    if (!标签) {
      return null
    }
    tabs.value = [标签]
    activeTabId.value = 标签.id
    return 标签
  }

  /** 关闭指定标签右侧的所有标签；若激活标签被关闭则激活指定标签。 */
  function 关闭右侧标签(标签ID: string): 控制台标签项 | null {
    const 索引 = tabs.value.findIndex((标签) => 标签.id === 标签ID)
    if (索引 < 0) {
      return null
    }
    const 激活标签仍在范围内 = tabs.value.findIndex((标签) => 标签.id === activeTabId.value) <= 索引
    tabs.value = tabs.value.slice(0, 索引 + 1)
    if (!激活标签仍在范围内) {
      activeTabId.value = tabs.value[索引].id
    }
    return 活跃标签.value
  }

  /** 判断关闭指定标签右侧标签时，当前激活标签是否会被一起关闭。 */
  function 关闭右侧会涉及激活标签(标签ID: string): boolean {
    const 索引 = tabs.value.findIndex((标签) => 标签.id === 标签ID)
    const 激活索引 = tabs.value.findIndex((标签) => 标签.id === activeTabId.value)
    return 索引 >= 0 && 激活索引 > 索引
  }

  /** 刷新标签：递增实例版本，KeepAlive 缓存键变化后页面会重新创建。 */
  function 刷新标签(标签ID: string): 控制台标签项 | null {
    const 标签 = 获取标签(标签ID)
    if (!标签) {
      return null
    }
    标签.实例版本 += 1
    return 标签
  }

  return {
    tabs,
    activeTabId,
    activeTab: 活跃标签,
    init: 初始化,
    syncRoute: 同步路由,
    addTab: 新增标签,
    setActiveTab: 设置活跃标签,
    getTabByPath: 根据路径获取标签,
    getTabById: 获取标签,
    planCloseTab: 计算关闭结果,
    applyCloseTab: 应用关闭标签,
    keepOnlyTab: 保留单个标签,
    closeTabsToRight: 关闭右侧标签,
    closeRightTouchesActive: 关闭右侧会涉及激活标签,
    refreshTab: 刷新标签,
  }
})
