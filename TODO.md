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

- [x] 优化文章详情页请求链路，移除进入详情时的全量文章元数据请求

- [x] 优化文章详情页公共设置读取，统一复用全局 settings store，避免重复请求

- [x] 优化仪表盘统计口径，区分个人数据与全站数据，避免图表含义混淆

- [x] 优化编辑器初始化时机，避免在非编辑场景预加载 `md-editor-v3`

- [ ] 优化后台超大页面与服务模块拆分，优先处理文件管理、待办、记账相关页面与服务

- [x] 完成 `FilesPage` 第一阶段拆分，抽离共享类型、常量与纯函数

- [x] 完成 `FilesPage` 第二阶段拆分，抽离资源展示与文件能力判断工具

- [x] 完成 `FilesPage` 第三阶段拆分，抽离选择态与批量重命名纯函数

- [x] 完成 `FilesPage` 第四阶段拆分，抽离右键菜单状态构造逻辑

- [x] 完成 `FilesPage` 第五阶段拆分，抽离资源分组与批量操作结果汇总逻辑

- [x] 完成 `FilesPage` 第六阶段拆分，抽离资源操作 API 编排逻辑

- [x] 完成 `FilesPage` 第七阶段拆分，抽离文件与目录上传流程

- [x] 完成 `FilesPage` 第八阶段拆分，抽离编辑态草稿构造与判定逻辑

- [x] 完成 `FilesPage` 第九阶段拆分，抽离输入框聚焦与编辑键盘交互逻辑

- [x] 完成 `FilesPage` 第十阶段拆分，抽离编辑态保存流程与已有编辑态回焦编排

- [x] 完成 `FilesPage` 第十一阶段拆分，抽离资源下载与媒体预览切换逻辑

- [x] 完成 `FilesPage` 第十二阶段拆分，抽离文件与目录上传入口编排逻辑

- [x] 完成 `FilesPage` 第十三阶段拆分，抽离拖拽移动协议与拖放编排逻辑

- [x] 完成 `FilesPage` 第十四阶段拆分，抽离批量删除、移动与重命名对话框编排逻辑

- [x] 完成 `FilesPage` 第十五阶段拆分，抽离文件夹删除确认与右键菜单触发编排逻辑

- [x] 完成 `FilesPage` 第十六阶段拆分，抽离资源拉取、全局搜索与刷新视图的数据编排逻辑

- [x] 优化 Feed 首页缓存失效策略，避免通过 `SCAN` 全量匹配删除缓存键

- [x] 优化系统监控数据存储，从进程内内存态迁移到可跨实例共享的存储

- 给整个首页的动态流添加置顶功能

- 动态也添加观看数量

- 到时候记得重构，比如将重复的 css 合并等等

- 从当前自带的评论系统改成 Twikoo 并接入后端

- 点击复制按钮得到的是：https://www.sakurakugu.top/rss.xml 实际上应该是 https://www.sakurakugu.top/rss.xml

- 导航删除关于我

- 推荐部分有包括 用户名（用户） 吗
