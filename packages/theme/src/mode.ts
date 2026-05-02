export type ThemeMode = 'light' | 'dark' | 'system'

export function isThemeMode(value: string | null): value is ThemeMode {
  return value === 'light' || value === 'dark' || value === 'system'
}

export function parseStoredThemeMode(value: string | null, fallback: ThemeMode = 'system') {
  return isThemeMode(value) ? value : fallback
}

export function resolveSystemDark() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export function resolveIsDarkFromMode(mode: ThemeMode, systemDark: boolean) {
  if (mode === 'system') {
    return systemDark
  }
  return mode === 'dark'
}

export function getThemeModeLabel(mode: ThemeMode) {
  if (mode === 'system') {
    return '跟随系统'
  }
  return mode === 'dark' ? '深色模式' : '浅色模式'
}

export function getToggledThemeMode(mode: ThemeMode, isDark: boolean): ThemeMode {
  if (mode === 'system') {
    return isDark ? 'light' : 'dark'
  }
  return mode === 'dark' ? 'light' : 'dark'
}
