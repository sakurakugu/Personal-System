## 项目概览

个人系统，当前仓库包含以下主要子项目：

| 目录                   | 技术栈                                                        | 说明                                         |
| ---------------------- | ------------------------------------------------------------- | -------------------------------------------- |
| `apps/phone/`          | Vue 3 + TypeScript + Vite + Capacitor + Element Plus          | 手机端应用，基于 Web 技术封装 Android        |
| `apps/cloud/frontend/` | Vue 3 + TypeScript + Vite + Element Plus + Pinia + Vue Router | 云端前端，包含博客展示与后台管理界面         |
| `apps/cloud/backend/`  | Python 3.14 + FastAPI + SQLAlchemy + Alembic                  | 云端后端，提供业务 API、认证、存储与后台能力 |
| `apps/cloud/`          | Docker Compose + Nginx + PostgreSQL + Redis + MinIO           | 云端部署入口，负责本地开发依赖与生产编排     |
| `packages/api/`        | TypeScript                                                    | 前端共享 API 请求封装                        |
| `packages/domain/`     | TypeScript                                                    | 前端共享领域模型、状态与业务封装             |
| `tools/`               | Python                                                        | 启动、构建、备份等开发辅助脚本               |

---

## 约定

- Python 使用 mypy 和 ruff
- Node 使用 "npm run lint && npm run typecheck"
- 修改后要通过上述检查来防止编辑错误
- 数据库使用 15432 端口，后端使用 8000 端口，前端在 5173 端口
- 开发阶段页面均为热更新，修改代码后无需重启服务，如要使用浏览器可以用 playwright 测试
- 如需安装库，直接安装
- 修改数据库，记得添加迁移文件
- 所有注释、描述一律使用中文，回复也使用中文
- 如有表述不清晰的就直接问，不用一直猜测
- 该项目为自用项目，可以重构禁止向前兼容
