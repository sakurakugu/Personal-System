# Web系统（Web System）

### 后端（FastAPI） — 9个API模块，38个路由

| 模块 | 文件 | 路由数 |
|---|---|---|
| 认证 | auth.py | 4 (register/login/refresh/logout) |
| 用户 | users.py | 2 (get/update profile) |
| 文章 | articles.py | 6 (CRUD + list + my/list) |
| 分类/标签 | categories_tags.py | 6 |
| 评论 | comments.py | 5 (CRUD + 审核 + pending列表) |
| 待办 | todos.py | 4 (CRUD) |
| 文件 | files.py | 3 (upload/list/delete) |
| 统计 | stats.py | 2 (dashboard + pageview) |
| 管理员 | admin.py | 1 (system status) |

### 前端（Vue 3 + Naive UI） — 10个页面组件

| 页面 | 功能 |
|---|---|
| BlogHome | 博客首页 — 文章列表/搜索/分类筛选/分页 |
| ArticleDetail | 文章详情 — Markdown渲染/代码高亮/评论系统 |
| LoginModal | 登录/注册弹窗 |
| DashboardLayout | 侧边栏导航 |
| DashboardHome | 个人看板（统计卡片） |
| TodosPage | 三栏看板式待办管理 |
| ArticlesManage | 文章列表管理 |
| ArticleEditor | Markdown编辑器（创建/编辑） |
| FilesPage | 文件上传/管理/复制链接 |
| StatsPage | ECharts 访问趋势图 |
| SystemPage | CPU/内存/磁盘圆环图（管理员） |

### DevOps

- docker-compose.yml — 6个服务（postgres/redis/minio/backend/frontend/nginx）
- nginx/conf.d/default.conf — www + api 反向代理（含HTTPS预留）
- deploy.sh — 一键部署脚本

### 部署方式

```bash
cd /root/web-system
# 编辑 .env 中的密码和密钥
vim .env
# 一键部署
./deploy.sh
```
