import { computed, ref } from 'vue'
import fullEmojiMap from 'markdown-it-emoji/lib/data/full.mjs'
import emojiShortcutsMap from 'markdown-it-emoji/lib/data/shortcuts.mjs'

const 常用Emoji存储键 = 'personal-system:article:markdown-editor:common-emojis'
const 常用颜文字存储键 = 'personal-system:article:markdown-editor:common-kaomoji'
const 常用Emoji最大数量 = 16
const 常用颜文字最大数量 = 8
const 默认常用Emoji短码 = [
  'smile',
  'joy',
  'rofl',
  'wink',
  'thinking',
  'neutral_face',
  'sob',
  'heart',
  'thumbsup',
  'clap',
  'fire',
  'tada',
  'rocket',
  'warning',
  'x',
  'white_check_mark',
]
const 默认常用颜文字 = [
  ':)',
  ':D',
  ';)',
  ':P',
  ':(',
  ":'(",
  '<3',
  '>:(',
]
const 颜文字选项 = Object.entries(emojiShortcutsMap)
  .flatMap(([shortcode, shortcuts]) => shortcuts.map((shortcut) => ({
    shortcode,
    shortcut,
    emoji: fullEmojiMap[shortcode] ?? '',
  })))
const 颜文字快捷值集合 = new Set(颜文字选项.map((option) => option.shortcut))

export function 使用Markdown常用表情() {
  const 常用Emoji短码 = ref<string[]>([])
  const 常用颜文字 = ref<string[]>([])
  const 常用Emoji选项 = computed(() => 常用Emoji短码.value
    .map((shortcode) => {
      const emoji = fullEmojiMap[shortcode]
      return emoji ? { shortcode, emoji } : null
    })
    .filter((item): item is { shortcode: string; emoji: string } => Boolean(item)))
  const 常用颜文字选项 = computed(() => 常用颜文字.value
    .map((shortcut) => 颜文字选项.find((option) => option.shortcut === shortcut))
    .filter((item): item is { shortcode: string; shortcut: string; emoji: string } => Boolean(item)))

  function 初始化常用表情记录() {
    常用Emoji短码.value = 合并默认常用项(
      读取本地字符串列表(常用Emoji存储键, 默认常用Emoji短码),
      默认常用Emoji短码,
    )
      .filter((shortcode) => Boolean(fullEmojiMap[shortcode]))
      .slice(0, 常用Emoji最大数量)
    常用颜文字.value = 合并默认常用项(
      读取本地字符串列表(常用颜文字存储键, 默认常用颜文字),
      默认常用颜文字,
    )
      .filter((shortcut) => 颜文字快捷值集合.has(shortcut))
      .slice(0, 常用颜文字最大数量)
  }

  function 记录常用Emoji(shortcode: string) {
    if (!fullEmojiMap[shortcode]) {
      return
    }

    常用Emoji短码.value = 更新最近使用项(shortcode, 常用Emoji短码.value, 常用Emoji最大数量)
    写入本地字符串列表(常用Emoji存储键, 常用Emoji短码.value)
  }

  function 记录常用颜文字(value: string) {
    if (!颜文字快捷值集合.has(value)) {
      return
    }

    常用颜文字.value = 更新最近使用项(value, 常用颜文字.value, 常用颜文字最大数量)
    写入本地字符串列表(常用颜文字存储键, 常用颜文字.value)
  }

  return {
    常用Emoji选项,
    常用颜文字选项,
    初始化常用表情记录,
    记录常用Emoji,
    记录常用颜文字,
  }
}

function 读取本地字符串列表(storageKey: string, fallback: string[]): string[] {
  if (typeof window === 'undefined') {
    return [...fallback]
  }

  try {
    const rawValue = window.localStorage.getItem(storageKey)
    const value = rawValue ? JSON.parse(rawValue) : fallback
    if (!Array.isArray(value)) {
      return [...fallback]
    }

    const result = value.filter((item): item is string => typeof item === 'string')
    return result.length > 0 ? result : [...fallback]
  } catch (error) {
    console.warn('读取 Markdown 编辑器常用表情失败', error)
    return [...fallback]
  }
}

function 写入本地字符串列表(storageKey: string, value: string[]) {
  if (typeof window === 'undefined') {
    return
  }

  try {
    window.localStorage.setItem(storageKey, JSON.stringify(value))
  } catch (error) {
    console.warn('保存 Markdown 编辑器常用表情失败', error)
  }
}

function 合并默认常用项(value: string[], fallback: string[]): string[] {
  return [...value, ...fallback.filter((item) => !value.includes(item))]
}

function 更新最近使用项(value: string, currentValues: string[], maxLength: number): string[] {
  return [value, ...currentValues.filter((item) => item !== value)].slice(0, maxLength)
}
