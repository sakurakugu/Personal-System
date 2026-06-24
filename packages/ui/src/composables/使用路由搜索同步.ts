import { watch, type Ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

interface 使用路由搜索同步选项 {
  queryKey?: string
  trim?: boolean
  replace?: boolean
}

function 读取查询字符串(value: unknown): string {
  if (typeof value === 'string') {
    return value
  }
  if (Array.isArray(value)) {
    return typeof value[0] === 'string' ? value[0] : ''
  }
  return ''
}

export function 使用路由搜索同步(
  搜索词: Ref<string>,
  options: 使用路由搜索同步选项 = {},
) {
  const route = useRoute()
  const router = useRouter()
  const queryKey = options.queryKey ?? 'search'
  const shouldTrim = options.trim ?? true
  const shouldReplace = options.replace ?? true

  function 标准化搜索词(value: string) {
    return shouldTrim ? value.trim() : value
  }

  function 同步路由到搜索词() {
    const routeValue = 读取查询字符串(route.query[queryKey])
    if (搜索词.value === routeValue) {
      return
    }
    搜索词.value = routeValue
  }

  function 同步搜索词到路由(value: string) {
    const keyword = 标准化搜索词(value)
    const query = { ...route.query }

    if (keyword) {
      query[queryKey] = keyword
    } else {
      delete query[queryKey]
    }

    const target = { path: route.path, query }
    const targetFullPath = router.resolve(target).fullPath
    if (targetFullPath === route.fullPath) {
      return
    }

    if (shouldReplace) {
      void router.replace(target)
      return
    }
    void router.push(target)
  }

  watch(
    () => route.query[queryKey],
    () => {
      同步路由到搜索词()
    },
    { immediate: true },
  )

  watch(搜索词, (value, oldValue) => {
    if (标准化搜索词(value) === 标准化搜索词(oldValue)) {
      return
    }
    同步搜索词到路由(value)
  })
}
