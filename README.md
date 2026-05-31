# 个人系统（Personal System）

个人使用的多端系统，当前包含云端站点、手机端应用、桌面端应用、共享前端包、云端后端和开发辅助脚本。主要能力包括博客展示、后台管理、待办、文章、文件、账单、收藏、动态、文娱数据、系统统计，以及后续 AI 与 MCP 工具接入。


## 技术栈

- 后端：FastAPI、SQLAlchemy async、Alembic、PostgreSQL、Redis、MinIO
- 前端：Vue 3、TypeScript、Vite、Pinia、Vue Router、UnoCSS、Element Plus（逐步剔除）
- 桌面端：Electron
- 手机端：Capacitor Android
- 部署：Docker Compose、Nginx
- 质量检查：Node 使用 `npm run lint && npm run typecheck`，Python 使用 `ruff` 和 `mypy`

## 快速开始

首次克隆建议带上子模块：

```bash
git clone --recurse-submodules git@github.com:sakurakugu/personal-system.git
cd personal-system
```

如果已经普通克隆过，再初始化子模块：

```bash
git submodule update --init --recursive
```

安装 Node workspace 依赖：

```bash
npm install
```

启动云端开发环境，默认会启动 Docker 依赖、后端热更新、云端前端热更新，并自动执行数据库迁移：

```bash
python ./tools/1.启动项目.py --cloud --start
```

常用入口：

| 能力 | 命令 |
| --- | --- |
| 启动云端开发环境 | `python ./tools/1.启动项目.py --cloud --start` |
| 查看云端状态 | `python ./tools/1.启动项目.py --cloud --status` |
| 停止云端开发环境 | `python ./tools/1.启动项目.py --cloud --stop` |
| 启动桌面端开发环境 | `python ./tools/1.启动项目.py --desktop --start` |
| 构建桌面端 Windows 产物 | `python ./tools/1.启动项目.py --desktop --build` |
| 启动 Android 手机端热更新 | `python ./tools/1.启动项目.py --phone` |
| 构建 Android APK | `python ./tools/1.启动项目.py --apk` |
| 创建数据备份 | `python ./tools/2.备份数据.py create` |

默认端口：

| 服务 | 端口 |
| --- | --- |
| PostgreSQL | `15432` |
| 后端 API | `8000` |
| Twikoo | `8001` |
| 云端前端 | `5173` |
| 手机端前端 | `5174` |
| 桌面端前端 | `5175` |

开发日志位于 `.cache/.dev/*.log`，排查本地热更新、后端启动、桌面端和手机端问题时优先查看这里。

## 项目结构

<details>
<summary>点击展开</summary>

| 目录 | 技术栈 | 说明 |
| --- | --- | --- |
| `apps/cloud/` | Docker Compose + Nginx + PostgreSQL + Redis + MinIO | 云端部署入口、本地依赖服务、生产编排 |
| `apps/cloud/frontend/` | Vue 3 + TypeScript + Vite + UnoCSS + Element Plus + Pinia + Vue Router | 云端前端，包含博客展示和后台管理 |
| `apps/cloud/backend/` | Python 3.14 + FastAPI + SQLAlchemy + Alembic | 云端后端，提供 API、认证、存储和后台能力 |
| `apps/phone/` | Vue 3 + TypeScript + Vite + UnoCSS + Capacitor + Element Plus | 手机端应用，基于 Web 技术封装 Android |
| `apps/desktop/` | Vue 3 + TypeScript + Vite + UnoCSS + Electron + Element Plus | 桌面端应用，提供桌面壳与本地能力接入 |
| `packages/app-core/` | TypeScript + Vue Router | 前端公共装配层，负责 bootstrap、模块路由收集、通用守卫 |
| `packages/api/` | TypeScript | 统一接口访问层 |
| `packages/domain/` | TypeScript + Pinia | 业务领域层，放类型、store、接口封装和业务流程 |
| `packages/modules/` | TypeScript + Vue 3 | 跨端业务模块，每个模块都是独立 workspace 包 |
| `packages/platform/` | TypeScript | 平台能力抽象与浏览器、桌面端、手机端适配 |
| `packages/theme/` | TypeScript + CSS | 多端共享主题、设计 token 和外观能力 |
| `packages/ui/` | Vue 3 + TypeScript | 多端复用基础 UI 组件 |
| `tools/` | Python | 启动、构建、备份等开发辅助脚本 |

当前 `packages/modules/` 下已有：博客、待办、动态、个人、工具、认证、收藏、文件、文娱、文章、账单。

</details>

## 质量检查

<details>
<summary>点击展开</summary>

前端和共享包：

```bash
npm run lint
npm run typecheck
```

云端后端：

```bash
cd apps/cloud/backend
python -m ruff check app alembic
python -m mypy
```

</details>

## 后端约定

<details>
<summary>点击展开</summary>

后端当前按 `bootstrap + shared + modules + integrations` 组织：

```text
apps/cloud/backend/app/
  bootstrap/      # 应用启动、生命周期、中间件、总路由装配
  shared/         # 跨模块基础设施，例如 db/auth/storage/kernel
  modules/        # 业务模块目录，每个模块自带 api/models/schemas/service
  integrations/   # 外部能力集成
  main.py         # 应用实例导出
```

新增后端功能时：

- 启动相关代码放 `bootstrap/`
- 可跨模块复用的基础设施放 `shared/`
- 业务能力优先落到 `modules/<name>/`
- 外部平台或三方能力放 `integrations/`
- 不再新增 `app/services`、`app/schemas`、`app/models` 这类顶层横向目录

</details>

## 前端约定

<details>
<summary>点击展开</summary>

- 通用能力优先放到 `packages/`，`apps/` 只放平台相关入口和适配。
- 业务模块优先沉到 `packages/modules/<模块名>/`，由 `packages/app-core` 收集路由并装配。
- 平台差异走 `packages/platform/`，不要在业务模块里直接散落平台判断。
- UI 基础组件放 `packages/ui/`，主题 token 和全局外观放 `packages/theme/`。

</details>

## 项目文档

<details>
<summary>点击展开</summary>

- [备份与恢复](./docs/备份与恢复.md)
- [前端弹窗开发注意事项](./docs/前端弹窗开发注意事项.md)
- [前端踩坑记录](./docs/前端踩坑记录.md)
- [前端包依赖约定](./docs/前端包依赖约定.md)
- [备忘录与资料库划分规划](./docs/备忘录与资料库划分规划.md)
- [文娱外部数据与封面导入规划](./docs/文娱外部数据与封面导入规划.md)
- [AI 与 MCP 工具接入规划](./docs/AI与MCP工具接入规划.md)

</details>

## 云端部署

<details>
<summary>点击展开</summary>

生产环境入口目录是 `apps/cloud`。首次部署时复制 `.env.example` 为 `.env` 并修改敏感配置：

```bash
cd apps/cloud
cp .env.example .env
```

核心配置：

- `DATABASE_URL`：PostgreSQL 连接字符串
- `REDIS_URL`：Redis 连接字符串
- `AUTH_SECRET_KEY`：认证与文件签名主密钥，生产环境请使用随机长字符串
- `AUTH_SESSION_EXPIRE_DAYS`：登录 Session 有效期
- `AUTH_COOKIE_SECURE`：生产环境建议设为 `true`
- `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY`：MinIO 访问密钥

启动生产环境：

```bash
python ./tools/1.启动项目.py --cloud --prod --start
```

也可以使用云端目录里的脚本：

```bash
cd apps/cloud
./start.sh
```

说明：

- 云端后端实际读取 `apps/cloud/.env`
- 根目录 `.env` 不是当前云端启动脚本和后端的正式配置来源
- 生产启动脚本会构建容器、启动服务、重启 Nginx 刷新 upstream 解析，并执行数据库迁移

</details>

## 认证说明

<details>
<summary>点击展开</summary>

当前项目使用服务端 `Session Cookie` 认证：

- 登录成功后，后端写入 `session_id` 与 `csrf_token`
- 前端写操作会自动携带 `X-CSRF-Token`
- 后端不再提供 refresh token，登录失效后需要重新登录
- 修改密码、管理员重置密码、停用账号、删除账号时，会主动撤销已有会话

生产环境建议：

- `AUTH_COOKIE_SECURE=true`
- 纯浏览器站点可使用 `AUTH_COOKIE_SAMESITE=lax`
- 如果手机原生 App 需要直接访问云端接口，建议使用 `AUTH_COOKIE_SAMESITE=none`
- 登录态 Cookie 只在 HTTPS 下部署
- 开发环境三端默认都通过各自的 Vite 代理访问 `/api`

手机原生 App 直连云端接口时，可参考：

```dotenv
AUTH_COOKIE_SECURE=true
AUTH_COOKIE_SAMESITE=none
CORS_ORIGINS=["https://www.sakurakugu.top","https://sakurakugu.top","http://localhost","capacitor://localhost"]
```

</details>

## 文件访问说明

<details>
<summary>点击展开</summary>

文件访问分为两类：

- 需要登录态的后台文件访问：依赖 `Session Cookie`
- 文章图片、文章封面、文件预览等对外展示地址：优先使用后端签名 URL

注意：

- 前端与原生端会把站内 `/files/...` 链接解析到当前 API 基址
- 如果后续新增文件访问功能，不走签名 URL 时必须确保请求会携带 Cookie
- 如果要把文件链接发给未登录用户长期使用，应继续使用签名 URL

</details>

## 手动启动开发环境

<details>
<summary>点击展开</summary>

如果不使用统一启动脚本，也可以手动启动：

```bash
# 1. 启动依赖服务
cd apps/cloud
docker compose up -d postgres redis minio twikoo

# 2. 后端开发服务器
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. 云端前端开发服务器
cd ../frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

</details>

## 手机端开发

<details>
<summary>点击展开</summary>

Android 手机端热更新：

```bash
# 先启动云端开发环境
python ./tools/1.启动项目.py --cloud --start

# 再启动手机端
python ./tools/1.启动项目.py --phone

# 指定 Android 目标
python ./tools/1.启动项目.py --phone --target emulator-5554

# 真机场景下手动指定电脑局域网 IP
python ./tools/1.启动项目.py --phone --host 192.168.1.23

# 指定手机端前端端口
python ./tools/1.启动项目.py --phone --port 5176
```

Android APK 构建：

```bash
# 默认构建 release 包
python ./tools/1.启动项目.py --apk

# 构建 debug 包
python ./tools/1.启动项目.py --apk --debug

# 仅构建 arm64-v8a release 包
python ./tools/1.启动项目.py --apk --release --arm-v8a
```

Release 签名配置放在 `apps/phone/.env`：

```dotenv
ANDROID_SIGNING_STORE_FILE=secrets/android/release.jks
ANDROID_SIGNING_STORE_PASSWORD=你的仓库密码
ANDROID_SIGNING_KEY_ALIAS=你的别名
ANDROID_SIGNING_KEY_PASSWORD=你的密钥密码
ANDROID_SIGNING_STORE_TYPE=JKS
```

说明：

- Android 原生工程目录为 `apps/phone/android`
- Capacitor 配置文件为 `apps/phone/capacitor.config.ts`
- 首次运行前需要安装 Android Studio 和 Android SDK
- `--phone` 不会启动云端前后端，请先启动云端开发环境
- `--apk` 默认构建 release 包，只有显式传 `--debug` 才构建 debug 包

</details>

## 桌面端开发

<details>
<summary>点击展开</summary>

启动桌面端开发环境：

```bash
python ./tools/1.启动项目.py --desktop --start
```

构建桌面端 Windows 产物：

```bash
# 默认构建 NSIS 安装包
python ./tools/1.启动项目.py --desktop --build

# 构建 MSI
python ./tools/1.启动项目.py --desktop --build --msi

# 构建全部 Windows 产物
python ./tools/1.启动项目.py --desktop --build --all
```

桌面端支持 Python 运行时模式：

```bash
python ./tools/1.启动项目.py --desktop --prepare-python-runtime
python ./tools/1.启动项目.py --desktop --build --python-mode embedded
```

</details>

## 数据备份

<details>
<summary>点击展开</summary>

默认备份 PostgreSQL、MinIO、Twikoo，产物保存在仓库根目录 `backups/` 下：

```bash
# 创建默认备份
python ./tools/2.备份数据.py create

# 追加 Redis
python ./tools/2.备份数据.py create --with-redis

# 查看已有备份
python ./tools/2.备份数据.py list

# 查看备份明细
python ./tools/2.备份数据.py list --verbose

# 清理旧备份，仅保留最近 7 份
python ./tools/2.备份数据.py prune --keep 7
```

更多说明见 [备份与恢复](./docs/备份与恢复.md)。

</details>

## 数据库迁移

<details>
<summary>点击展开</summary>

启动脚本会在云端启动时自动执行 `alembic upgrade head`：

```bash
# 开发环境启动时自动迁移
python ./tools/1.启动项目.py --cloud --start

# 生产环境启动时自动迁移
python ./tools/1.启动项目.py --cloud --prod --start
```

也可以单独执行迁移：

```bash
# 开发环境
python ./tools/1.启动项目.py --cloud --db-upgrade

# 生产环境
python ./tools/1.启动项目.py --cloud --prod --db-upgrade
```

创建或回滚迁移仍使用 Alembic：

```bash
cd apps/cloud/backend

alembic revision --autogenerate -m "描述"
alembic upgrade head
alembic downgrade -1
```

</details>


## 故障排除

<details>
<summary>点击展开</summary>

### 502 Bad Gateway

现象：更新代码并重新部署后，访问网站显示 `502 Bad Gateway`，Nginx 错误日志显示 `connect() failed (111: Connection refused) while connecting to upstream`。

原因：Docker 网络 DNS 缓存问题，Nginx 容器可能缓存了旧的容器 IP 地址。

生产环境启动脚本会自动重启 Nginx：

```bash
python ./tools/1.启动项目.py --cloud --prod --start
```

如果已经手动部署完成，但仍然遇到该问题，可以单独重启 Nginx：

```bash
cd apps/cloud
docker compose restart nginx
```

### 查看日志

```bash
# 查看开发日志
Get-ChildItem .cache/.dev

# 查看 Docker 服务日志
cd apps/cloud
docker compose logs -f
docker compose logs -f backend
docker compose logs -f nginx
```

</details>


## 默认账号

<details>
<summary>点击展开</summary>

部署完成后，首次启动会自动创建默认超级管理员账号：

- 用户名：`superadmin`
- 邮箱：`superadmin@sakurakugu.top`
- 初始密码：`change_me_super_admin`

登录后可以在界面中修改超级管理员的用户名、邮箱、昵称和密码。生产环境首次登录后应立即修改初始密码。

</details>
