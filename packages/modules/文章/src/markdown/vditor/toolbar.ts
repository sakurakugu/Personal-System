export type Vditor文章工具栏动作 =
  | 'subscript'
  | 'superscript'
  | 'insert-table'
  | 'image-link'
  | 'image-crop-upload'
  | 'insert-mermaid'
  | 'insert-math'
  | 'format'
  | 'scroll-sync'
  | 'page-fullscreen'

export interface Vditor表格尺寸 {
  row: number
  col: number
}

export interface 创建Vditor工具栏选项 {
  showScrollSync: boolean
  scrollSync: boolean
  canUpload: boolean
  onImageUpload: () => void
  onImageLink: () => void
  onImageCropUpload: () => void
  onInsertMermaid: (type: string) => void
  onInsertMath: (type: 'inline' | 'block') => void
  onUnderline: () => void
  onSubscript: () => void
  onSuperscript: () => void
  onInsertTable: (size: Vditor表格尺寸) => void
  onFormat?: () => void | Promise<unknown>
  onToggleScrollSync: () => void
  onTogglePageFullscreen: () => void
}

type Vditor工具栏项 =
  | string
  | {
      name: string
      icon?: string
      className?: string
      tip?: string
      tipPosition?: string
      toolbar?: Vditor工具栏项[]
      click?: (event: Event, vditor: IVditor) => void
    }

function 创建Lucide图标(content: string): string {
  return `<svg class="article-vditor-lucide-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${content}</svg>`
}

function 创建文本图标(text: string): string {
  return `<span class="article-vditor-text-icon" aria-hidden="true">${text}</span>`
}

const lucide图标 = {
  emoji: 创建Lucide图标(
    '<circle cx="12" cy="12" r="10"></circle><path d="M8 14s1.5 2 4 2 4-2 4-2"></path><line x1="9" x2="9.01" y1="9" y2="9"></line><line x1="15" x2="15.01" y1="9" y2="9"></line>',
  ),
  headings: 创建Lucide图标(
    '<path d="M6 12h12"></path><path d="M6 20V4"></path><path d="M18 20V4"></path>',
  ),
  bold: 创建Lucide图标(
    '<path d="M6 12h9a4 4 0 0 1 0 8H7a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h7a4 4 0 0 1 0 8"></path>',
  ),
  underline: 创建Lucide图标(
    '<path d="M6 4v6a6 6 0 0 0 12 0V4"></path><line x1="4" x2="20" y1="20" y2="20"></line>',
  ),
  subscript: 创建文本图标('X₂'),
  superscript: 创建文本图标('X²'),
  italic: 创建Lucide图标(
    '<line x1="19" x2="10" y1="4" y2="4"></line><line x1="14" x2="5" y1="20" y2="20"></line><line x1="15" x2="9" y1="4" y2="20"></line>',
  ),
  strike: 创建Lucide图标(
    '<path d="M16 4H9a3 3 0 0 0-2.83 4"></path><path d="M14 12a4 4 0 0 1 0 8H6"></path><line x1="4" x2="20" y1="12" y2="12"></line>',
  ),
  link: 创建Lucide图标(
    '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>',
  ),
  list: 创建Lucide图标(
    '<path d="M3 5h.01"></path><path d="M3 12h.01"></path><path d="M3 19h.01"></path><path d="M8 5h13"></path><path d="M8 12h13"></path><path d="M8 19h13"></path>',
  ),
  orderedList: 创建Lucide图标(
    '<path d="M11 5h10"></path><path d="M11 12h10"></path><path d="M11 19h10"></path><path d="M4 4h1v5"></path><path d="M4 9h2"></path><path d="M6.5 20H3.4c0-1 2.6-1.925 2.6-3.5a1.5 1.5 0 0 0-2.6-1.02"></path>',
  ),
  check: 创建Lucide图标(
    '<path d="M13 5h8"></path><path d="M13 12h8"></path><path d="M13 19h8"></path><path d="m3 17 2 2 4-4"></path><rect x="3" y="4" width="6" height="6" rx="1"></rect>',
  ),
  outdent: 创建Lucide图标(
    '<path d="M21 5H11"></path><path d="M21 12H11"></path><path d="M21 19H11"></path><path d="m7 8-4 4 4 4"></path>',
  ),
  indent: 创建Lucide图标(
    '<path d="M21 5H11"></path><path d="M21 12H11"></path><path d="M21 19H11"></path><path d="m3 8 4 4-4 4"></path>',
  ),
  quote: 创建Lucide图标(
    '<path d="M16 3a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2 1 1 0 0 1 1 1v1a2 2 0 0 1-2 2 1 1 0 0 0-1 1v2a1 1 0 0 0 1 1 6 6 0 0 0 6-6V5a2 2 0 0 0-2-2z"></path><path d="M5 3a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2 1 1 0 0 1 1 1v1a2 2 0 0 1-2 2 1 1 0 0 0-1 1v2a1 1 0 0 0 1 1 6 6 0 0 0 6-6V5a2 2 0 0 0-2-2z"></path>',
  ),
  line: 创建Lucide图标('<path d="M5 12h14"></path>'),
  code: 创建Lucide图标(
    '<path d="m10 9-3 3 3 3"></path><path d="m14 15 3-3-3-3"></path><rect x="3" y="3" width="18" height="18" rx="2"></rect>',
  ),
  inlineCode: 创建Lucide图标('<path d="m16 18 6-6-6-6"></path><path d="m8 6-6 6 6 6"></path>'),
  insertBefore: 创建Lucide图标('<path d="m11 17-5-5 5-5"></path><path d="m18 17-5-5 5-5"></path>'),
  insertAfter: 创建Lucide图标('<path d="m6 17 5-5-5-5"></path><path d="m13 17 5-5-5-5"></path>'),
  table: 创建Lucide图标(
    '<path d="M12 3v18"></path><rect width="18" height="18" x="3" y="3" rx="2"></rect><path d="M3 9h18"></path><path d="M3 15h18"></path>',
  ),
  undo: 创建Lucide图标(
    '<path d="M9 14 4 9l5-5"></path><path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11"></path>',
  ),
  redo: 创建Lucide图标(
    '<path d="m15 14 5-5-5-5"></path><path d="M20 9H9.5A5.5 5.5 0 0 0 4 14.5A5.5 5.5 0 0 0 9.5 20H13"></path>',
  ),
  image: 创建Lucide图标(
    '<rect width="18" height="18" x="3" y="3" rx="2" ry="2"></rect><circle cx="9" cy="9" r="2"></circle><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"></path>',
  ),
  upload: 创建Lucide图标(
    '<path d="M12 3v12"></path><path d="m17 8-5-5-5 5"></path><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>',
  ),
  crop: 创建Lucide图标(
    '<path d="M6 2v14a2 2 0 0 0 2 2h14"></path><path d="M18 22V8a2 2 0 0 0-2-2H2"></path>',
  ),
  chart: 创建Lucide图标(
    '<path d="M3 3v16a2 2 0 0 0 2 2h16"></path><path d="M7 11.207a.5.5 0 0 1 .146-.353l2-2a.5.5 0 0 1 .708 0l3.292 3.292a.5.5 0 0 0 .708 0l4.292-4.292a.5.5 0 0 1 .854.353V16a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1z"></path>',
  ),
  math: 创建Lucide图标(
    '<rect width="18" height="18" x="3" y="3" rx="2"></rect><path d="M16 8.9V7H8l4 5-4 5h8v-1.9"></path>',
  ),
  format: 创建Lucide图标(
    '<path d="m10 9-3 3 3 3"></path><path d="m14 15 3-3-3-3"></path><rect x="3" y="3" width="18" height="18" rx="2"></rect>',
  ),
  scrollSync: 创建Lucide图标(
    '<path d="m3 16 4 4 4-4"></path><path d="M7 20V4"></path><path d="m21 8-4-4-4 4"></path><path d="M17 4v16"></path>',
  ),
  editMode: 创建Lucide图标(
    '<path d="m18 5-2.414-2.414A2 2 0 0 0 14.172 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2"></path><path d="M21.378 12.626a1 1 0 0 0-3.004-3.004l-4.01 4.012a2 2 0 0 0-.506.854l-.837 2.87a.5.5 0 0 0 .62.62l2.87-.837a2 2 0 0 0 .854-.506z"></path><path d="M8 18h1"></path>',
  ),
  both: 创建Lucide图标(
    '<rect width="18" height="18" x="3" y="3" rx="2"></rect><path d="M12 3v18"></path>',
  ),
  preview: 创建Lucide图标(
    '<path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"></path><circle cx="12" cy="12" r="3"></circle>',
  ),
  outline: 创建Lucide图标(
    '<path d="M8 5h13"></path><path d="M13 12h8"></path><path d="M13 19h8"></path><path d="M3 10a2 2 0 0 0 2 2h3"></path><path d="M3 5v12a2 2 0 0 0 2 2h3"></path>',
  ),
  pageFullscreen: 创建Lucide图标(
    '<path d="M15 3h6v6"></path><path d="m21 3-7 7"></path><path d="m3 21 7-7"></path><path d="M9 21H3v-6"></path>',
  ),
  fullscreen: 创建Lucide图标(
    '<path d="m15 15 6 6"></path><path d="m15 9 6-6"></path><path d="M21 16v5h-5"></path><path d="M21 8V3h-5"></path><path d="M3 16v5h5"></path><path d="m3 21 6-6"></path><path d="M3 8V3h5"></path><path d="M9 9 3 3"></path>',
  ),
}

function 创建图片菜单项图标(icon: string, label: string): string {
  return `<span class="article-vditor-image-menu-item">${icon}<span>${label}</span></span>`
}

function 创建表格选择器内容() {
  const cells = Array.from({ length: 6 }, (_rowItem, rowIndex) =>
    Array.from({ length: 6 }, (_colItem, colIndex) => {
      const row = rowIndex + 1
      const col = colIndex + 1
      const activeClass = row <= 3 && col <= 3 ? ' is-active' : ''
      return `<span class="article-vditor-table-picker__cell${activeClass}" data-row="${row}" data-col="${col}" aria-hidden="true"></span>`
    }).join(''),
  ).join('')

  return `
    <span class="article-vditor-table-picker__content">
      <span class="article-vditor-table-picker__label" data-role="table-label">3 x 3</span>
      <span class="article-vditor-table-picker__grid">${cells}</span>
    </span>
  `.trim()
}

function 解析表格尺寸(event: Event): Vditor表格尺寸 | null {
  const target = event.target
  if (!(target instanceof HTMLElement)) {
    return null
  }

  const cell = target.closest<HTMLElement>('[data-row][data-col]')
  if (!cell) {
    return null
  }

  const row = Number(cell.dataset.row)
  const col = Number(cell.dataset.col)
  if (!Number.isInteger(row) || !Number.isInteger(col)) {
    return null
  }

  return {
    row: Math.min(6, Math.max(1, row)),
    col: Math.min(6, Math.max(1, col)),
  }
}

function 创建默认工具栏项(name: string, icon: string): Vditor工具栏项 {
  return { name, icon }
}

function 创建自定义工具栏项(
  name: string,
  icon: string,
  tip: string,
  tipPosition: string = 'n',
): Extract<Vditor工具栏项, { name: string }> {
  return {
    name,
    icon,
    tip,
    tipPosition,
  }
}

export function 创建Vditor文章工具栏(options: 创建Vditor工具栏选项): Vditor工具栏项[] {
  const imageToolbar: Vditor工具栏项 = {
    name: 'article-image-more',
    tip: '图片',
    icon: lucide图标.image,
    tipPosition: 'n',
    toolbar: [
      {
        name: 'article-image-upload',
        tip: '上传图片',
        icon: 创建图片菜单项图标(lucide图标.upload, '上传图片'),
        click: options.onImageUpload,
      },
      {
        name: 'article-image-link',
        tip: '添加图片链接',
        icon: 创建图片菜单项图标(lucide图标.link, '添加图片链接'),
        click: options.onImageLink,
      },
      {
        name: 'article-image-crop-upload',
        tip: '裁剪上传',
        icon: 创建图片菜单项图标(lucide图标.crop, '裁剪上传'),
        click: options.onImageCropUpload,
      },
    ],
  }

  const toolbar: Vditor工具栏项[] = [
    创建默认工具栏项('bold', lucide图标.bold),
    {
      ...创建自定义工具栏项('article-underline', lucide图标.underline, '下划线'),
      click: () => {
        options.onUnderline()
      },
    },
    创建默认工具栏项('italic', lucide图标.italic),
    创建默认工具栏项('strike', lucide图标.strike),
    创建默认工具栏项('link', lucide图标.link),
    '|',
    创建默认工具栏项('headings', lucide图标.headings),
    {
      ...创建自定义工具栏项('article-subscript', lucide图标.subscript, '下标'),
      click: () => {
        options.onSubscript()
      },
    },
    {
      ...创建自定义工具栏项('article-superscript', lucide图标.superscript, '上标'),
      click: () => {
        options.onSuperscript()
      },
    },
    创建默认工具栏项('list', lucide图标.list),
    创建默认工具栏项('ordered-list', lucide图标.orderedList),
    创建默认工具栏项('check', lucide图标.check),
    创建默认工具栏项('outdent', lucide图标.outdent),
    创建默认工具栏项('indent', lucide图标.indent),
    '|',
    创建默认工具栏项('emoji', lucide图标.emoji),
    创建默认工具栏项('quote', lucide图标.quote),
    创建默认工具栏项('line', lucide图标.line),
    创建默认工具栏项('code', lucide图标.code),
    创建默认工具栏项('inline-code', lucide图标.inlineCode),
    创建默认工具栏项('insert-before', lucide图标.insertBefore),
    创建默认工具栏项('insert-after', lucide图标.insertAfter),
    {
      ...创建自定义工具栏项('article-mermaid', lucide图标.chart, '各种图'),
      toolbar: [
        {
          name: 'article-mermaid-flow',
          tip: '流程图',
          icon: 创建图片菜单项图标(lucide图标.chart, '流程图'),
          click: () => {
            options.onInsertMermaid('flow')
          },
        },
        {
          name: 'article-mermaid-sequence',
          tip: '时序图',
          icon: 创建图片菜单项图标(lucide图标.chart, '时序图'),
          click: () => {
            options.onInsertMermaid('sequence')
          },
        },
        {
          name: 'article-mermaid-gantt',
          tip: '甘特图',
          icon: 创建图片菜单项图标(lucide图标.chart, '甘特图'),
          click: () => {
            options.onInsertMermaid('gantt')
          },
        },
        {
          name: 'article-mermaid-class',
          tip: '类图',
          icon: 创建图片菜单项图标(lucide图标.chart, '类图'),
          click: () => {
            options.onInsertMermaid('class')
          },
        },
        {
          name: 'article-mermaid-state',
          tip: '状态图',
          icon: 创建图片菜单项图标(lucide图标.chart, '状态图'),
          click: () => {
            options.onInsertMermaid('state')
          },
        },
        {
          name: 'article-mermaid-pie',
          tip: '饼图',
          icon: 创建图片菜单项图标(lucide图标.chart, '饼图'),
          click: () => {
            options.onInsertMermaid('pie')
          },
        },
        {
          name: 'article-mermaid-relationship',
          tip: '关系图',
          icon: 创建图片菜单项图标(lucide图标.chart, '关系图'),
          click: () => {
            options.onInsertMermaid('relationship')
          },
        },
        {
          name: 'article-mermaid-journey',
          tip: '旅程图',
          icon: 创建图片菜单项图标(lucide图标.chart, '旅程图'),
          click: () => {
            options.onInsertMermaid('journey')
          },
        },
      ],
    },
    {
      ...创建自定义工具栏项('article-math', lucide图标.math, '公式'),
      toolbar: [
        {
          name: 'article-math-inline',
          tip: '行内公式',
          icon: 创建图片菜单项图标(lucide图标.math, '行内公式'),
          click: () => {
            options.onInsertMath('inline')
          },
        },
        {
          name: 'article-math-block',
          tip: '块级公式',
          icon: 创建图片菜单项图标(lucide图标.math, '块级公式'),
          click: () => {
            options.onInsertMath('block')
          },
        },
      ],
    },
    '|',
    {
      ...创建自定义工具栏项('article-table', lucide图标.table, '表格'),
      className: 'article-vditor-table-toolbar',
      toolbar: [
        {
          name: 'article-table-picker',
          className: 'article-vditor-table-picker',
          tip: '选择表格尺寸',
          icon: 创建表格选择器内容(),
          click: (event) => {
            const size = 解析表格尺寸(event)
            if (!size) {
              return
            }
            options.onInsertTable(size)
          },
        },
      ],
    },
    options.canUpload ? imageToolbar : 创建默认工具栏项('upload', lucide图标.upload),
    '|',
    创建默认工具栏项('undo', lucide图标.undo),
    创建默认工具栏项('redo', lucide图标.redo),
    '|',
    创建默认工具栏项('edit-mode', lucide图标.editMode),
    创建默认工具栏项('both', lucide图标.both),
    创建默认工具栏项('preview', lucide图标.preview),
    创建默认工具栏项('outline', lucide图标.outline),
  ]

  if (options.onFormat) {
    toolbar.push({
      ...创建自定义工具栏项('article-format', lucide图标.format, '美化', 'nw'),
      click: () => {
        void options.onFormat?.()
      },
    })
  }

  if (options.showScrollSync) {
    toolbar.push({
      ...创建自定义工具栏项(
        'article-scroll-sync',
        lucide图标.scrollSync,
        options.scrollSync ? '关闭同步滚动' : '开启同步滚动',
        'nw',
      ),
      click: options.onToggleScrollSync,
    })
  }

  toolbar.push(
    {
      ...创建自定义工具栏项('article-page-fullscreen', lucide图标.pageFullscreen, '页面全屏', 'nw'),
      click: options.onTogglePageFullscreen,
    },
    创建默认工具栏项('fullscreen', lucide图标.fullscreen),
  )

  return toolbar
}
