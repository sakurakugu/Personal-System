import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  DEFAULT_THEME_HUE,
  DEFAULT_THEME_PRIMARY_RGB_TOKEN,
  应用主题色相到根元素,
  从Oklch创建RGB_CSS,
  获取主题模式标签,
  获取切换后的主题模式,
  标准化色相,
  解析存储的色相,
  解析存储的主题模式,
  从模式解析是否为暗色,
  解析系统暗色,
  type ThemeMode,
} from '@personal-system/theme'

const DEFAULT_HUE = DEFAULT_THEME_HUE
const DEFAULT_CLICK_EFFECT_ENABLED = false

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

export function 获取主题点击效果颜色(hueValue: number, isDark: boolean) {
  const selectionHue = 标准化色相(hueValue)
  const colorStops = isDark
    ? CLICK_EFFECT_COLOR_STOPS.dark
    : CLICK_EFFECT_COLOR_STOPS.light
  return colorStops.map(([lightness, chroma]) =>
    从Oklch创建RGB_CSS({ lightness, chroma }, selectionHue),
  )
}

function 应用色相(hueValue: number) {
  return 应用主题色相到根元素({
    hueValue,
    primaryRgbToken: DEFAULT_THEME_PRIMARY_RGB_TOKEN,
  })
}

export const 使用主题存储 = defineStore("theme", () => {
  const mode = ref<ThemeMode>('system')
  const isDark = ref(false);
  const clickEffectEnabled = ref(DEFAULT_CLICK_EFFECT_ENABLED);
  const hue = ref(DEFAULT_HUE);
  let mediaQuery: MediaQueryList | null = null;

  function 初始化主题() {
    mode.value = 解析存储的主题模式(localStorage.getItem('theme'))
    localStorage.setItem('theme', mode.value)
    同步主题模式()

    const savedClickEffect = localStorage.getItem("clickEffectEnabled");
    clickEffectEnabled.value = savedClickEffect === null
      ? DEFAULT_CLICK_EFFECT_ENABLED
      : savedClickEffect === "true";
  }

  function 应用主题() {
    if (isDark.value) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }

  function 同步主题模式() {
    isDark.value = 从模式解析是否为暗色(mode.value, 解析系统暗色())
    应用主题()
  }

  function 切换主题() {
    设置模式(获取切换后的主题模式(mode.value, isDark.value))
  }

  function 设置模式(nextMode: ThemeMode) {
    mode.value = nextMode
    localStorage.setItem('theme', nextMode)
    同步主题模式()
  }

  function 处理系统主题变更(event: MediaQueryListEvent) {
    if (mode.value !== 'system') {
      return;
    }
    isDark.value = event.matches;
    应用主题();
  }

  function 监听系统主题() {
    if (mediaQuery) {
      return;
    }
    mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    mediaQuery.addEventListener("change", 处理系统主题变更);
  }

  const modeLabel = computed(() => {
    return 获取主题模式标签(mode.value)
  });

  function 设置点击效果启用(value: boolean | string | number) {
    clickEffectEnabled.value = Boolean(value);
    localStorage.setItem("clickEffectEnabled", String(Boolean(value)));
  }

  function 初始化色相() {
    const saved = localStorage.getItem("hue");
    hue.value = 解析存储的色相(saved, DEFAULT_HUE);
    应用色相(hue.value);
  }

  function 设置色相(value: number) {
    const nextHue = 应用色相(value);
    hue.value = nextHue;
    localStorage.setItem("hue", String(nextHue));
  }

  return {
    mode,
    isDark,
    clickEffectEnabled,
    hue,
    defaultClickEffectEnabled: DEFAULT_CLICK_EFFECT_ENABLED,
    defaultHue: DEFAULT_HUE,
    modeLabel,
    initTheme: 初始化主题,
    toggleTheme: 切换主题,
    setMode: 设置模式,
    applyTheme: 应用主题,
    listenToSystemTheme: 监听系统主题,
    setClickEffectEnabled: 设置点击效果启用,
    initHue: 初始化色相,
    setHue: 设置色相,
  };
});
