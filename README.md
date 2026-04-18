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
| 认证      | auth.py            | 3 (register/login/logout) |
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
- [前端踩坑记录](./docs/前端踩坑记录.md)
- [前端架构重构方案](./docs/前端架构重构方案.md)

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
- `AUTH_SECRET_KEY`: 认证与文件签名主密钥（生产环境请使用随机长字符串）
- `AUTH_SESSION_EXPIRE_DAYS`: 登录 Session 有效期（天）
- `AUTH_COOKIE_SECURE`: 生产环境建议设为 `true`
- `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY`: MinIO 访问密钥
- `SUPER_ADMIN_USERNAME` / `SUPER_ADMIN_PASSWORD`: 超级管理员账号

### 认证说明

当前项目使用服务端 `Session Cookie` 认证：

- 登录成功后，后端会写入 `session_id` 与 `csrf_token`
- 前端写操作会自动携带 `X-CSRF-Token`
- 后端不再提供 `refresh token` 机制，登录失效后需要重新登录
- 修改密码、管理员重置密码、停用账号、删除账号时，会主动撤销已有会话

生产环境建议：

- `AUTH_COOKIE_SECURE=true`
- `AUTH_COOKIE_SAMESITE=lax` 或按你的实际跨站需求调整
- 仅在 HTTPS 下部署登录态 Cookie

### 文件访问说明

项目中的文件访问分为两类：

- 需要登录态的后台文件访问：依赖 `Session Cookie`
- 文章图片、文章封面、文件预览等对外展示地址：优先使用后端签名 URL

注意：

- 前端与原生端现在都会把站内 `/files/...` 链接解析到当前 API 基址，不再依赖 `window.location.origin`
- 如果后续新增文件访问功能，不走签名 URL 时必须确保请求会携带 Cookie
- 如果要把文件链接发给未登录用户长期使用，应继续使用签名 URL，而不是依赖 Session

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

### 移动端热更新开发（Android）

现在支持让 Android 手机端直接连接前端开发服务器，修改前端代码后无需重新构建 App，手机端刷新或等待 HMR 即可生效。手机端部署命令现在独立为 `--phone`，不会再顺带启动前后端。

```bash
# 先启动本地开发环境
python ./tools/1.启动项目.py start

# 再单独部署 Android 手机端
python ./tools/1.启动项目.py --phone

# 指定 Android 目标 ID
python ./tools/1.启动项目.py --phone --target emulator-5554

# 真机场景下手动指定手机访问你电脑的局域网 IP
python ./tools/1.启动项目.py --phone --host 192.168.1.23

# 当前端开发服务器不在默认 5173 端口时，显式指定端口
python ./tools/1.启动项目.py --phone --port 5174
```

### 移动端安装包构建（Android）

现在支持直接通过启动脚本构建 Android 安装包。默认构建 `release` 包，传 `--debug` 时构建 `debug` 包。构建成功后会自动打开资源管理器定位到 APK 文件。

```bash
# 默认构建 release 包
python ./tools/1.启动项目.py --apk

# 构建 debug 包
python ./tools/1.启动项目.py --apk --debug

# 显式构建 release 包
python ./tools/1.启动项目.py --apk --release
```

如果你要输出已签名的 `release` 安装包，请在根目录 `.env` 中补充下面这些配置：

```dotenv
ANDROID_SIGNING_STORE_FILE=secrets/android/release.jks
ANDROID_SIGNING_STORE_PASSWORD=你的仓库密码
ANDROID_SIGNING_KEY_ALIAS=你的别名
ANDROID_SIGNING_KEY_PASSWORD=你的密钥密码
ANDROID_SIGNING_STORE_TYPE=JKS
```

说明：

- `ANDROID_SIGNING_STORE_FILE` 支持绝对路径，也支持相对项目根目录的路径
- 只要这 4 个必填项里填了任意一项，就必须全部填完整；否则脚本会直接报错
- 没有配置签名时，`release` 仍然可以构建，但产物通常是 `app-release-unsigned.apk`

说明：

- Android 原生工程目录为 `frontend/android`
- Capacitor 配置文件为 `frontend/capacitor.config.ts`
- 首次运行前请确保本机已安装 Android Studio 和 Android SDK
- `--phone` 只负责部署手机端，不会启动前后端；请先执行 `python ./tools/1.启动项目.py start`，或自行启动前端开发服务器
- 使用 `python ./tools/1.启动项目.py --phone` 时，脚本会自动选择一个可用 Android 目标；若同时连了多台设备，优先选择模拟器，也可通过 `--target` 指定
- 启动手机端时，脚本会优先从 `frontend/android/local.properties`、`ANDROID_HOME`、`ANDROID_SDK_ROOT` 和常见默认安装目录中自动探测 Android SDK，并自动补全 `frontend/android/local.properties`
- 启动手机端时，脚本会优先使用兼容的 `JAVA_HOME`，也会扫描你自定义的 Java/JDK 环境变量；如果环境里存在 `JDK 21+`，会自动优先选用，再不行才回退到常见安装目录
- `--phone` 默认连接 `http://127.0.0.1:5173`；如果前端开发服务器改了端口，请通过 `--port` 指定
- `--apk` 默认构建 `release` 包；只有显式传 `--debug` 时才构建 `debug` 包
- 目前构建的是 Android APK；如果 `release` 包已配置签名，产物通常会是 `app-release.apk`；未配置签名时，通常会是 `app-release-unsigned.apk`
- Android 模拟器热更新默认走 `10.0.2.2:5173`
- 真机热更新默认自动探测电脑局域网 IP；若探测错误，请使用 `--host` 手动指定
- 手机端热更新时，前端 API 会继续走 Vite 开发服务器代理，不需要额外修改 `VITE_NATIVE_API_BASE`
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
