# Firefly 复刻 TODO 清单

> 记录从 `other/Firefly` 尚未复刻到 `frontend` 的功能与组件，方便逐项对照迁移。

---

## 一、独立页面

Firefly 中有完整页面，但 frontend 的博客路由里缺失的：
> 如果要复刻过来，都放到 `/blog` 下，是 `/blog?mode=about` 还是 `/blog/about` 这种到时候再讨论

- [ ] **Bangumi 追番页** (`/bangumi`) — 展示追番/观影记录的独立页面
- [ ] **相册/Gallery** (`/gallery` 及 `/gallery/:album`) — 相册列表与相册详情页
- [ ] **留言板** (`/guestbook`) — 独立的留言板页面
- [ ] **赞助页** (`/sponsor`) — 赞助展示页面
- [ ] **友链独立页** (`/friends`) — frontend 目前只有 `FriendLinksWidget`，没有独立页面
- [ ] **RSS 订阅** (`/rss.xml`) — 自动生成 RSS
- [ ] **OG 图片生成** (`/og/[...slug].png`) — 文章分享时的 OpenGraph 图片自动生成

---

## 二、评论系统组件

frontend 目前没有任何评论系统接入：

- [ ] **Twikoo**
- [ ] **Artalk**
- [ ] **Disqus**
- [ ] **Giscus**
- [ ] **Waline**

---

## 四、导航与辅助组件

- [ ] **返回顶部** (`BackToTop`)
- [ ] **返回首页** (`BackToHome`)
- [ ] **返回评论** (`BackToComment`)
- [ ] **悬浮目录** (`FloatingTOC`)  
      frontend 有 `BlogTocWidget`（侧边栏目录），但没有文章内悬浮目录
- [ ] **悬浮控制按钮组** (`FloatingControls`)  
      frontend 有同名组件，但功能可能不同，需对照确认
- [ ] **分页组件** (`Pagination`、`ClientPagination`)

---

## 五、内容增强（Markdown / 插件）

Firefly 有一整套 remark/rehype 插件来增强 Markdown，frontend 目前无对应：

- [ ] **Mermaid 图表** (`rehype-mermaid.mjs`、`remark-mermaid.js`)
- [ ] **KaTeX 数学公式** (`KatexManager`)
- [ ] **GitHub 仓库卡片** (`rehype-component-github-card.mjs`)
- [ ] **图片网格布局** (`remark-image-grid.js`)
- [ ] **阅读时间统计** (`remark-reading-time.mjs`)
- [ ] **邮件保护** (`rehype-email-protection.mjs`)
- [ ] **外部链接处理** (`rehype-external-links.mjs`)
- [ ] **Expressive Code 代码块** (`astro-expressive-code`)
- [ ] **图片灯箱** (`FancyboxManager`、`ImageWrapper`)

---

## 六、SEO / 搜索 / 分析

- [ ] **Pagefind 全文搜索** — Firefly 构建时索引；frontend 有 `SearchPage.vue`，但搜索逻辑是自定义的
- [ ] **Sitemap 自动生成** (`@astrojs/sitemap`)
- [ ] **Robots.txt 自动生成** (`src/pages/robots.txt.ts`) — frontend 目前是静态 `public/robots.txt`
- [ ] **OG 图片自动生成** (`src/pages/og/[...slug].png.ts`)
- [ ] **网站分析** (`GoogleAnalytics`、`UmamiAnalytics`、`MicrosoftClarity`、`La51Analytics`)

---

## 七、布局 / 样式 / 动画

- [ ] **文章布局切换** (`LayoutSwitchButton`)  
      Firefly 支持列表/网格/瀑布流切换，frontend 的 `BlogFeed` 目前只有一种布局
- [ ] **壁纸模式切换** (`WallpaperSwitch`)  
      frontend 有 `useBannerImages`，但没有壁纸模式切换 UI（横幅/全屏透明/纯色）
- [ ] **字体管理器** (`FontManager`)
- [ ] **Swup 页面过渡动画** (`@swup/astro`)
- [ ] **双侧边栏布局** — Firefly 支持左/右/双侧边栏，frontend 目前只有单侧边栏

---

## 八、静态资源（未搬运）

以下 `public/` 资源在 Firefly 中存在，frontend 中没有对应：

- [ ] `public/favicon/` — 多尺寸 favicon 套装
- [ ] `public/assets/js/` — `highlight.min.js`、`marked.min.js`、`twikoo.nocss.js`
- [ ] `public/assets/css/` — `highlight-github-dark.min.css`、`twikoo.css`

---

## 九、配置文件体系

Firefly 的 `src/config/` 下有大量配置模块，frontend 中没有直接对应：

- [ ] `fontConfig.ts` — 字体配置
- [ ] `commentConfig.ts` — 评论系统配置
- [ ] `expressiveCodeConfig.ts` — 代码高亮配置
- [ ] `coverImageConfig.ts` — 封面图配置
- [ ] `galleryConfig.ts` — 相册配置
- [ ] `licenseConfig.ts` — 文章许可证配置
- [ ] `adConfig.ts` — 广告配置

---

## 十、其他内容增强组件

- [ ] **相关文章推荐** (`RecommendedPost`)
- [ ] **加密文章** (`EncryptedPost`)
- [ ] **广告组件** (`Advertisement`)
- [ ] **封面图组件** (`CoverImage`)

---

## 其他

- 给整个首页的动态流添加置顶功能

- 动态也添加观看数量
