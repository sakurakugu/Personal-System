# Web 系统（Web System）

个人博客 + 看板管理系统，基于 FastAPI + Vue 3 + Element Plus 构建。

## 技术栈

- **后端**: FastAPI + SQLAlchemy (async) + PostgreSQL + Redis + MinIO
- **前端**: Vue 3 + TypeScript + Element Plus + Pinia + Vue Router
- **部署**: Docker Compose + Nginx

---

## 后端 API

### 9 个 API 模块，共 38 个路由

| 模块      | 文件               | 路由数                            |
| --------- | ------------------ | --------------------------------- |
| 认证      | auth.py            | 4 (register/login/refresh/logout) |
| 用户      | users.py           | 2 (get/update profile)            |
| 文章      | articles.py        | 6 (CRUD + list + my/list)         |
| 分类/标签 | categories_tags.py | 6                                 |
| 评论      | comments.py        | 5 (CRUD + 审核 + pending 列表)     |
| 待办      | todos.py           | 4 (CRUD)                          |
| 文件      | files.py           | 3 (upload/list/delete)            |
| 统计      | stats.py           | 2 (dashboard + pageview)          |
| 管理员    | admin.py           | 1 (system status)                 |

### 代码规范

- 所有注释使用中文
- 类型检查：`mypy`
- 代码风格：`ruff`

---

## 前端页面

### 10 个主要页面组件

| 页面            | 功能                                      |
| --------------- | ----------------------------------------- |
| BlogHome        | 博客首页 — 文章列表/搜索/分类筛选/分页    |
| ArticleDetail   | 文章详情 — Markdown 渲染/代码高亮/评论系统 |
| LoginModal      | 登录/注册弹窗                             |
| DashboardLayout | 侧边栏导航                                |
| DashboardHome   | 个人看板（统计卡片）                      |
| TodosPage       | 三栏看板式待办管理                        |
| ArticlesManage  | 文章列表管理                              |
| ArticleEditor   | Markdown 编辑器（创建/编辑）               |
| FilesPage       | 文件上传/管理/复制链接                    |
| StatsPage       | ECharts 访问趋势图                        |
| SystemPage      | CPU/内存/磁盘圆环图（管理员）             |

---

## 项目文档

- [前端弹窗约定](./docs/前端弹窗开发注意事项.md)

---

## DevOps

### 服务架构

- `docker-compose.yml` — 6 个服务（postgres/redis/minio/backend/frontend/nginx）
- `nginx/conf.d/default.conf` — www + api 反向代理（含 HTTPS 预留）
- `start.sh` — 启动脚本

---

## 部署方式

### 生产环境部署

```bash
cd /root/web-system

# 1. 编辑 .env 中的密码和密钥
vim .env

# 2. 启动服务
./start.sh
```

### 环境变量配置

复制 `.env.example` 为 `.env` 并修改：

- `DATABASE_URL`: PostgreSQL 连接字符串
- `REDIS_URL`: Redis 连接字符串
- `JWT_SECRET_KEY`: JWT 密钥（生产环境请使用随机长字符串）
- `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY`: MinIO 访问密钥
- `SUPER_ADMIN_USERNAME` / `SUPER_ADMIN_PASSWORD`: 超级管理员账号

---

## 本地开发

### 开发模式（前后端热更新 + 依赖 Docker）

```bash
# 启动：postgres/redis/minio 用 docker，前后端用 dev 热更新
python ./tools/1.启动项目.py start

# 查看状态
python ./tools/1.启动项目.py status

# 停止
python ./tools/1.启动项目.py stop
```

### 手动启动开发环境

```bash
# 1. 启动依赖服务（PostgreSQL/Redis/MinIO）
docker compose up -d postgres redis minio

# 2. 后端开发服务器（热更新）
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. 前端开发服务器（热更新）
cd frontend
npm install
npm run dev
```

### 依赖与质量检查

```bash
# 前端（Node）
cd frontend
npm install
npm run lint
npm run typecheck

# 后端（Python）
cd backend
python -m pip install -r requirements.txt
python -m ruff check app alembic
python -m mypy
```

### 移动端封装（Capacitor）

前端已接入 Capacitor，可直接封装 Android 应用。

```bash
cd frontend

# 构建并同步 Web 资源到原生工程
npm run cap:sync

# 构建、同步并用 Android Studio 打开工程
npm run cap:android

# 使用本地后端（Android 模拟器 -> 宿主机 8000 端口）
npm run cap:sync:local
npm run cap:android:local
```

说明：

- Android 原生工程目录为 `frontend/android`
- Capacitor 配置文件为 `frontend/capacitor.config.ts`
- 首次运行前请确保本机已安装 Android Studio 和 Android SDK
- 如果只改了前端页面，重新执行 `npm run cap:sync` 即可同步最新资源
- App 内已接入返回键、状态栏和键盘基础适配
- 本地 Android 模拟器调试默认走 `10.0.2.2:8000`
- 如果要在真机上连本地后端，请把 `frontend/.env.mobile-local` 中的 `VITE_NATIVE_API_BASE` 改成你的局域网 IP

---

## 故障排除

### 502 Bad Gateway

**现象**: 更新代码并重新部署后，访问网站显示 `502 Bad Gateway`，Nginx 错误日志显示 `connect() failed (111: Connection refused) while connecting to upstream`

**原因**: Docker 网络 DNS 缓存问题，Nginx 容器可能缓存了旧的容器 IP 地址

**解决**: 重启 Nginx 容器刷新 DNS 解析
```bash
docker compose restart nginx
```

### 数据库迁移

使用 Alembic 进行数据库迁移：

```bash
cd backend

# 创建新迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f nginx
```

---

## 默认账号

部署完成后，使用 `.env` 中配置的超级管理员账号登录：

- 用户名：`superadmin`（或自定义）
- 密码：`change_me_super_admin`（请生产环境修改）
