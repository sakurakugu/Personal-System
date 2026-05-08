import { computed, nextTick, ref, watch, type ComputedRef, type Ref } from 'vue'
import type { ComponentPublicInstance } from 'vue'
import type { TreeInstance } from 'element-plus'
import {
  创建列表文件夹重命名草稿,
  创建列表文件重命名草稿,
  创建新建目录草稿,
  创建右侧新建文件夹草稿,
  创建重命名目录草稿,
  是否资源处于右侧编辑态 as 是否资源处于右侧编辑态工具,
  是否资源是右侧新建文件夹草稿 as 是否资源是右侧新建文件夹草稿工具,
  是否资源正在右侧重命名 as 是否资源正在右侧重命名工具,
} from '../../core/editing'
import {
  保存文件夹创建草稿,
  保存资源重命名草稿,
  尝试聚焦现有编辑输入框,
} from '../../core/editing-actions'
import {
  处理编辑输入框失焦,
  处理编辑输入框键盘事件,
  提取输入框元素,
  聚焦输入框,
  聚焦资源行输入框,
} from '../../core/input'
import {
  右侧新建文件夹临时资源键,
  新建目录临时节点键,
} from '../../core/shared'
import type {
  右侧新建文件夹草稿,
  右键菜单状态,
  列表重命名草稿,
  文件夹展示项,
  文件展示项,
  资源展示项,
  资源标识,
  重命名目录草稿,
} from '../../core/shared'

export function useFilesPageEditing(options: {
  当前目录ID: Ref<string | null> | ComputedRef<string | null>
  当前是内容图片视图: Ref<boolean> | ComputedRef<boolean>
  当前可在右侧新建文件夹: Ref<boolean> | ComputedRef<boolean>
  当前展示资源列表: Ref<资源展示项[]> | ComputedRef<资源展示项[]>
  目录树引用: Ref<TreeInstance | null>
  获取右键菜单来源: () => 右键菜单状态['source']
  关闭右键菜单: () => void
  刷新当前视图: () => Promise<void>
  创建文件夹: (name: string, parentId: string | null) => Promise<unknown>
  重命名资源: (resource: 资源标识, name: string) => Promise<unknown>
}) {
  const 新建目录草稿状态 = ref<{
    id: string
    parentId: string | null
    name: string
  } | null>(null)
  const 正在提交新建目录 = ref(false)
  const 右侧新建文件夹草稿状态 = ref<右侧新建文件夹草稿 | null>(null)
  const 正在提交右侧新建文件夹 = ref(false)
  const 重命名目录草稿状态 = ref<重命名目录草稿 | null>(null)
  const 正在提交重命名目录 = ref(false)
  const 列表重命名草稿状态 = ref<列表重命名草稿 | null>(null)
  const 正在提交列表重命名 = ref(false)
  const 新建目录输入框 = ref<globalThis.HTMLInputElement | null>(null)
  const 重命名目录输入框 = ref<globalThis.HTMLInputElement | null>(null)
  const 列表重命名输入框 = ref<globalThis.HTMLInputElement | null>(null)
  const 右侧新建文件夹输入框 = ref<globalThis.HTMLInputElement | null>(null)

  const 新建目录名称 = computed({
    get: () => 新建目录草稿状态.value?.name ?? '',
    set: (value: string) => {
      if (!新建目录草稿状态.value) {
        return
      }
      新建目录草稿状态.value = {
        ...新建目录草稿状态.value,
        name: value,
      }
    },
  })
  const 右侧新建文件夹名称 = computed({
    get: () => 右侧新建文件夹草稿状态.value?.name ?? '',
    set: (value: string) => {
      if (!右侧新建文件夹草稿状态.value) {
        return
      }
      右侧新建文件夹草稿状态.value = {
        ...右侧新建文件夹草稿状态.value,
        name: value,
      }
    },
  })
  const 重命名目录名称 = computed({
    get: () => 重命名目录草稿状态.value?.name ?? '',
    set: (value: string) => {
      if (!重命名目录草稿状态.value) {
        return
      }
      重命名目录草稿状态.value = {
        ...重命名目录草稿状态.value,
        name: value,
      }
    },
  })
  const 列表重命名名称 = computed({
    get: () => 列表重命名草稿状态.value?.name ?? '',
    set: (value: string) => {
      if (!列表重命名草稿状态.value) {
        return
      }
      列表重命名草稿状态.value = {
        ...列表重命名草稿状态.value,
        name: value,
      }
    },
  })
  const 右侧新建文件夹资源 = computed<资源展示项 | null>(() => {
    const draft = 右侧新建文件夹草稿状态.value
    if (!draft || !options.当前可在右侧新建文件夹.value || draft.parentId !== options.当前目录ID.value) {
      return null
    }
    return {
      type: 'folder',
      id: draft.id,
      item: {
        id: draft.id,
        parent_id: draft.parentId,
        name: draft.name,
        created_at: '',
        updated_at: '',
      },
    }
  })

  function 取消新建文件夹() {
    新建目录草稿状态.value = null
    正在提交新建目录.value = false
  }

  function 取消右侧新建文件夹() {
    右侧新建文件夹草稿状态.value = null
    正在提交右侧新建文件夹.value = false
  }

  function 取消重命名目录() {
    重命名目录草稿状态.value = null
    正在提交重命名目录.value = false
  }

  function 取消列表重命名() {
    列表重命名草稿状态.value = null
    正在提交列表重命名.value = false
  }

  async function 聚焦新建目录输入框() {
    await 聚焦输入框(新建目录输入框.value)
  }

  async function 聚焦右侧新建文件夹输入框() {
    await 聚焦资源行输入框(右侧新建文件夹输入框.value)
  }

  async function 聚焦重命名目录输入框() {
    await 聚焦输入框(重命名目录输入框.value)
  }

  async function 聚焦列表重命名输入框() {
    await 聚焦资源行输入框(列表重命名输入框.value)
  }

  async function 尝试聚焦已有编辑输入() {
    return 尝试聚焦现有编辑输入框({
      当前目录ID: options.当前目录ID.value,
      当前可在右侧新建文件夹: options.当前可在右侧新建文件夹.value,
      当前展示资源列表: options.当前展示资源列表.value,
      右侧新建文件夹草稿: 右侧新建文件夹草稿状态.value,
      新建目录草稿: 新建目录草稿状态.value,
      重命名目录草稿: 重命名目录草稿状态.value,
      列表重命名草稿: 列表重命名草稿状态.value,
      聚焦右侧新建文件夹输入框,
      聚焦新建目录输入框,
      聚焦重命名目录输入框,
      聚焦列表重命名输入框,
      取消右侧新建文件夹,
      取消列表重命名,
    })
  }

  async function 新建文件夹() {
    options.关闭右键菜单()
    if (await 尝试聚焦已有编辑输入()) {
      return
    }

    const parentId = options.当前是内容图片视图.value ? null : options.当前目录ID.value
    新建目录草稿状态.value = 创建新建目录草稿(新建目录临时节点键, parentId)

    if (parentId) {
      await nextTick()
      options.目录树引用.value?.getNode(parentId)?.expand()
    }

    await 聚焦新建目录输入框()
  }

  async function 在右侧新建文件夹() {
    options.关闭右键菜单()
    if (!options.当前可在右侧新建文件夹.value) {
      await 新建文件夹()
      return
    }
    if (await 尝试聚焦已有编辑输入()) {
      return
    }

    右侧新建文件夹草稿状态.value = 创建右侧新建文件夹草稿(
      右侧新建文件夹临时资源键,
      options.当前目录ID.value,
    )

    await 聚焦右侧新建文件夹输入框()
  }

  function 设置右侧新建文件夹输入框引用(element: globalThis.Element | ComponentPublicInstance | null) {
    右侧新建文件夹输入框.value = 提取输入框元素(element)
  }

  function 设置列表重命名输入框引用(element: globalThis.Element | ComponentPublicInstance | null) {
    列表重命名输入框.value = 提取输入框元素(element)
  }

  async function 保存右侧新建文件夹() {
    await 保存文件夹创建草稿({
      草稿: 右侧新建文件夹草稿状态.value,
      正在提交: 正在提交右侧新建文件夹.value,
      设置正在提交: (value) => {
        正在提交右侧新建文件夹.value = value
      },
      取消编辑: 取消右侧新建文件夹,
      清空草稿: () => {
        右侧新建文件夹草稿状态.value = null
      },
      创建文件夹: options.创建文件夹,
      刷新当前视图: options.刷新当前视图,
      重新聚焦输入框: 聚焦右侧新建文件夹输入框,
    })
  }

  async function 保存新建文件夹() {
    await 保存文件夹创建草稿({
      草稿: 新建目录草稿状态.value,
      正在提交: 正在提交新建目录.value,
      设置正在提交: (value) => {
        正在提交新建目录.value = value
      },
      取消编辑: 取消新建文件夹,
      清空草稿: () => {
        新建目录草稿状态.value = null
      },
      创建文件夹: options.创建文件夹,
      刷新当前视图: options.刷新当前视图,
      重新聚焦输入框: 聚焦新建目录输入框,
    })
  }

  async function 处理新建目录输入框失焦() {
    await 处理编辑输入框失焦(正在提交新建目录.value, 保存新建文件夹)
  }

  async function 处理右侧新建文件夹输入框失焦() {
    await 处理编辑输入框失焦(正在提交右侧新建文件夹.value, 保存右侧新建文件夹)
  }

  function 处理新建目录键盘事件(event: globalThis.KeyboardEvent) {
    处理编辑输入框键盘事件(event, () => {
      void 保存新建文件夹()
    }, 取消新建文件夹)
  }

  function 处理右侧新建文件夹键盘事件(event: globalThis.KeyboardEvent) {
    处理编辑输入框键盘事件(event, () => {
      void 保存右侧新建文件夹()
    }, 取消右侧新建文件夹)
  }

  async function 重命名文件夹(folder: 文件夹展示项) {
    const menuSource = options.获取右键菜单来源()
    options.关闭右键菜单()
    if (await 尝试聚焦已有编辑输入()) {
      return
    }
    if (menuSource === 'tree') {
      重命名目录草稿状态.value = 创建重命名目录草稿(folder)
      await 聚焦重命名目录输入框()
      return
    }
    列表重命名草稿状态.value = 创建列表文件夹重命名草稿(folder)
    await 聚焦列表重命名输入框()
  }

  async function 保存重命名目录() {
    await 保存资源重命名草稿({
      草稿: 重命名目录草稿状态.value,
      正在提交: 正在提交重命名目录.value,
      设置正在提交: (value) => {
        正在提交重命名目录.value = value
      },
      取消编辑: 取消重命名目录,
      清空草稿: () => {
        重命名目录草稿状态.value = null
      },
      获取资源类型: () => 'folder',
      获取成功文案: () => '文件夹已重命名',
      获取失败文案: () => '重命名文件夹失败',
      重命名资源: options.重命名资源,
      刷新当前视图: options.刷新当前视图,
      重新聚焦输入框: 聚焦重命名目录输入框,
    })
  }

  async function 处理重命名目录输入框失焦() {
    await 处理编辑输入框失焦(正在提交重命名目录.value, 保存重命名目录)
  }

  function 处理重命名目录键盘事件(event: globalThis.KeyboardEvent) {
    处理编辑输入框键盘事件(event, () => {
      void 保存重命名目录()
    }, 取消重命名目录)
  }

  function 是否资源正在右侧重命名(resource: 资源展示项) {
    return 是否资源正在右侧重命名工具(resource, 列表重命名草稿状态.value)
  }

  function 是否资源是右侧新建文件夹草稿(resource: 资源展示项) {
    return 是否资源是右侧新建文件夹草稿工具(resource, 右侧新建文件夹草稿状态.value)
  }

  function 是否资源处于右侧编辑态(resource: 资源展示项) {
    return 是否资源处于右侧编辑态工具(
      resource,
      右侧新建文件夹草稿状态.value,
      列表重命名草稿状态.value,
    )
  }

  async function 保存右侧重命名() {
    await 保存资源重命名草稿({
      草稿: 列表重命名草稿状态.value,
      正在提交: 正在提交列表重命名.value,
      设置正在提交: (value) => {
        正在提交列表重命名.value = value
      },
      取消编辑: 取消列表重命名,
      清空草稿: () => {
        列表重命名草稿状态.value = null
      },
      获取资源类型: (draft) => draft.type,
      获取成功文案: (draft) => (draft.type === 'folder' ? '文件夹已重命名' : '文件已重命名'),
      获取失败文案: (draft) => (draft.type === 'folder' ? '重命名文件夹失败' : '重命名文件失败'),
      重命名资源: options.重命名资源,
      刷新当前视图: options.刷新当前视图,
      重新聚焦输入框: 聚焦列表重命名输入框,
    })
  }

  async function 处理右侧重命名输入框失焦() {
    await 处理编辑输入框失焦(正在提交列表重命名.value, 保存右侧重命名)
  }

  function 处理右侧重命名键盘事件(event: globalThis.KeyboardEvent) {
    处理编辑输入框键盘事件(event, () => {
      void 保存右侧重命名()
    }, 取消列表重命名)
  }

  async function 重命名文件(file: 文件展示项) {
    options.关闭右键菜单()
    if (await 尝试聚焦已有编辑输入()) {
      return
    }
    列表重命名草稿状态.value = 创建列表文件重命名草稿(file)
    await 聚焦列表重命名输入框()
  }

  watch(
    [() => options.当前目录ID.value, () => options.当前可在右侧新建文件夹.value],
    () => {
      const draft = 右侧新建文件夹草稿状态.value
      if (!draft) {
        return
      }
      if (!options.当前可在右侧新建文件夹.value || draft.parentId !== options.当前目录ID.value) {
        取消右侧新建文件夹()
      }
    },
  )

  return {
    新建目录输入框,
    重命名目录输入框,
    新建目录草稿状态,
    正在提交新建目录,
    右侧新建文件夹草稿状态,
    正在提交右侧新建文件夹,
    重命名目录草稿状态,
    正在提交重命名目录,
    列表重命名草稿状态,
    正在提交列表重命名,
    新建目录名称,
    右侧新建文件夹名称,
    重命名目录名称,
    列表重命名名称,
    右侧新建文件夹资源,
    新建文件夹,
    在右侧新建文件夹,
    取消右侧新建文件夹,
    设置右侧新建文件夹输入框引用,
    设置列表重命名输入框引用,
    保存右侧新建文件夹,
    保存新建文件夹,
    处理新建目录输入框失焦,
    处理右侧新建文件夹输入框失焦,
    处理新建目录键盘事件,
    处理右侧新建文件夹键盘事件,
    重命名文件夹,
    处理重命名目录输入框失焦,
    处理重命名目录键盘事件,
    是否资源正在右侧重命名,
    是否资源是右侧新建文件夹草稿,
    是否资源处于右侧编辑态,
    保存右侧重命名,
    处理右侧重命名输入框失焦,
    处理右侧重命名键盘事件,
    重命名文件,
  }
}
