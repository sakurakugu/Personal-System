# UnoCSS 与 Element Plus 迁移约定

本文记录前端逐步移除 Element Plus 时的样式与组件迁移约定。

## 目标

- 逐步减少业务代码对 Element Plus 组件和全局样式的依赖。
- 保留 `packages/theme` 作为唯一设计 token 来源。
- 使用 UnoCSS 提升自研组件样式编写效率，但不把业务页面变成大量原子类堆叠。
- 优先把通用能力沉淀到 `packages/ui`，各端 `apps/` 只保留平台差异。

## 当前接入方式

项目已在三个前端入口接入 UnoCSS：

- `apps/cloud/frontend/vite.config.ts`
- `apps/phone/vite.config.ts`
- `apps/desktop/vite.config.ts`

各入口已引入 `virtual:uno.css`：

- `apps/cloud/frontend/src/main.ts`
- `apps/phone/src/main.ts`
- `apps/desktop/src/main.ts`
- `apps/desktop/src/widget-main.ts`

`configs/uno.config.ts` 提供项目级配置。当前仅使用 `presetWind3`，没有接入预设重置样式，避免影响 Element Plus 和现有页面。

## 使用边界

推荐使用 UnoCSS 的位置：

- `packages/ui` 中的新组件。
- 正在替换 Element Plus 的组件内部。
- 新建且低风险的页面壳层、工具面板、设置页。
- 临时验证布局时的样式草稿，稳定后再沉淀为组件或 shortcut。

不推荐使用 UnoCSS 的位置：

- 已经稳定的老业务页面大面积重写（目前主要是先替换，而不是重写，重写之后再说，但是可以做标记，比如`// TODO: xxx`之类的）。
- 页面里堆叠复杂 class 来替代通用组件。
- 绕过 `packages/theme` 直接写大量固定颜色值。
- 重新定义一套和主题 token 并行的颜色、阴影、圆角系统。

## 主题约定

颜色、暗色模式、圆角、阴影优先来自现有 CSS 变量：

- `packages/theme/src/base.css`
- 各端 `styles/tokens.css`
- 各端 `styles/app.css`

UnoCSS 中需要使用主题值时，优先使用 `configs/uno.config.ts` 已映射的语义色：

```vue
<div class="bg-card text-text-primary">
  内容
</div>
```

需要引用暂未映射的变量时，可以使用任意值语法：

```vue
<div class="border border-[var(--theme-card-border)] bg-[var(--theme-panel-soft)]">
  内容
</div>
```

如果某个变量会在多个组件中反复使用，应补充到 `configs/uno.config.ts` 的 `theme` 或 `shortcuts`，不要在业务页面重复散写。

## Shortcut 约定

`configs/uno.config.ts` 中的 shortcut 用于表达项目语义，不用于包装一次性样式。

当前已有：

- `ps-panel`：通用面板外观。
- `ps-field`：通用输入区域外观。
- `ps-focus-ring`：统一键盘焦点样式。

新增 shortcut 时应满足至少一个条件：

- 被多个组件复用。
- 表达项目级语义。
- 能减少 Element Plus 替换过程中的重复样式。

## Element Plus 替换顺序

推荐按风险从低到高迁移：

1. `ElButton`、`ElTag`、`ElCard`、`ElEmpty`
2. `ElDialog`、`ElDrawer`、`ElDropdown`、`ElPopover`
3. `ElInput`、`ElSelect`、`ElCheckbox`、`ElRadio`、表单校验
4. `ElPagination`、`ElUpload`、日期时间类组件
5. `ElTable` 和复杂数据录入页面

替换时优先新增或完善 `packages/ui` 组件，再回到业务模块替换使用方。

## 开发检查

修改前端后执行：

```bash
npm run lint && npm run typecheck
```

如果只修改单个前端应用，可以先执行对应 workspace 的检查，但合并前仍应跑根级检查。
