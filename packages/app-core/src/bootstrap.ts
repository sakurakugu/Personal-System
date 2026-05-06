export interface ThemeStoreLike {
  initTheme: () => void
  initHue: () => void
  listenToSystemTheme: () => void
}

export interface BootstrapTaskState {
  task: Promise<void> | null
}

export function initializeThemeStore(themeStore: ThemeStoreLike): void {
  themeStore.initTheme()
  themeStore.initHue()
  themeStore.listenToSystemTheme()
}

export function runBootstrapTaskOnce(
  state: BootstrapTaskState,
  initializer: () => Promise<void>,
): Promise<void> {
  if (!state.task) {
    state.task = initializer()
  }
  return state.task
}
