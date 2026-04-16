# Firefly 复刻 TODO 清单

> 记录从 `other/Firefly` 尚未复刻到 `frontend` 的功能与组件，方便逐项对照迁移。

---

## 一、独立页面

Firefly 中有完整页面，但 frontend 的博客路由里缺失的：
> 如果要复刻过来，都放到 `/blog` 下，是 `/blog?mode=about` 还是 `/blog/about` 这种到时候再讨论

- [ ] **相册/Gallery** (`/gallery` 及 `/gallery/:album`) — 相册列表与相册详情页
- [ ] **留言板** (`/guestbook`) — 独立的留言板页面
- [ ] **友链独立页** (`/friends`) — frontend 目前只有 `FriendLinksWidget`，没有独立页面
- [ ] **RSS 订阅** (`/rss.xml`) — 自动生成 RSS
- [ ] **OG 图片生成** (`/og/[...slug].png`) — 文章分享时的 OpenGraph 图片自动生成

---

## 二、评论系统组件

> 注：`frontend` 已接入**自研评论系统**（`ArticleReader` 内置评论 + 后台管理），但以下第三方评论系统尚未接入。

- [ ] **Twikoo**
- [ ] **Artalk**
- [ ] **Disqus**
- [ ] **Giscus**
- [ ] **Waline**


## 四、导航与辅助组件

- [ ] **返回评论** (`BackToComment`)
- [ ] **悬浮目录** (`FloatingTOC`)  
      frontend 有 `BlogTocWidget`（侧边栏目录），但没有文章内悬浮目录
- [x] **悬浮控制按钮组** (`FloatingControls`) — 已实现（包含回到首页、回到顶部）

---

## 五、SEO / 搜索 / 分析

- [ ] **Sitemap 自动生成** (`@astrojs/sitemap`)
- [ ] **Robots.txt 自动生成** (`src/pages/robots.txt.ts`) — frontend 目前是静态 `public/robots.txt`
- [ ] **OG 图片自动生成** (`src/pages/og/[...slug].png.ts`)
- [ ] **网站分析** (`GoogleAnalytics`、`UmamiAnalytics`、`MicrosoftClarity`、`La51Analytics`)

---

## 六、静态资源（未搬运）

以下 `public/` 资源在 Firefly 中存在，frontend 中没有对应：

- [ ] `public/favicon/` — 多尺寸 favicon 套装
- [ ] `public/assets/js/` — `highlight.min.js`、`marked.min.js`、`twikoo.nocss.js`
- [ ] `public/assets/css/` — `highlight-github-dark.min.css`、`twikoo.css`

---

## 七、配置文件体系

Firefly 的 `src/config/` 下有大量配置模块，frontend 中没有直接对应：

- [ ] `commentConfig.ts` — 评论系统配置
- [ ] `galleryConfig.ts` — 相册配置
- [ ] `licenseConfig.ts` — 文章许可证配置
- [ ] `adConfig.ts` — 广告配置

---

## 八、其他内容增强组件

- [ ] **广告组件** (`Advertisement`)

---

## 九、Markdown 代码块补齐计划

### P0 兼容项

- [x] 修复 `showLineNumbers=false` 被误判为开启行号
- [x] 支持 `startLineNumber=N` 自定义起始行号
- [x] 补一篇代码块能力对照测试文档，覆盖 Firefly 示例语法
- [x] 明确当前项目支持的代码块元数据语法，并记录到文档

### P1 低成本高收益

- [x] 支持 `frame="none"` 无外框代码块
- [x] 支持 `frame="code"` / `frame="terminal"` 框架类型切换
- [x] 支持 `wrap` / `wrap=false` 按块控制自动换行
- [x] 支持 `preserveIndent` / `preserveIndent=false` 控制换行缩进
- [x] 支持 `ins={...}` / `del={...}` 行级语义标记
- [x] 为普通高亮 / 插入 / 删除提供独立视觉样式
- [x] 扩充 `highlight.js` 注册语言列表并优化未知语言降级

### P2 进阶能力

- [ ] 支持按文本匹配的行内高亮，如 `"given text"`
- [ ] 支持按正则匹配的行内高亮，如 `/pattern/`
- [ ] 支持 `ins="..."` / `del="..."` 文本级标记
- [ ] 支持带标签的行标记与长标签展示
- [ ] 支持 `collapse={...}` 指定折叠区间
- [x] 支持长代码自动折叠与展开/收起按钮
- [ ] 评估 ANSI 颜色序列渲染支持
- [ ] 评估更强的整块高亮方案，替代逐行 `highlight.js`

---

## 其他

- 给整个首页的动态流添加置顶功能

- 动态也添加观看数量

- 到时候记得压行，比如将重复的 css 合并等等
