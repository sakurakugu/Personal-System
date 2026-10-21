/**
 * 控制台标签切换的一次性标记。
 *
 * 切换标签本质上是路由跳转，但被 KeepAlive 保留的页面不应该把它当成“真正离开”
 * （例如文章编辑页会因此弹出未保存确认、并按全局路由重置表单）。
 * 这里在切换标签导航前写入一次性标记，被保活页面在离开守卫里读取并消费该标记。
 *
 * 键名与 packages/modules/文章/src/dashboard/pages/文章编辑页面.vue 中的读取逻辑保持一致。
 */

/** 一次性标记的 sessionStorage 键。 */
export const 控制台标签切换标记键 = 'dashboard-tab-switch'

/** 写入标签切换标记（导航开始前调用）。 */
export function 设置控制台标签切换标记(): void {
  try {
    window.sessionStorage.setItem(控制台标签切换标记键, String(Date.now()))
  } catch {
    // sessionStorage 不可用时忽略，守卫最多退化为正常确认流程
  }
}

/** 清除标签切换标记（导航完成或取消后调用）。 */
export function 清除控制台标签切换标记(): void {
  try {
    window.sessionStorage.removeItem(控制台标签切换标记键)
  } catch {
    // 忽略不可用场景
  }
}
