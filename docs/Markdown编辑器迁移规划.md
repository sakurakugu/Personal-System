# Markdown 编辑器迁移规划

本文记录文章 Markdown 编辑体验的迁移判断和后续待办。目标是在保留当前发布态渲染能力的前提下，把编辑器逐步迁移到更适合所见即所得编辑的方案。

## 当前结论

最终建议是：替换编辑器，保留渲染器。

也就是：

- 编辑态逐步从 `md-editor-v3` 迁移到 Milkdown。
- 发布态、预览态继续使用现有 `MarkdownRenderer`。
- 文章内容仍然只保存 Markdown 字符串，不保存 Milkdown 或 ProseMirror 的内部 JSON。

目标结构：

```text
文章 Markdown 字符串
        |
        | 编辑
        v
Milkdown 编辑器 <-> form.content
        |
        | 预览/发布
        v
现有 MarkdownRenderer
```

## 为什么保留 MarkdownRenderer

当前 `MarkdownRenderer` 不只是一个普通 Markdown 渲染组件，它承载了项目文章的最终显示标准。

相关实现：

- `packages/modules/文章/src/components/Markdown渲染器.vue`
- `packages/modules/文章/src/markdown.ts`
- `packages/modules/文章/src/composables/增强文章Markdown.ts`
- `packages/modules/文章/src/styles/article-markdown.css`

它目前负责：

- 基础 Markdown 渲染。
- KaTeX、脚注、任务列表、mark、emoji 等插件能力。
- 提示块、折叠块、标签页、特殊布局等自定义语法。
- 代码高亮、代码块增强、Mermaid、图片预览、Fancybox 等发布态增强。
- 博客前台、后台预览、关于页、留言板等多处展示一致性。

Milkdown 适合解决“直接编辑显示文本，并同步回 Markdown”的问题，但不适合直接接管最终文章渲染。否则需要把现有自定义 Markdown 语法全部重新实现为 Milkdown/ProseMirror 的 schema、parser、serializer，迁移成本会明显上升，但是最终维护成本低。

## 不推荐的方向

### 不推荐全部换成 Milkdown 渲染

原因：

- 编辑器显示效果和博客最终显示效果容易不一致。
- 现有自定义语法需要重新实现 Milkdown 插件。
- 发布态增强能力会被迫绑定编辑器生态，后续维护边界不清晰。

### 不推荐长期保留两套编辑器

短期迁移阶段可以并存，但长期不建议同时维护 `md-editor-v3` 和 Milkdown。

原因：

- 快捷键、图片上传、格式化、样式适配会变成两套逻辑。
- 表单状态同步、脏数据判断、保存逻辑更容易出现分叉。
- 后续功能每次都要判断两个编辑器是否都支持。

### 暂不建议立刻迁移到 remark/rehype

`unified + remark + rehype` 更适合 AST 管线，例如结构化分析、内部链接检查、内容迁移、服务端渲染统一等场景。当前主要诉求是编辑体验升级，不应把渲染管线迁移和编辑器迁移绑在一起。

如果后续 `markdown.ts` 继续膨胀，可以单独规划 Markdown 渲染管线重构。

## 推荐迁移路线

第一阶段先引入 Milkdown 作为新正文编辑器，但仍使用 `MarkdownRenderer` 做预览和发布态渲染。

第二阶段补齐与现有编辑器一致的基础能力，包括图片上传、快捷键、主题、工具栏、移动端布局、脏数据判断和保存逻辑。

第三阶段逐步处理自定义 Markdown 语法在 Milkdown 编辑态里的表现。优先保证原文不丢失，再按常用程度做可视化编辑。

第四阶段确认新编辑器稳定后，移除 `md-editor-v3` 相关依赖、样式和快捷键适配。

## 待办

- [x] 新增独立的 Milkdown 编辑器组件，不直接改散在页面里的逻辑。
- [x] 让 Milkdown 以 Markdown 字符串作为唯一输入输出，和 `form.content` 双向同步。
- [x] 保留当前 `MarkdownRenderer` 作为后台预览和博客发布态渲染标准。
- [x] 接入文章图片上传能力，保持上传后插入 Markdown 图片语法。
- [x] 迁移保存快捷键、格式化保存快捷键、重做快捷键等编辑器快捷键。
- [x] 初步适配亮色、暗色主题。
- [x] 初步适配桌面端分栏预览、全屏预览和移动端布局。
- [] 验证标题、段落、加粗、斜体、链接、图片、表格、代码块、任务列表等基础语法。
- [] 验证 KaTeX、脚注、Mermaid、提示块、折叠块、标签页等增强语法不会在编辑器中丢失原文。
- [] 对最常用的自定义语法补充 Milkdown 编辑态表现。
- [x] 保留源码编辑入口，便于处理 Milkdown 暂不支持的复杂语法。
- [x] 补充编辑器迁移相关测试或人工验收清单。
- [] 新编辑器稳定后移除 `md-editor-v3` 依赖。
- [] 清理 `md-editor-v3` 专用样式、DOM 查询和快捷键适配。
- [] 评估是否需要把 `MarkdownRenderer` 拆成渲染、增强、样式三层。
- [] 如果后续需要 AST 分析能力，再单独评估 `remark/rehype` 渲染管线迁移。

## 验收标准

- 写作时可以直接编辑显示文本，并实时同步 Markdown。
- 保存到后端的内容仍然是 Markdown 字符串。
- 后台预览和博客最终展示继续走同一套 `MarkdownRenderer`。
- 常规 Markdown 不丢格式，不产生明显脏 HTML。
- Milkdown 暂不支持的自定义语法至少能保留原文，不应被静默删除或改坏。
- 新旧编辑器迁移完成后，只保留一套编辑器维护入口。
