import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  applyThemeHueToRoot,
  createRgbCssFromOklch,
  getThemeModeLabel,
  getToggledThemeMode,
  normalizeHue,
  parseStoredHue,
  parseStoredThemeMode,
  resolveIsDarkFromMode,
  resolveSystemDark,
  type OklchColorToken,
  type ThemeMode,
} from '@personal-system/theme'

const DEFAULT_HUE = 0
const FRONTEND_PRIMARY_RGB_TOKEN: OklchColorToken = { lightness: 0.62, chroma: 0.14 }

const CLICK_EFFECT_COLOR_STOPS = {
  light: [
    [0.62, 0.16],
    [0.72, 0.14],
    [0.82, 0.1],
    [0.9, 0.05],
  ],
  dark: [
    [0.76, 0.16],
    [0.82, 0.13],
    [0.88, 0.09],
    [0.94, 0.04],
  ],
} as const

export function getThemeClickEffectColors(hueValue: number, isDark: boolean) {
  const selectionHue = normalizeHue(hueValue)
  const colorStops = isDark
    ? CLICK_EFFECT_COLOR_STOPS.dark
    : CLICK_EFFECT_COLOR_STOPS.light
  return colorStops.map(([lightness, chroma]) =>
    createRgbCssFromOklch({ lightness, chroma }, selectionHue),
  )
}

function applyHue(hueValue: number) {
  return applyThemeHueToRoot({
    hueValue,
    primaryRgbToken: FRONTEND_PRIMARY_RGB_TOKEN,
  })
}

export const useThemeStore = defineStore("theme", () => {
  const mode = ref<ThemeMode>('system')
  const isDark = ref(false);
  const clickEffectEnabled = ref(true);
  const hue = ref(DEFAULT_HUE);
  let mediaQuery: MediaQueryList | null = null;

  function initTheme() {
    mode.value = parseStoredThemeMode(localStorage.getItem('theme'))
    localStorage.setItem('theme', mode.value)
    syncThemeFromMode()

    const savedClickEffect = localStorage.getItem("clickEffectEnabled");
    clickEffectEnabled.value = savedClickEffect !== "false";
  }

  function applyTheme() {
    if (isDark.value) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }

  function syncThemeFromMode() {
    isDark.value = resolveIsDarkFromMode(mode.value, resolveSystemDark())
    applyTheme()
  }

  function toggleTheme() {
    setMode(getToggledThemeMode(mode.value, isDark.value))
  }

  function setMode(nextMode: ThemeMode) {
    mode.value = nextMode
    localStorage.setItem('theme', nextMode)
    syncThemeFromMode()
  }

  function handleSystemThemeChange(event: MediaQueryListEvent) {
    if (mode.value !== 'system') {
      return;
    }
    isDark.value = event.matches;
    applyTheme();
  }

  function listenToSystemTheme() {
    if (mediaQuery) {
      return;
    }
    mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    mediaQuery.addEventListener("change", handleSystemThemeChange);
  }

  const modeLabel = computed(() => {
    return getThemeModeLabel(mode.value)
  });

  function setClickEffectEnabled(value: boolean | string | number) {
    clickEffectEnabled.value = Boolean(value);
    localStorage.setItem("clickEffectEnabled", String(Boolean(value)));
  }

  function initHue() {
    const saved = localStorage.getItem("hue");
    hue.value = parseStoredHue(saved, DEFAULT_HUE);
    applyHue(hue.value);
  }

  function setHue(value: number) {
    const nextHue = applyHue(value);
    hue.value = nextHue;
    localStorage.setItem("hue", String(nextHue));
  }

  return {
    mode,
    isDark,
    clickEffectEnabled,
    hue,
    defaultHue: DEFAULT_HUE,
    modeLabel,
    initTheme,
    toggleTheme,
    setMode,
    applyTheme,
    listenToSystemTheme,
    setClickEffectEnabled,
    initHue,
    setHue,
  };
});
