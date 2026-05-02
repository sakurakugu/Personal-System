import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  applyThemeHueToRoot,
  createRgbCssFromOklch,
  normalizeHue,
  parseStoredHue,
  type OklchColorToken,
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
  const isDark = ref(false);
  const followSystem = ref(false);
  const clickEffectEnabled = ref(true);
  const hue = ref(DEFAULT_HUE);
  let mediaQuery: MediaQueryList | null = null;

  function initTheme() {
    const saved = localStorage.getItem("theme");
    if (saved === "dark") {
      isDark.value = true;
      followSystem.value = false;
    } else if (saved === "light") {
      isDark.value = false;
      followSystem.value = false;
    } else if (saved === "system") {
      // 跟随系统
      followSystem.value = true;
      isDark.value = window.matchMedia("(prefers-color-scheme: dark)").matches;
    } else {
      // 默认跟随系统
      followSystem.value = true;
      isDark.value = window.matchMedia("(prefers-color-scheme: dark)").matches;
      localStorage.setItem("theme", "system");
    }
    applyTheme();

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

  // 切换主题（仅在非跟随系统模式下有效）
  function toggleTheme() {
    if (followSystem.value) {
      // 如果正在跟随系统，切换为手动模式并设置相反的主题
      followSystem.value = false;
      isDark.value = !isDark.value;
      localStorage.setItem("theme", isDark.value ? "dark" : "light");
    } else {
      isDark.value = !isDark.value;
      localStorage.setItem("theme", isDark.value ? "dark" : "light");
    }
    applyTheme();
  }

  function setFollowSystem(value: boolean | string | number) {
    const boolValue = Boolean(value);
    followSystem.value = boolValue;
    if (boolValue) {
      localStorage.setItem("theme", "system");
      isDark.value = window.matchMedia("(prefers-color-scheme: dark)").matches;
    } else {
      localStorage.setItem("theme", isDark.value ? "dark" : "light");
    }
    applyTheme();
  }

  function handleSystemThemeChange(event: MediaQueryListEvent) {
    if (!followSystem.value) {
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
    if (followSystem.value) return "跟随系统";
    return isDark.value ? "深色模式" : "浅色模式";
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
    isDark,
    followSystem,
    clickEffectEnabled,
    hue,
    defaultHue: DEFAULT_HUE,
    modeLabel,
    initTheme,
    toggleTheme,
    setFollowSystem,
    applyTheme,
    listenToSystemTheme,
    setClickEffectEnabled,
    initHue,
    setHue,
  };
});
