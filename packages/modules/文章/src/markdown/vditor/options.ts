import { parseVditor文章预览, preprocessVditor文章Markdown, transformVditor文章预览Html } from './preview'
import { 创建Vditor文章工具栏, type 创建Vditor工具栏选项 } from './toolbar'
import { type VditorMarkdownImageUploader } from './upload'

export interface 创建Vditor文章编辑器选项 {
  value: string
  placeholder: string
  theme: 'light' | 'dark'
  uploadImages?: VditorMarkdownImageUploader
  toolbar: 创建Vditor工具栏选项
  onReady: () => void
  onInput: (value: string) => void
  onKeydown: (event: KeyboardEvent) => void
  onUploadError: (error: unknown) => void
}

export function 创建Vditor文章编辑器选项(options: 创建Vditor文章编辑器选项): IOptions {
  return {
    value: options.value,
    placeholder: options.placeholder,
    height: '100%',
    minHeight: 360,
    mode: 'ir',
    lang: 'zh_CN',
    theme: options.theme === 'dark' ? 'dark' : 'classic',
    icon: 'ant',
    tab: '  ',
    cache: {
      enable: false,
    },
    toolbar: 创建Vditor文章工具栏(options.toolbar),
    toolbarConfig: {
      pin: false,
    },
    resize: {
      enable: false,
    },
    counter: {
      enable: false,
      type: 'markdown',
    },
    preview: {
      delay: 180,
      mode: 'editor',
      maxWidth: 1200,
      markdown: {
        autoSpace: true,
        paragraphBeginningSpace: true,
        mark: true,
        footnotes: true,
        gfmAutoLink: true,
        toc: true,
        codeBlockPreview: true,
        mathBlockPreview: true,
        sanitize: false,
        sup: true,
        sub: true,
      },
      math: {
        engine: 'KaTeX',
        inlineDigit: true,
      },
      hljs: {
        enable: true,
        lineNumber: false,
        style: options.theme === 'dark' ? 'dracula' : 'github',
      },
      transform: (html) => transformVditor文章预览Html(html),
      parse: parseVditor文章预览,
    },
    hint: {
      emoji: {
        smile: '😄',
        laugh: '😆',
        thumbsup: '👍',
        heart: '❤️',
      },
    },
    input: options.onInput,
    keydown: options.onKeydown,
    after: options.onReady,
    customRenders: [
      {
        language: 'article-preview',
        render: (element) => {
          element.innerHTML = preprocessVditor文章Markdown(element.textContent ?? '')
        },
      },
    ],
  }
}
