export interface ThemeStoreLike {
  initTheme: () => void
  initHue: () => void
  listenToSystemTheme: () => void
}

export interface BootstrapTaskState {
  task: Promise<void> | null
}

export function 初始化主题存储(themeStore: ThemeStoreLike): void {
  themeStore.initTheme()
  themeStore.initHue()
  themeStore.listenToSystemTheme()
}

export function 仅运行一次引导任务(
  state: BootstrapTaskState,
  initializer: () => Promise<void>,
): Promise<void> {
  if (!state.task) {
    state.task = initializer()
  }
  return state.task
}
