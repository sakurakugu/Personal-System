export type ThemeMode = 'light' | 'dark' | 'system'

export function 是否为主题模式(value: string | null): value is ThemeMode {
  return value === 'light' || value === 'dark' || value === 'system'
}

export function 解析存储的主题模式(value: string | null, fallback: ThemeMode = 'system') {
  return 是否为主题模式(value) ? value : fallback
}

export function 解析系统暗色() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export function 从模式解析是否为暗色(mode: ThemeMode, systemDark: boolean) {
  if (mode === 'system') {
    return systemDark
  }
  return mode === 'dark'
}

export function 获取主题模式标签(mode: ThemeMode) {
  if (mode === 'system') {
    return '跟随系统'
  }
  return mode === 'dark' ? '深色模式' : '浅色模式'
}

export function 获取切换后的主题模式(mode: ThemeMode, isDark: boolean): ThemeMode {
  if (mode === 'system') {
    return isDark ? 'light' : 'dark'
  }
  return mode === 'dark' ? 'light' : 'dark'
}
