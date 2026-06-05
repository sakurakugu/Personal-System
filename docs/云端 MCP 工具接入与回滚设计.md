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

当前 MCP 基础能力已经落地：`/mcp` Streamable HTTP 入口、Bearer Token 认证、事务运行时、工具注册分发、操作日志和撤销、待办工具、操作查询工具、MCP 令牌签发接口。

文章 MCP 工具当前还没有对应的 `apps/cloud/backend/app/mcp/tools/articles.py`，下一阶段应按本文的文章能力设计补齐。

## 推荐目录结构

当前目录已经存在大部分 MCP 基础文件，后续建议补齐文章和文件工具：

```text
apps/cloud/backend/app/mcp/
  __init__.py
  server.py
  auth.py
  runtime.py
  context.py
  registry.py
  models.py
  operation_log.py
  tools/
    __init__.py
    todos.py
    system.py
    operations.py
    articles.py
    files.py
```

职责划分：

| 文件 | 职责 |
| --- | --- |
| `server.py` | 创建 MCP Server、注册工具、导出 ASGI app |
| `auth.py` | 解析 MCP 请求里的 Bearer Token，得到用户和权限范围 |
| `runtime.py` | 统一事务、日志、异常转换、耗时统计 |
| `context.py` | MCP 调用上下文，保存当前用户、设备会话、数据库会话等运行态信息 |
| `registry.py` | MCP 工具注册表 |
| `models.py` | MCP 操作日志模型 |
| `operation_log.py` | 写操作审计和撤销记录 |
| `tools/todos.py` | 待办相关工具 |
| `tools/system.py` | 系统状态工具 |
| `tools/operations.py` | MCP 操作查询和撤销工具 |
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
articles.get_summary
articles.get_content
articles.create
articles.update_metadata
articles.patch_content
```

## 第一版工具范围

当前第一批已完成待办读写、操作日志和撤销。下一批建议补齐文章能力，支持当前用户名下所有未删除文章的读取和低风险写入，仍然保持工具偏少、偏稳定。

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
| `articles.list_mine` | `mcp_readonly` | 否 | 查询我的文章列表，只返回列表项和摘要，不返回正文 |
| `articles.get_summary` | `mcp_readonly` | 否 | 读取文章元信息、摘要、标签、分类、字数、状态和编辑时间，不返回正文 |
| `articles.get_outline` | `mcp_readonly` | 否 | 从 Markdown 正文解析标题层级和片段定位信息，默认不返回完整正文 |
| `articles.get_content` | `mcp_readonly` | 否 | 按需读取正文，可指定 `metadata`、`full`、`excerpt`、`heading` 或 `line_range` |
| `articles.create` | `mcp_full` | 是 | 创建文章，默认状态由入参决定，未指定时创建私有文章 |
| `articles.update_metadata` | `mcp_full` | 是 | 更新文章标题、摘要、封面、分类、标签、状态等元信息，不修改正文 |
| `articles.replace_content` | `mcp_full` | 是 | 替换文章完整正文，需要提供 `expected_last_edited_at` |
| `articles.patch_content` | `mcp_full` | 是 | 局部修改文章正文，需要提供定位信息和 `expected_hash` |

当前文章模型在 `articles.content` 中保存完整 Markdown 正文，`articles.excerpt` 保存摘要，`articles.last_edited_at` 表示内容编辑时间；当前还没有独立的文章版本表、正文块表或稳定的 block id。因此文章 MCP 第一版要默认少读正文，局部写入也要先基于 Markdown heading、行范围和片段 hash 做保护。

第一版支持编辑当前用户名下所有未删除文章，包括私有、草稿和已发布文章。永久删除、批量修改仍然不建议开放；文章发布如果只是状态字段更新，可以走 `articles.update_metadata`，如果后续需要发布校验、定时发布或外部通知，再单独拆成两阶段工具。

#### 文章正文读取策略

MCP 默认不应该把完整正文返回给 AI。推荐按读取范围显式选择：

| `mode` | 说明 | 返回正文 |
| --- | --- | --- |
| `metadata` | 只返回标题、slug、摘要、状态、标签、分类、字数、时间等 | 否 |
| `outline` | 返回 Markdown 标题树、标题行号、标题锚点和片段 hash | 否 |
| `excerpt` | 返回摘要字段，必要时补充正文前 N 字 | 部分 |
| `heading` | 返回某个标题下的片段 | 部分 |
| `line_range` | 返回指定行范围 | 部分 |
| `full` | 返回完整正文 | 是 |

`articles.list_mine` 固定使用 `metadata` 级别返回，避免列表工具把大量正文塞进上下文。`articles.get_summary` 也不返回 `content` 字段，只返回：

```json
{
  "id": "019...",
  "title": "文章标题",
  "slug": "article-slug",
  "excerpt": "摘要",
  "status": "private",
  "word_count": 1200,
  "category": {},
  "tags": [],
  "created_at": "...",
  "last_edited_at": "...",
  "updated_at": "..."
}
```

`articles.get_content` 读取完整正文时必须显式传：

```json
{
  "article_id": "019...",
  "mode": "full",
  "reason": "需要全局检查标题结构和前后文一致性"
}
```

服务端日志只记录读取模式、正文长度和目标文章，不记录完整正文。

#### 文章局部定位策略

不建议把“行号”作为唯一稳定定位。Markdown 编辑器会因为格式化、图片插入、换行变化导致行号漂移。

第一版可以同时支持三种定位，但写入时必须带片段 hash：

| 定位方式 | 适用场景 | 稳定性 |
| --- | --- | --- |
| `heading` | 修改某个标题下的章节 | 较好 |
| `line_range` | 用户明确指出第几行，或调试纯 Markdown | 一般 |
| `text_anchor` | 根据前后锚点和原片段查找 | 一般 |

推荐 `articles.patch_content` 入参：

```json
{
  "article_id": "019...",
  "expected_last_edited_at": "2026-06-06T10:00:00+08:00",
  "target": {
    "type": "heading",
    "heading_path": ["一级标题", "二级标题"]
  },
  "expected_hash": "sha256:...",
  "replacement": "新的 Markdown 片段"
}
```

服务端执行时必须：

- 校验文章属于当前用户
- 校验文章未删除
- 校验 `expected_last_edited_at` 等于当前 `last_edited_at`
- 根据 `target` 找到当前正文片段
- 计算当前片段 hash 并与 `expected_hash` 比对
- 不一致时拒绝写入，返回冲突错误和新的片段摘要

这样可以避免 AI 基于旧上下文覆盖用户刚修改的内容。

#### 第一版和后续版本边界

当前代码可以先做：

- 摘要读取：直接使用 `文章列表项`、`文章信息` 中已有的 `excerpt`、`word_count`、`last_edited_at`
- 大纲读取：对 `articles.content` 做 Markdown 标题解析，不需要改库表
- 完整正文读取：复用 `获取我的文章` 和 `构建文章读取响应`
- 完整正文更新：复用 `更新文章`
- 简单局部更新：服务端读取完整 Markdown，在内存中定位片段、替换后再调用 `更新文章`

后续如果要更稳地支持富文本或多人协作编辑，再新增：

- `article_revisions`：文章版本快照表
- `article_content_blocks`：正文块表，提供稳定 `block_id`
- `content_version` 或 `edit_version`：独立内容版本号，避免用时间戳做并发控制
- `articles.patch_block`：按 `block_id` 精准读写

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

`before_json` 和 `after_json` 不应该保存过大的内容。文章正文这类大字段要按工具类型区分：

- 元信息更新只保存元信息快照
- 完整正文替换可以保存正文 hash、字数、长度、前后摘要，不默认保存完整正文
- 局部正文修改可以保存被替换片段、替换后片段、片段 hash 和定位信息
- 后续新增 `article_revisions` 后，操作日志只保存 `revision_id`

如果第一版需要支持 `articles.replace_content` 的完整撤销，建议在操作日志中临时保存完整 `content` 的 before/after，并设置撤销过期时间。更稳妥的方案是先新增文章版本快照表，再开放大正文替换。

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

文章写操作支持当前用户名下所有未删除文章，不再限制为草稿或私有文章。

建议：

| 原操作 | 撤销方式 |
| --- | --- |
| `articles.create` | 软删除新建文章 |
| `articles.update_metadata` | 根据元信息快照恢复标题、摘要、封面、分类、标签、状态等字段 |
| `articles.replace_content` | 根据正文快照或文章版本恢复完整正文 |
| `articles.patch_content` | 根据局部片段快照反向替换原片段 |

删除、批量修改第一版不开放给 MCP。已发布文章允许通过普通文章写工具修改，但必须带版本或片段校验；文章发布如果只是状态字段更新，可以走 `articles.update_metadata`，复杂发布流程后续再单独设计。

当前文章没有版本快照表，所以 `articles.patch_content` 的撤销要保存足够的局部 before/after 片段和定位信息。如果后续要支持完整正文替换或长文本多轮编辑，建议先做文章版本快照表，而不是只依赖 `mcp_operation_logs.before_json`。

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
- 复杂文章发布流程
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
- `articles.list_mine` 不返回正文
- `articles.get_summary` 不返回正文
- `articles.get_content` 只有显式 `mode=full` 时才返回完整正文
- `articles.patch_content` 在 `expected_last_edited_at` 不一致时拒绝写入
- `articles.patch_content` 在 `expected_hash` 不一致时拒绝写入
- `articles.patch_content` 只允许修改当前用户的未删除文章
- 文章写工具成功后生成 operation log，且普通日志不打印完整正文

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

### 已完成基础能力

已经完成最小 MCP 接入、待办相关、MCP 调用日志、操作日志。

### 第四阶段：文章能力

目标：

- [ ] 暴露 `articles.list_mine`
- [ ] 暴露 `articles.get_summary`
- [ ] 暴露 `articles.get_outline`
- [ ] 暴露 `articles.get_content`
- [ ] 暴露 `articles.create`
- [ ] 暴露 `articles.update_metadata`
- [ ] 暴露 `articles.replace_content`
- [ ] 暴露 `articles.patch_content`
- [ ] 支持文章撤销
- [ ] 保证文章列表和摘要工具默认不返回正文
- [ ] 为局部正文写入增加 `expected_last_edited_at` 和 `expected_hash` 校验

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
- [ ] 复杂文章发布工具
- [ ] 无校验的已发布文章写入工具
- [ ] 批量删除工具
- [ ] 无版本校验的全文覆盖
- [ ] 把行号作为唯一定位的正文写入
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
- 当前已完成待办读写、操作日志和撤销
- 下一批做文章能力，默认只读摘要和局部正文
- 文章完整正文读取必须显式请求
- 文章写入支持当前用户名下所有未删除文章，且必须带版本或片段校验
- 文件和系统管理先只读或暂不开放

这样可以先把 AI 调用能力跑起来，同时保留可审计、可撤销、可收缩权限的空间。
