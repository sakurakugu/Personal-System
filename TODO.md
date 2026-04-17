# Firefly 复刻 TODO 清单

> 记录从 `other/Firefly` 尚未复刻到 `frontend` 的功能与组件，方便逐项对照迁移。

- [ ] **留言板** (`/guestbook`) — 独立的留言板页面
- [ ] **Sitemap 自动生成** (`@astrojs/sitemap`)
- [ ] **Robots.txt 自动生成** (`src/pages/robots.txt.ts`) — frontend 目前是静态 `public/robots.txt`
- [ ] **OG 图片自动生成** (`src/pages/og/[...slug].png.ts` `/og/[...slug].png`)  — 文章分享时的 OpenGraph 图片自动生成
- [ ] **网站分析** (`GoogleAnalytics`、`UmamiAnalytics`、`MicrosoftClarity`、`La51Analytics`)
- [ ] `public/favicon/` — 多尺寸 favicon 套装
---

# 其他

- 给整个首页的动态流添加置顶功能

- 动态也添加观看数量

- 到时候记得重构，比如将重复的 css 合并等等

- 从当前自带的评论系统改成 Twikoo 并接入后端

- 点击复制按钮得到的是：https://www.sakurakugu.top/rss.xml 实际上应该是 https://www.sakurakugu.top/rss.xml

- 导航删除关于我

- 推荐部分有包括 用户名（用户） 吗