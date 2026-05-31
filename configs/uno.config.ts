import { defineConfig, presetWind3 } from 'unocss'

export default defineConfig({
  presets: [
    presetWind3(),
  ],
  shortcuts: {
    'ps-panel': 'border border-[var(--theme-card-border)] bg-[var(--theme-card-bg)] shadow-[var(--theme-card-shadow)]',
    'ps-field': 'border border-[var(--theme-input-border)] bg-[var(--theme-input-bg)] text-[var(--text-primary)]',
    'ps-focus-ring': 'focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-[var(--theme-focus-ring)]',
  },
  theme: {
    colors: {
      primary: 'var(--el-color-primary)',
      'primary-soft': 'var(--theme-accent-soft)',
      card: 'var(--theme-card-bg)',
      panel: 'var(--theme-panel-soft)',
      text: {
        primary: 'var(--text-primary)',
        secondary: 'var(--text-secondary)',
        tertiary: 'var(--text-tertiary)',
      },
      danger: 'var(--theme-danger-strong)',
      success: 'var(--theme-success-strong)',
    },
    borderRadius: {
      app: 'var(--app-button-radius)',
    },
  },
})
