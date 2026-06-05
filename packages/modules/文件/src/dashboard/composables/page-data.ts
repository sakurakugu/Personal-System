import { onBeforeUnmount, ref, watch, type ComputedRef, type Ref } from 'vue'
import type {
  FileExplorerData,
  FileSearchData,
  FileTrashData,
} from '../../types'
import {
  刷新当前视图数据,
  执行全局搜索 as 执行全局搜索动作,
  应用资源数据 as 应用资源数据动作,
  拉取回收站数据,
  拉取资源数据,
  重置全局搜索结果 as 重置全局搜索结果动作,
} from '../../core/data-actions'
import type {
  搜索范围,
} from '../../core/shared'

export function 使用文件页面数据(options: {
  搜索关键词: Ref<string> | ComputedRef<string>
  搜索范围值: Ref<搜索范围> | ComputedRef<搜索范围>
  是否全局搜索模式: Ref<boolean> | ComputedRef<boolean>
  清空选择: () => void
}) {
  const 资源数据 = ref<FileExplorerData | null>(null)
  const 首次加载中 = ref(true)
  const 刷新中 = ref(false)
  const 全局搜索中 = ref(false)
  const 全局搜索结果 = ref<FileSearchData>({ folders: [], files: [] })
  const 回收站数据 = ref<FileTrashData>({ items: [] })
  const 当前目录ID = ref<string | null>(null)
  let 全局搜索定时器: number | null = null
  let 全局搜索序号 = 0

  function 应用资源数据(data: FileExplorerData) {
    应用资源数据动作({
      data,
      设置资源数据: (nextData) => {
        资源数据.value = nextData
      },
      设置当前目录ID: (folderId) => {
        当前目录ID.value = folderId
      },
      清空选择: options.清空选择,
    })
  }

  async function 拉取资源(folderId: string | null = 当前目录ID.value, config: { 静默?: boolean } = {}) {
    await 拉取资源数据({
      folderId,
      静默: config.静默 ?? false,
      应用资源数据,
      设置刷新中: (value) => {
        刷新中.value = value
      },
      设置首次加载中: (value) => {
        首次加载中.value = value
      },
    })
  }

  async function 拉取回收站() {
    await 拉取回收站数据({
      设置回收站数据: (data) => {
        回收站数据.value = data
      },
      设置刷新中: (value) => {
        刷新中.value = value
      },
      清空选择: options.清空选择,
    })
  }

  function 重置全局搜索结果() {
    重置全局搜索结果动作({
      设置全局搜索中: (value) => {
        全局搜索中.value = value
      },
      设置全局搜索结果: (data) => {
        全局搜索结果.value = data
      },
    })
  }

  async function 执行全局搜索(keyword: string, requestId: number) {
    await 执行全局搜索动作({
      keyword,
      requestId,
      获取当前请求序号: () => 全局搜索序号,
      设置全局搜索中: (value) => {
        全局搜索中.value = value
      },
      设置全局搜索结果: (data) => {
        全局搜索结果.value = data
      },
    })
  }

  async function 刷新当前视图(folderId: string | null = 当前目录ID.value) {
    await 刷新当前视图数据({
      folderId,
      是否全局搜索模式: options.是否全局搜索模式.value,
      keyword: options.搜索关键词.value,
      拉取资源,
      重置全局搜索结果,
      设置全局搜索中: (value) => {
        全局搜索中.value = value
      },
      创建全局搜索请求: () => {
        全局搜索序号 += 1
        return 全局搜索序号
      },
      执行全局搜索,
    })
  }

  watch([options.搜索关键词, options.搜索范围值], ([keyword, scope]) => {
    if (全局搜索定时器 !== null) {
      window.clearTimeout(全局搜索定时器)
      全局搜索定时器 = null
    }

    全局搜索序号 += 1
    const requestId = 全局搜索序号
    if (scope !== 'global') {
      重置全局搜索结果()
      return
    }

    const normalizedKeyword = keyword.trim()
    if (!normalizedKeyword) {
      重置全局搜索结果()
      return
    }

    全局搜索中.value = true
    全局搜索定时器 = window.setTimeout(() => {
      全局搜索定时器 = null
      void 执行全局搜索(normalizedKeyword, requestId)
    }, 280)
  })

  onBeforeUnmount(() => {
    if (全局搜索定时器 !== null) {
      window.clearTimeout(全局搜索定时器)
      全局搜索定时器 = null
    }
  })

  return {
    资源数据,
    首次加载中,
    刷新中,
    全局搜索中,
    全局搜索结果,
    回收站数据,
    当前目录ID,
    拉取资源,
    拉取回收站,
    刷新当前视图,
  }
}
