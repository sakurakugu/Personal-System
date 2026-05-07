import hljs from 'highlight.js/lib/core'
import bash from 'highlight.js/lib/languages/bash'
import c from 'highlight.js/lib/languages/c'
import cpp from 'highlight.js/lib/languages/cpp'
import csharp from 'highlight.js/lib/languages/csharp'
import css from 'highlight.js/lib/languages/css'
import dart from 'highlight.js/lib/languages/dart'
import diff from 'highlight.js/lib/languages/diff'
import dockerfile from 'highlight.js/lib/languages/dockerfile'
import go from 'highlight.js/lib/languages/go'
import graphql from 'highlight.js/lib/languages/graphql'
import javascript from 'highlight.js/lib/languages/javascript'
import java from 'highlight.js/lib/languages/java'
import ini from 'highlight.js/lib/languages/ini'
import json from 'highlight.js/lib/languages/json'
import kotlin from 'highlight.js/lib/languages/kotlin'
import less from 'highlight.js/lib/languages/less'
import lua from 'highlight.js/lib/languages/lua'
import makefile from 'highlight.js/lib/languages/makefile'
import markdown from 'highlight.js/lib/languages/markdown'
import nginx from 'highlight.js/lib/languages/nginx'
import plaintext from 'highlight.js/lib/languages/plaintext'
import powershell from 'highlight.js/lib/languages/powershell'
import python from 'highlight.js/lib/languages/python'
import ruby from 'highlight.js/lib/languages/ruby'
import rust from 'highlight.js/lib/languages/rust'
import scss from 'highlight.js/lib/languages/scss'
import sql from 'highlight.js/lib/languages/sql'
import typescript from 'highlight.js/lib/languages/typescript'
import xml from 'highlight.js/lib/languages/xml'
import yaml from 'highlight.js/lib/languages/yaml'

const 已注册语言 = {
  bash,
  c,
  cpp,
  csharp,
  css,
  dart,
  diff,
  dockerfile,
  go,
  graphql,
  ini,
  java,
  javascript,
  json,
  kotlin,
  less,
  lua,
  makefile,
  markdown,
  nginx,
  plaintext,
  powershell,
  python,
  ruby,
  rust,
  scss,
  sql,
  typescript,
  xml,
  yaml,
}

for (const [语言名, 语言定义] of Object.entries(已注册语言)) {
  hljs.registerLanguage(语言名, 语言定义)
}

const 语言别名: Record<string, string> = {
  bat: 'powershell',
  'c#': 'csharp',
  'c++': 'cpp',
  conf: 'nginx',
  console: 'bash',
  cs: 'csharp',
  docker: 'dockerfile',
  env: 'ini',
  gql: 'graphql',
  htm: 'xml',
  html: 'xml',
  js: 'javascript',
  jsonc: 'json',
  jsx: 'javascript',
  kt: 'kotlin',
  kts: 'kotlin',
  mdx: 'markdown',
  md: 'markdown',
  pyi: 'python',
  plain: 'plaintext',
  powershell: 'powershell',
  ps1: 'powershell',
  py: 'python',
  rb: 'ruby',
  rs: 'rust',
  scss: 'scss',
  shell: 'bash',
  shellscript: 'bash',
  sh: 'bash',
  sql: 'sql',
  styl: 'css',
  text: 'plaintext',
  ts: 'typescript',
  tsx: 'typescript',
  txt: 'plaintext',
  vue: 'xml',
  yml: 'yaml',
  zsh: 'bash',
}

export function 渲染Markdown代码高亮(source: string, language: string) {
  const 标准语言 = 获取高亮语言(language)

  try {
    return hljs.highlight(source, { language: 标准语言 }).value
  } catch {
    return hljs.highlight(source, { language: 'plaintext' }).value
  }
}

function 获取高亮语言(language: string): string {
  const 规范化语言 = language.trim().toLowerCase()
  const 标准语言 = 语言别名[规范化语言] || 规范化语言

  if (hljs.getLanguage(标准语言)) {
    return 标准语言
  }

  const 去前缀语言 = 标准语言.replace(/^language-/, '')
  if (hljs.getLanguage(去前缀语言)) {
    return 去前缀语言
  }

  return 'plaintext'
}
