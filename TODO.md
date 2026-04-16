# Firefly 复刻 TODO 清单

> 记录从 `other/Firefly` 尚未复刻到 `frontend` 的功能与组件，方便逐项对照迁移。

---

## 一、独立页面

Firefly 中有完整页面，但 frontend 的博客路由里缺失的：
> 如果要复刻过来，都放到 `/blog` 下，是 `/blog?mode=about` 还是 `/blog/about` 这种到时候再讨论

- [x] **Bangumi 追番页** (`/bangumi`) — 已作为 `BlogHome` 的 `bangumi` 视图实现
- [ ] **相册/Gallery** (`/gallery` 及 `/gallery/:album`) — 相册列表与相册详情页
- [ ] **留言板** (`/guestbook`) — 独立的留言板页面
- [x] **赞助页** (`/sponsor`) — 已作为 `BlogHome` 的 `sponsor` 视图实现
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

---

## 三、内容增强（Markdown / 插件）

Firefly 用 remark/rehype 插件在构建时处理，`frontend` 已通过客户端预处理 + DOM 后处理实现等价效果：

- [ ] **Expressive Code 代码块** (`astro-expressive-code`) — 当前为自研代码高亮，未使用 Expressive Code

---

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

## 其他

- 给整个首页的动态流添加置顶功能

- 动态也添加观看数量

- 到时候记得压行，比如将重复的 css 合并等等
