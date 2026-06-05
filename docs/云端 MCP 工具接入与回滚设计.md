# 云端 MCP 工具接入与回滚设计

## 背景

后续需要给 AI 提供可调用的云端工具，让 AI 能读取和操作个人系统里的待办、文章、文件、统计等能力。

当前只考虑云端能力，不把桌面端独有能力纳入云端 MCP。桌面端已经存在的本地能力和 CLI 命令，可以后续由桌面端或本机 MCP Server 单独暴露，不放进云端后端里。

本设计优先满足：

- 复用现有云端后端能力
- 保持认证、权限、日志和事务一致
- 支持 AI 写错后的业务级撤销
- 第一版小步落地，避免一开始把 MCP 做成另一套后端

## 结论

推荐在 `apps/cloud/backend` 内直接接入 MCP Server，挂到现有 FastAPI 进程中。

入口建议：

```text
POST /mcp
GET /mcp
DELETE /mcp
```

传输方式建议使用 MCP 官方 Python SDK 的 Streamable HTTP。

不建议第一版把 MCP 拆成独立服务。原因是当前后端已经有完整的：

- FastAPI 应用构建入口
- SQLAlchemy async 会话和事务管理
- 设备令牌认证
- 用户权限模型
- 业务 service 层
- 日志基础设施

MCP 层应只是协议适配层，核心业务仍然调用现有 service。

## 当前代码基础

当前后端已经具备适合接入 MCP 的基础结构：

- `apps/cloud/backend/app/bootstrap/app.py`
  - FastAPI 应用创建入口
- `apps/cloud/backend/app/shared/db/session.py`
  - 异步数据库会话和事务管理
- `apps/cloud/backend/app/shared/auth/deps.py`
  - 当前用户解析和角色权限
- `apps/cloud/backend/app/shared/auth/device_deps.py`
  - Bearer 设备令牌解析
- `apps/cloud/backend/app/modules/auth/device_service.py`
  - 设备令牌签发、校验和吊销
- `apps/cloud/backend/app/modules/todos/service.py`
  - 待办业务逻辑
- `apps/cloud/backend/app/modules/articles/service.py`
  - 文章业务服务入口
- `apps/cloud/backend/app/core/logger.py`
  - 统一日志配置

这些代码已经把“HTTP API 路由”和“业务逻辑”分开，MCP 工具可以直接复用 service 层，不需要反向调用站内 HTTP API。

## 推荐目录结构

建议新增：

```text
apps/cloud/backend/app/mcp/
  __init__.py
  server.py
  auth.py
  runtime.py
  schemas.py
  operation_log.py
  tools/
    __init__.py
    todos.py
    articles.py
    files.py
```

职责划分：

| 文件 | 职责 |
| --- | --- |
| `server.py` | 创建 MCP Server、注册工具、导出 ASGI app |
| `auth.py` | 解析 MCP 请求里的 Bearer Token，得到用户和权限范围 |
| `runtime.py` | 统一事务、日志、异常转换、耗时统计 |
| `schemas.py` | MCP 工具专用入参和返回模型 |
| `operation_log.py` | 写操作审计和撤销记录 |
| `tools/todos.py` | 待办相关工具 |
| `tools/articles.py` | 文章相关工具 |
| `tools/files.py` | 文件相关工具 |

## 挂载方式

推荐在应用创建时挂载 MCP ASGI app。

大致结构：

```python
def 创建应用() -> FastAPI:
    app = FastAPI(...)
    注册中间件(app, app_logger=app_logger)
    注册应用路由(app, include_dev_auth=...)
    注册MCP服务(app)
    return app
```

`注册MCP服务(app)` 内部只负责把 MCP 的 ASGI 应用挂到 `/mcp`。

MCP 不放到 `/api/v1` 下。原因是 MCP 是协议入口，不是普通 REST API 版本。

## SDK 选择

第一版建议使用官方 Python SDK。

当前已经下载的参考目录：

```text
other/python-sdk
other/fastmcp
other/servers
```

建议优先看：

- `other/python-sdk/examples/servers/simple-tool`
- `other/python-sdk/examples/servers/simple-streamablehttp`
- `other/python-sdk/examples/servers/simple-auth`

`other/fastmcp` 可以作为开发体验和挂载方式的参考，但第一版不建议依赖 FastMCP 作为主框架。官方 SDK 足够完成当前目标，也更贴近协议本身。

## 认证设计

MCP 请求只接受 Bearer Token，不使用浏览器 Cookie。

建议复用现有设备令牌体系，但为 MCP 增加独立设备类型和权限范围。

### 设备类型

建议给 `设备会话类型` 增加：

```text
mcp
```

### 权限范围

建议给 `设备会话范围` 增加：

```text
mcp_readonly
mcp_full
```

语义：

| 范围 | 说明 |
| --- | --- |
| `mcp_readonly` | 只允许调用读取类工具 |
| `mcp_full` | 允许调用读取和写入类工具 |

不建议直接复用 `full_client`。AI 工具调用和真实客户端登录不是同一个安全模型，单独 scope 更容易审计和收缩权限。

### 令牌签发

建议新增普通 HTTP API：

```text
POST /api/v1/auth/mcp/token
```

签发时要求当前用户已登录，并创建一条 `user_device_sessions` 记录。

建议请求参数：

```text
device_name
scope
client_version
platform
```

建议返回：

```text
token
expires_at
session
```

### 迁移

由于当前 `设备会话类型` 和 `设备会话范围` 是 PostgreSQL enum，新增枚举值时需要 Alembic 迁移。

## 工具设计原则

MCP 工具应该偏少、偏稳定、偏业务语义，不应该把所有 HTTP API 原样暴露给 AI。

每个工具都应满足：

- 名称清晰
- 输入结构明确
- 返回结构稳定
- 写操作有审计记录
- 高风险操作支持预览或确认
- 不让 AI 自己拼反向操作

建议命名使用模块前缀：

```text
todos.list
todos.create
todos.update
todos.complete
articles.list_mine
articles.get
articles.create_draft
articles.update_draft
```

## 第一版工具范围

第一版建议只暴露待办和文章草稿能力。

### 待办工具

建议提供：

| 工具 | 权限 | 是否可撤销 | 说明 |
| --- | --- | --- | --- |
| `todos.list` | `mcp_readonly` | 否 | 查询当前用户待办 |
| `todos.get` | `mcp_readonly` | 否 | 读取待办详情 |
| `todos.create` | `mcp_full` | 是 | 创建待办 |
| `todos.update` | `mcp_full` | 是 | 更新待办 |
| `todos.complete` | `mcp_full` | 是 | 完成待办 |
| `todos.uncomplete` | `mcp_full` | 是 | 撤销完成 |
| `todos.delete` | `mcp_full` | 是 | 移入回收站 |
| `todos.restore` | `mcp_full` | 是 | 从回收站恢复 |

### 文章工具

建议提供：

| 工具 | 权限 | 是否可撤销 | 说明 |
| --- | --- | --- | --- |
| `articles.list_mine` | `mcp_readonly` | 否 | 查询我的文章 |
| `articles.get` | `mcp_readonly` | 否 | 读取文章详情 |
| `articles.create_draft` | `mcp_full` | 是 | 创建草稿 |
| `articles.update_draft` | `mcp_full` | 是 | 更新草稿 |

第一版不建议开放文章发布、永久删除、批量修改。

### 文件工具

第一版建议只读：

| 工具 | 权限 | 是否可撤销 | 说明 |
| --- | --- | --- | --- |
| `files.list` | `mcp_readonly` | 否 | 查询文件列表 |
| `files.get_metadata` | `mcp_readonly` | 否 | 读取文件元信息 |

暂不开放上传、删除、覆盖。文件类错误回滚成本更高，后续再单独设计。

## 执行流程

每次 MCP tool 调用建议固定成一个事务。

流程：

```text
收到 MCP tool 调用
  -> 解析 Bearer Token
  -> 校验设备会话和 scope
  -> 打开 AsyncSession
  -> 解析当前用户
  -> 调用现有 service
  -> 写入操作日志
  -> commit
  -> 返回工具结果
```

如果中间发生异常：

```text
异常
  -> rollback
  -> 记录失败日志
  -> 转成 MCP 错误返回
```

这类失败属于事务级回滚。只要数据库事务还没提交，数据不会落库。

## 操作日志

AI 调用成功但改错了，不能依赖数据库事务回滚。事务只能处理失败，不能处理“成功但语义错误”。

因此所有写工具都要记录业务操作日志。

建议新增表：

```text
mcp_operation_logs
```

建议字段：

```text
id
user_id
device_session_id
tool_name
status
target_type
target_id
args_json
before_json
after_json
result_json
error_message
duration_ms
is_undoable
undo_tool_name
undoable_until
undone_at
undone_by_operation_id
created_at
updated_at
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `user_id` | 操作所属用户 |
| `device_session_id` | 调用来源设备会话 |
| `tool_name` | MCP 工具名 |
| `status` | `success`、`failed`、`undone` |
| `target_type` | 业务对象类型，例如 `todo`、`article` |
| `target_id` | 业务对象 ID |
| `args_json` | 工具输入摘要 |
| `before_json` | 写入前快照 |
| `after_json` | 写入后快照 |
| `result_json` | 返回结果摘要 |
| `error_message` | 失败原因 |
| `duration_ms` | 调用耗时 |
| `is_undoable` | 是否允许撤销 |
| `undo_tool_name` | 对应撤销处理器 |
| `undoable_until` | 撤销截止时间 |
| `undone_at` | 实际撤销时间 |
| `undone_by_operation_id` | 哪次撤销操作执行了回滚 |

`before_json` 和 `after_json` 不应该保存过大的内容。文章正文这类大字段可以按需保存，或后续拆成专门的版本快照表。

## 回滚设计

回滚分两类。

### 事务级回滚

用于处理执行失败。

例如：

- 参数校验失败
- 权限不足
- service 抛异常
- 数据库写入失败

这种情况直接依赖 `AsyncSession.rollback()`。

### 业务级撤销

用于处理执行成功但后来发现改错。

必须由服务端定义撤销规则，不让 AI 自己推导反向操作。

建议提供三个 MCP 管理工具：

| 工具 | 权限 | 说明 |
| --- | --- | --- |
| `operations.list_recent` | `mcp_readonly` | 查看最近 MCP 写操作 |
| `operations.get` | `mcp_readonly` | 查看某次操作详情 |
| `operations.undo` | `mcp_full` | 撤销一次可撤销操作 |

`operations.undo` 只接收 `operation_id`，不接收任意 SQL 或任意反向参数。

## 各模块撤销策略

### 待办

待办最适合作为第一批可撤销工具。

建议：

| 原操作 | 撤销方式 |
| --- | --- |
| `todos.create` | 软删除新建的待办，必要时可硬删 |
| `todos.update` | 根据 `before_json` 恢复字段和标签 |
| `todos.complete` | 调用现有取消完成逻辑 |
| `todos.uncomplete` | 根据完成事件重新补一条完成记录 |

待办已经有软删除、完成事件和重复任务状态逻辑，所以撤销成本较低。

### 文章

文章建议只对草稿开放写操作。

建议：

| 原操作 | 撤销方式 |
| --- | --- |
| `articles.create_draft` | 软删除草稿 |
| `articles.update_draft` | 根据快照恢复标题、正文、摘要、标签、状态等字段 |

发布、删除、修改已发布文章第一版不开放给 MCP。

如果后续要开放已发布文章编辑，建议先做文章版本快照表，而不是只依赖 `mcp_operation_logs.before_json`。

### 文件

文件第一版只读。

后续如果要开放文件写操作，需要单独设计：

- 上传后的孤儿文件清理
- 删除前对象存储回收站
- 覆盖前版本保留
- MinIO 对象和数据库记录一致性

文件类能力不建议和待办、文章一起第一批开放写入。

## 高风险操作

以下操作建议采用两阶段模式：

```text
dry_run -> confirm
```

高风险操作包括：

- 批量更新
- 批量删除
- 永久删除
- 文件覆盖
- 文章发布
- 修改用户、权限、系统设置

`dry_run` 返回影响范围，不落库。

`confirm` 必须带上 `preview_id` 或 `operation_plan_id`，并且服务端重新校验影响范围是否仍然一致。

第一版可以暂不实现两阶段，只要不暴露高风险写操作即可。

## 返回格式建议

写工具成功返回建议包含：

```json
{
  "operation_id": "019...",
  "undoable": true,
  "undoable_until": "2026-05-28T12:00:00+08:00",
  "target": {
    "type": "todo",
    "id": "019..."
  },
  "summary": "已创建待办：整理 MCP 接入方案",
  "data": {}
}
```

读工具返回可以不包含 `operation_id`。

撤销工具成功返回建议包含：

```json
{
  "operation_id": "019...",
  "undone_operation_id": "019...",
  "summary": "已撤销待办更新",
  "target": {
    "type": "todo",
    "id": "019..."
  }
}
```

## 日志建议

除数据库操作日志外，还建议使用普通应用日志记录 MCP 调用。

每次调用至少记录：

```text
tool_name
user_id
device_session_id
duration_ms
success
operation_id
args_summary
error_detail
```

不要在普通日志里打印完整正文、token、密码、敏感配置。

## 测试建议

第一批测试建议覆盖：

- MCP Bearer Token 解析
- `mcp_readonly` 不能调用写工具
- `mcp_full` 能调用写工具
- 写工具成功后生成 operation log
- 工具异常时数据库 rollback
- `todos.create` 可撤销
- `todos.update` 可撤销
- `todos.complete` 可撤销
- 已撤销操作不能重复撤销
- 超过 `undoable_until` 后不能撤销

后端质量检查仍按项目约定：

```bash
ruff check apps/cloud/backend
mypy apps/cloud/backend
```

如果后续改动前端，再运行：

```bash
npm run lint
npm run typecheck
```

## 分阶段计划

### 第一阶段：最小 MCP 接入

目标：

- [x] 安装官方 MCP Python SDK
- [x] 新增 `/mcp` 入口
- [x] 接入 Bearer Token 认证
- [x] 暴露一个只读测试工具，例如 `system.ping`
- [ ] 打通 MCP Inspector 或本地 client 调用

### 第二阶段：待办只读和写入

目标：

- [x] 暴露 `todos.list`
- [x] 暴露 `todos.get`
- [x] 暴露 `todos.create`
- [x] 暴露 `todos.update`
- [x] 暴露 `todos.complete`
- [x] 暴露 `todos.uncomplete`
- [x] 暴露 `todos.delete`
- [x] 暴露 `todos.restore`
- [ ] 增加 MCP 调用日志

### 第三阶段：操作日志和撤销

目标：

- [ ] 新增 `mcp_operation_logs`
- [ ] 写工具返回 `operation_id`
- [ ] 暴露 `operations.list_recent`
- [ ] 暴露 `operations.get`
- [ ] 暴露 `operations.undo`
- [ ] 完成待办相关撤销

### 第四阶段：文章草稿能力

目标：

- [ ] 暴露 `articles.list_mine`
- [ ] 暴露 `articles.get`
- [ ] 暴露 `articles.create_draft`
- [ ] 暴露 `articles.update_draft`
- [ ] 支持草稿撤销

### 第五阶段：扩展更多模块

目标：

- [ ] 文件只读
- [ ] 收藏只读或低风险写入
- [ ] 文娱条目低风险写入
- [ ] 统计查询

高风险写操作等两阶段确认机制成熟后再开放。

## 暂不做事项

第一版暂不做：

- [ ] OAuth 授权服务器
- [ ] 多租户 MCP 网关
- [ ] 通用 SQL 执行工具
- [ ] 任意文件写入工具
- [ ] 系统管理工具
- [ ] 文章发布工具
- [ ] 批量删除工具
- [ ] 全局事件溯源
- [ ] 数据库级自动反向 SQL 回滚

这些能力不是不能做，而是不适合作为第一批云端 MCP 工具。

## 推荐默认策略

默认策略如下：

- MCP 入口放在云端后端现有 FastAPI 进程
- 只用 Bearer Token
- MCP 使用独立设备类型和权限范围
- 工具直接调用 service 层
- 一次工具调用一个事务
- 失败靠事务 rollback
- 成功后改错靠 operation log + 服务端 undo
- 第一批只做待办和文章草稿
- 文件和系统管理先只读或暂不开放

这样可以先把 AI 调用能力跑起来，同时保留可审计、可撤销、可收缩权限的空间。
