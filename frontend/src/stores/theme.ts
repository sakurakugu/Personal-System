import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { converter, formatCss } from "culori";

const DEFAULT_HUE = 0;
const toRgb = converter("rgb");

const THEME_COLOR_STOPS = [
  // ['--el-color-primary', 0.62, 0.14],
  // ['--el-color-primary-light-3', 0.7, 0.13],
  // ['--el-color-primary-light-5', 0.78, 0.1],
  // ['--el-color-primary-light-7', 0.84, 0.08],
  // ['--el-color-primary-light-8', 0.88, 0.06],
  // ['--el-color-primary-light-9', 0.94, 0.03],
  // ['--el-color-primary-dark-2', 0.54, 0.14],
  // ['--el-color-primary-dark-8', 0.34, 0.1],
  // 下面的更浅一点
  ["--el-color-primary", 0.7, 0.14],
  ["--el-color-primary-light-3", 0.78, 0.13],
  ["--el-color-primary-light-5", 0.84, 0.1],
  ["--el-color-primary-light-7", 0.88, 0.08],
  ["--el-color-primary-light-8", 0.94, 0.06],
  ["--el-color-primary-light-9", 0.98, 0.03],
  ["--el-color-primary-dark-2", 0.54, 0.14],
  ["--el-color-primary-dark-8", 0.34, 0.1],
] as const;

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
} as const;

function normalizeHue(value: number) {
  return ((value % 360) + 360) % 360;
}

function createOklchCss(lightness: number, chroma: number, hue: number) {
  return formatCss({ mode: "oklch", l: lightness, c: chroma, h: hue });
}

function createRgbCss(lightness: number, chroma: number, hue: number) {
  const color = toRgb({ mode: "oklch", l: lightness, c: chroma, h: hue });
  if (!color) {
    return "rgb(24, 160, 88)";
  }

  return `rgb(${Math.round(color.r * 255)}, ${Math.round(color.g * 255)}, ${Math.round(color.b * 255)})`;
}

export function getThemeClickEffectColors(hueValue: number, isDark: boolean) {
  const selectionHue = normalizeHue(hueValue);
  const colorStops = isDark
    ? CLICK_EFFECT_COLOR_STOPS.dark
    : CLICK_EFFECT_COLOR_STOPS.light;
  return colorStops.map(([lightness, chroma]) =>
    createRgbCss(lightness, chroma, selectionHue),
  );
}

function applyHue(hueValue: number) {
  const r = document.querySelector(":root") as HTMLElement | null;
  if (!r) return;
  const selectionHue = normalizeHue(hueValue);
  r.style.setProperty("--selection-hue", String(selectionHue));
  r.style.setProperty("--hue", String(selectionHue));

  THEME_COLOR_STOPS.forEach(([token, lightness, chroma]) => {
    r.style.setProperty(token, createOklchCss(lightness, chroma, selectionHue));
  });

  const primaryRgb = toRgb({
    mode: "oklch",
    l: 0.62,
    c: 0.14,
    h: selectionHue,
  });
  if (primaryRgb) {
    const rgbValue = [
      Math.round(primaryRgb.r * 255),
      Math.round(primaryRgb.g * 255),
      Math.round(primaryRgb.b * 255),
    ].join(", ");
    r.style.setProperty("--el-color-primary-rgb", rgbValue);
  }
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
    const parsed = saved ? Number.parseInt(saved, 10) : NaN;
    hue.value = Number.isNaN(parsed) ? DEFAULT_HUE : parsed;
    applyHue(hue.value);
  }

  function setHue(value: number) {
    hue.value = value;
    localStorage.setItem("hue", String(value));
    applyHue(value);
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
