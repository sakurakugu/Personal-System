# Firefly 复刻 TODO 清单

> 记录从 `other/Firefly` 尚未复刻到 `frontend` 的功能与组件，方便逐项对照迁移。

## 一、独立页面

Firefly 中有完整页面，但 frontend 的博客路由里缺失的：

> 如果要复刻过来，都放到 `/blog` 下，是 `/blog?mode=xxx`

- [ ] **留言板** (`/guestbook`) — 独立的留言板页面
- [ ] **RSS 订阅** (`/rss.xml`) — 自动生成 RSS
- [ ] **OG 图片生成** (`/og/[...slug].png`) — 文章分享时的 OpenGraph 图片自动生成

## 二、SEO / 搜索 / 分析

- [ ] **Sitemap 自动生成** (`@astrojs/sitemap`)
- [ ] **Robots.txt 自动生成** (`src/pages/robots.txt.ts`) — frontend 目前是静态 `public/robots.txt`
- [ ] **OG 图片自动生成** (`src/pages/og/[...slug].png.ts`)
- [ ] **网站分析** (`GoogleAnalytics`、`UmamiAnalytics`、`MicrosoftClarity`、`La51Analytics`)

## 三、静态资源（未搬运）

以下 `public/` 资源在 Firefly 中存在，frontend 中没有对应：

- [ ] `public/favicon/` — 多尺寸 favicon 套装
---

# 其他

- 给整个首页的动态流添加置顶功能

- 动态也添加观看数量

- 到时候记得重构，比如将重复的 css 合并等等

- 从当前自带的评论系统改成 Twikoo 并接入后端
