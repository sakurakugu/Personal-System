import {
  ArrowDownUp,
  Blocks,
  Bold,
  ChartArea,
  Code,
  Columns2,
  Expand,
  Eye,
  EyeOff,
  FileCode,
  FilePenLine,
  FileText,
  Forward,
  Github,
  Heading,
  Highlighter,
  Image,
  Italic,
  Link,
  List,
  ListOrdered,
  ListTodo,
  Maximize2,
  Network,
  PanelRightOpen,
  Pilcrow,
  Quote,
  Reply,
  SeparatorHorizontal,
  Smile,
  SquareCode,
  SquareSigma,
  Strikethrough,
  Subscript,
  Superscript,
  Table,
  Underline,
} from 'lucide-vue-next'
import {
  HTML预览图标,
  大纲图标,
  标签页图标,
  美化图标,
  缩写图标,
} from './MilkdownMarkdown工具栏图标'
import type { ToolbarItem } from './MilkdownMarkdown工具栏类型'

interface 创建MilkdownMarkdown工具栏项选项 {
  isUploading: () => boolean
  isSourceMode: () => boolean
  hasFormatContent: () => boolean
  showScrollSync: () => boolean
  scrollSync: () => boolean
  previewEnabled: () => boolean
  previewLayoutMode: () => 'split' | 'full'
  previewType: () => 'preview' | 'html' | 'mindmap'
  showPreviewToggle: () => boolean
  outlineVisible: () => boolean
  showOutlineToggle: () => boolean
}

export function 创建MilkdownMarkdown工具栏项(options: 创建MilkdownMarkdown工具栏项选项): ToolbarItem[] {
  return [
    { label: '加粗', title: '加粗', action: 'strong', icon: Bold },
    { label: '下划线', title: '下划线', action: 'underline', icon: Underline },
    { label: '斜体', title: '斜体', action: 'emphasis', icon: Italic },
    { label: '删除线', title: '删除线', action: 'strikethrough', icon: Strikethrough },
    { label: '高亮文本', title: '高亮文本', action: 'highlight', icon: Highlighter },
    { type: 'separator', label: '', title: '' },
    {
      type: 'dropdown',
      label: '标题',
      title: '标题',
      action: 'heading',
      icon: Heading,
      dropdown: [
        { label: '一级标题', title: '一级标题', action: 'heading', payload: 1 },
        { label: '二级标题', title: '二级标题', action: 'heading', payload: 2 },
        { label: '三级标题', title: '三级标题', action: 'heading', payload: 3 },
        { label: '四级标题', title: '四级标题', action: 'heading', payload: 4 },
        { label: '五级标题', title: '五级标题', action: 'heading', payload: 5 },
        { label: '六级标题', title: '六级标题', action: 'heading', payload: 6 },
      ],
    },
    { label: '下标', title: '下标', action: 'subscript', icon: Subscript },
    { label: '上标', title: '上标', action: 'superscript', icon: Superscript },
    {
      type: 'dropdown',
      label: '引用',
      title: '引用块',
      action: 'blockquote',
      icon: Quote,
      dropdown: [
        { label: '普通引用块', title: '普通引用块', action: 'blockquote' },
        { label: '常用提示块', kind: 'divider' },
        { label: '说明块', title: '插入 GitHub 风格说明提示块', action: 'customMarkdown', payload: 'github-alert-note' },
        { label: '提示块', title: '插入 GitHub 风格提示提示块', action: 'customMarkdown', payload: 'github-alert-tip' },
        { label: '重要块', title: '插入 GitHub 风格重要提示块', action: 'customMarkdown', payload: 'github-alert-important' },
        { label: '警告块', title: '插入 GitHub 风格警告提示块', action: 'customMarkdown', payload: 'github-alert-warning' },
        { label: '注意块', title: '插入 GitHub 风格注意提示块', action: 'customMarkdown', payload: 'github-alert-caution' },
        { label: '说明', kind: 'divider' },
        { label: '查看提示块语法', title: '查看全部提示块语法', action: 'customMarkdown', payload: 'github-alert-syntax' },
      ],
    },
    { label: '无序列表', title: '无序列表', action: 'bulletList', icon: List },
    { label: '有序列表', title: '有序列表', action: 'orderedList', icon: ListOrdered },
    { label: '任务列表', title: '任务列表', action: 'taskList', icon: ListTodo },
    { label: '分割线', title: '分割线', action: 'hr', icon: SeparatorHorizontal },
    { type: 'separator', label: '', title: '' },
    { label: '行内代码', title: '行内代码', action: 'inlineCode', icon: Code },
    {
      type: 'dropdown',
      label: '块级代码',
      title: '增强代码块',
      action: 'codeBlock',
      icon: SquareCode,
      dropdown: [
        { label: '默认代码块', title: '插入默认代码块', action: 'codeBlock' },
        { label: '说明', kind: 'divider' },
        { label: '查看代码块语法', title: '查看增强代码块语法', action: 'customMarkdown', payload: 'code-syntax' },
      ],
    },
    { label: '超链接', title: '超链接', action: 'link', icon: Link },
    { label: '脚注', title: '脚注', action: 'footnote', icon: Pilcrow },
    { label: '缩写', title: '缩写', action: 'abbr', icon: 缩写图标 },
    { type: 'dropdown', label: 'Emoji 短码', title: 'Emoji 短码', action: 'emojiShortcode', icon: Smile },
    {
      type: 'dropdown',
      label: '图片',
      title: '图片',
      action: 'image',
      icon: Image,
      dropdown: [
        { label: '上传图片', title: '上传图片', action: 'image' },
        { label: '添加图片链接', title: '添加图片链接', action: 'imageLink' },
        { label: '裁剪上传', title: '裁剪上传', action: 'imageCropUpload' },
        { label: '图片网络', title: '插入图片网络', action: 'customMarkdown', payload: 'image-grid' },
      ],
      disabled: () => options.isUploading(),
    },
    {
      type: 'dropdown',
      label: '其他块',
      title: '其他自定义块',
      action: 'customMarkdown',
      icon: Blocks,
      dropdown: [
        { label: '容器式提示块', title: '插入 :::type[title] 提示块', action: 'customMarkdown', payload: 'container-alert' },
        { label: '缩进式提示块', title: '插入 !!! type 提示块', action: 'customMarkdown', payload: 'indented-alert' },
        { label: '折叠块（已折叠）', title: '插入默认收起的 ??? type 折叠块', action: 'customMarkdown', payload: 'details-alert-collapsed' },
        { label: '折叠块（未折叠）', title: '插入默认展开的 ???+ type 折叠块', action: 'customMarkdown', payload: 'details-alert-expanded' },
      ],
    },
    { label: '标签页', title: '标签页', action: 'customMarkdown', payload: 'tabs', icon: 标签页图标 },
    { label: 'GitHub 仓库卡片', title: 'GitHub 仓库卡片', action: 'customMarkdown', payload: 'github-card', icon: Github },
    { label: '剧透文本', title: '剧透文本', action: 'customMarkdown', payload: 'spoiler', icon: EyeOff },
    { type: 'dropdown', label: '表格', title: '表格', action: 'table', icon: Table },
    {
      type: 'dropdown',
      label: '各种图',
      title: '各种图',
      action: 'mermaid',
      icon: ChartArea,
      dropdown: [
        { label: '流程图', title: '流程图', action: 'mermaid', payload: 'flow' },
        { label: '时序图', title: '时序图', action: 'mermaid', payload: 'sequence' },
        { label: '甘特图', title: '甘特图', action: 'mermaid', payload: 'gantt' },
        { label: '类图', title: '类图', action: 'mermaid', payload: 'class' },
        { label: '状态图', title: '状态图', action: 'mermaid', payload: 'state' },
        { label: '饼图', title: '饼图', action: 'mermaid', payload: 'pie' },
        { label: '关系图', title: '关系图', action: 'mermaid', payload: 'relationship' },
        { label: '旅程图', title: '旅程图', action: 'mermaid', payload: 'journey' },
      ],
    },
    {
      type: 'dropdown',
      label: '公式',
      title: '公式',
      action: 'math',
      icon: SquareSigma,
      dropdown: [
        { label: '行内公式', title: '行内公式', action: 'math', payload: 'inline' },
        { label: '块级公式', title: '块级公式', action: 'math', payload: 'block' },
      ],
    },
    { type: 'separator', label: '', title: '' },
    { label: '后退', title: '后退', action: 'undo', icon: Reply },
    { label: '前进', title: '前进', action: 'redo', icon: Forward },
    { type: 'spacer', label: '', title: '' },
    {
      label: '布局',
      title: '预览布局切换',
      dynamicTitle: () => (options.previewLayoutMode() === 'split' ? '切换为全屏预览' : '切换为半屏预览'),
      action: 'previewLayoutToggle',
      dynamicIcon: () => (options.previewLayoutMode() === 'split' ? PanelRightOpen : Columns2),
      hidden: () => !options.showPreviewToggle() || !options.previewEnabled(),
      active: () => options.previewLayoutMode() === 'full',
    },
    {
      label: '类型',
      title: '预览类型切换',
      dynamicTitle: () => {
        if (options.previewType() === 'preview') {
          return '当前正文预览，点击切换为 HTML 预览'
        }
        if (options.previewType() === 'html') {
          return '当前 HTML 预览，点击切换为脑图预览'
        }
        return '当前脑图预览，点击切换为正文预览'
      },
      action: 'previewTypeToggle',
      dynamicIcon: () => {
        if (options.previewType() === 'preview') {
          return FileText
        }
        if (options.previewType() === 'html') {
          return HTML预览图标
        }
        return Network
      },
      hidden: () => !options.showPreviewToggle() || !options.previewEnabled(),
    },
    {
      label: '同步滚动',
      title: '同步滚动',
      dynamicTitle: () => (
        options.previewLayoutMode() === 'split' && options.previewType() !== 'mindmap'
          ? '同步滚动'
          : '仅半屏正文和 HTML 预览支持同步滚动'
      ),
      action: 'scrollSync',
      icon: ArrowDownUp,
      hidden: () => !options.showScrollSync(),
      disabled: () => options.previewLayoutMode() !== 'split' || options.previewType() === 'mindmap',
      active: () => options.previewLayoutMode() === 'split' && options.previewType() !== 'mindmap' && options.scrollSync(),
    },
    { type: 'separator', label: '', title: '' },
    {
      label: '源码',
      title: '源码和显示模式切换',
      action: 'sourceMode',
      dynamicIcon: () => (options.isSourceMode() ? FilePenLine : FileCode),
      active: () => options.isSourceMode(),
    },
    {
      label: '预览',
      title: '预览',
      dynamicTitle: () => (options.previewEnabled() ? '关闭预览' : '启用预览'),
      action: 'previewToggle',
      dynamicIcon: () => (options.previewEnabled() ? EyeOff : Eye),
      hidden: () => !options.showPreviewToggle(),
      active: () => options.previewEnabled(),
    },
    { type: 'separator', label: '', title: '' },
    { label: '美化', title: '美化', action: 'format', icon: 美化图标, hidden: () => !options.hasFormatContent() },
    {
      label: '大纲',
      title: '大纲',
      action: 'outlineToggle',
      icon: 大纲图标,
      hidden: () => !options.showOutlineToggle(),
      active: () => options.outlineVisible(),
    },
    {
      label: '浏览器全屏',
      title: '浏览器全屏',
      action: 'pageFullscreen',
      icon: Maximize2,
    },
    { label: '屏幕全屏', title: '屏幕全屏', action: 'fullscreen', icon: Expand },
  ]
}
