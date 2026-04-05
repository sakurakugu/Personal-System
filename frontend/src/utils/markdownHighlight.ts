import hljs from 'highlight.js/lib/core'
import bash from 'highlight.js/lib/languages/bash'
import css from 'highlight.js/lib/languages/css'
import diff from 'highlight.js/lib/languages/diff'
import javascript from 'highlight.js/lib/languages/javascript'
import json from 'highlight.js/lib/languages/json'
import markdown from 'highlight.js/lib/languages/markdown'
import plaintext from 'highlight.js/lib/languages/plaintext'
import python from 'highlight.js/lib/languages/python'
import sql from 'highlight.js/lib/languages/sql'
import typescript from 'highlight.js/lib/languages/typescript'
import xml from 'highlight.js/lib/languages/xml'
import yaml from 'highlight.js/lib/languages/yaml'

hljs.registerLanguage('bash', bash)
hljs.registerLanguage('css', css)
hljs.registerLanguage('diff', diff)
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('json', json)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('plaintext', plaintext)
hljs.registerLanguage('python', python)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('yaml', yaml)

const 语言别名: Record<string, string> = {
  html: 'xml',
  js: 'javascript',
  md: 'markdown',
  plain: 'plaintext',
  py: 'python',
  shell: 'bash',
  sh: 'bash',
  text: 'plaintext',
  ts: 'typescript',
  txt: 'plaintext',
  vue: 'xml',
  yml: 'yaml',
  zsh: 'bash',
}

export function 渲染Markdown代码高亮(source: string, language: string) {
  const 标准语言 = 语言别名[language.toLowerCase()] || language.toLowerCase()
  if (!hljs.getLanguage(标准语言)) {
    return ''
  }

  try {
    return hljs.highlight(source, { language: 标准语言 }).value
  } catch {
    return ''
  }
}
