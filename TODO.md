# Firefly 复刻 TODO 清单

> 记录从 `other/Firefly` 尚未复刻到 `frontend` 的功能与组件，方便逐项对照迁移。

- [ ] **留言板** (`/guestbook`) — 独立的留言板页面
- [ ] **Sitemap 自动生成** (`@astrojs/sitemap`)
- [ ] **Robots.txt 自动生成** (`src/pages/robots.txt.ts`) — frontend 目前是静态 `public/robots.txt`
- [ ] **OG 图片自动生成** (`src/pages/og/[...slug].png.ts` `/og/[...slug].png`)  — 文章分享时的 OpenGraph 图片自动生成
- [ ] **网站分析** (`GoogleAnalytics`、`UmamiAnalytics`、`MicrosoftClarity`、`La51Analytics`)
- [ ] `public/favicon/` — 多尺寸 favicon 套装
---

# 项目结构重构

> 结论：根目录 `backend / frontend / nginx / tools` 这一层暂时不用动，重点重构前后端内部结构，按领域逐步收口，不做一次性推翻重来。

## 后端

- [x] 抽离 `backend/app/main.py` 的路由注册，新增统一注册模块，避免入口继续堆积 `include_router`
- [ ] 以“领域优先”重组后端目录，逐步从 `api / services / models / schemas` 横向分层迁移到按领域收口
- [ ] 第一批优先重构 `files` 领域，拆分超大 `service`，至少分出上传处理、目录树查询、文件查询、预览/下载、压缩包处理
- [ ] 第二批重构 `users` 领域，把用户资料更新、管理员用户管理、权限校验、密码处理、会话撤销拆开
- [ ] 第三批重构 `articles` 领域，把文章 CRUD、文章图片、文章检索、文章响应组装继续收口到同一领域目录
- [ ] 第四批重构 `bills` 领域，避免账单服务继续膨胀成单文件业务中心
- [ ] 为重构后的领域补齐内部边界约定：路由只做参数接收与响应返回，业务校验尽量下沉到领域服务
- [ ] 重构过程中同步清理跨领域直接引用，减少一个领域直接依赖多个其他领域内部实现

建议目标形态：

```text
backend/app/
  main.py
  core/
  api/
    health.py
    public_files.py
    deps.py
    v1/
      __init__.py
      router.py
  domains/
    files/
      api.py
      models.py
      schemas.py
      service.py
      queries.py
      storage.py
    users/
      api.py
      models.py
      schemas.py
      service.py
      permissions.py
    articles/
      api.py
      models.py
      schemas.py
      service.py
      images.py
      search.py
```

## 前端

- [ ] 保持 `src/features` 作为主要业务承载层，不再新增“页面旁边散落一组同前缀文件”的模式
- [x] 优先把文件管理页从 `views/dashboard/FilesPage.vue` 周边文件迁入 `src/features/files/explorer/`
- [x] 将 `files-explorer.*` 这一组文件按职责归并到 `explorer` 子目录，例如 `actions`、`editing`、`selection`、`preview`
- [ ] 页面组件 `FilesPage.vue` 只保留页面编排、视图状态和交互入口，不继续承载大量业务细节
- [ ] 继续把强业务逻辑下沉到 `features/*`，避免 `views/*` 直接堆接口调用、转换逻辑和通用错误处理
- [ ] 收敛 `stores` 的职责，只保留真正的全局状态：认证、主题、外观、运行环境
- [ ] 评估 `todo`、`moment`、`article` 等 store 是否逐步并回对应 `features`，减少“feature + store 双中心”并存
- [ ] 统一 `features/*` 的内部结构，至少约定 `api.ts`、`types.ts`、可选 `model.ts` / `store.ts` / `composables.ts`
- [ ] 逐步减少 `utils` 中偏业务的内容，把领域工具迁回对应 `features`

建议目标形态：

```text
frontend/src/
  app/
  router/
  components/
  stores/
    auth.ts
    theme.ts
    blog-appearance.ts
    api-environment.ts
  features/
    files/
      api.ts
      types.ts
      explorer/
        model.ts
        actions.ts
        editing.ts
        selection.ts
        preview.ts
        resource.ts
    todos/
      api.ts
      types.ts
      store.ts
      transfer.ts
    articles/
      api.ts
      types.ts
      editor/
        useArticleEditor.ts
  views/
    dashboard/
      FilesPage.vue
      ArticleEditor.vue
```

## 执行顺序

- [x] 第一步：先抽后端路由注册和前端文件管理模块，这两处收益最高、风险也最可控
- [ ] 第二步：处理后端 `files` / `users` / `articles` 三个领域的大文件问题
- [ ] 第三步：收敛前端 `stores` 与 `features` 的职责边界
- [ ] 第四步：最后再做目录层面的统一命名和历史遗留文件清理
- [ ] 每完成一个阶段后，运行前端 `lint + typecheck` 与后端 `ruff + mypy`

# 其他

- 给整个首页的动态流添加置顶功能

- 动态也添加观看数量

- 到时候记得重构，比如将重复的 css 合并等等

- 从当前自带的评论系统改成 Twikoo 并接入后端

- 点击复制按钮得到的是：https://www.sakurakugu.top/rss.xml 实际上应该是 https://www.sakurakugu.top/rss.xml

- 导航删除关于我

- 推荐部分有包括 用户名（用户） 吗
