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

当前 MCP 能力已覆盖协议入口、Bearer Token 认证、事务运行时、工具注册分发、操作日志、撤销、待办、文章和操作查询。

后续新增 MCP 工具时应继续保持“协议适配层调用现有 service 层”的边界，不要为 MCP 另起一套业务实现。

## AI 聊天框工具调用体验

云端前端右下角的 `AIChatWidget` 当前请求 `/api/v1/ai/chat`，后端 AI 聊天服务会把 MCP 工具按 OpenAI compatible `tools/function calling` 格式暴露给模型。

当前已支持的能力：

- 聊天框可以触发待办写入。模型可调用 `todos.create`、`todos.update`、`todos.complete`、`todos.uncomplete`、`todos.delete`、`todos.restore`，工具执行后会真实写入数据库。
- 聊天框支持一次请求内的多轮工具调用。`AI工具最大轮数` 当前为 4，模型可以先查询再写入，也可以在读取工具结果后继续调用下一轮工具。
- 聊天框支持连续对话。前端会把当前聊天框里的历史消息一起发送给 `/api/v1/ai/chat`，因此用户可以继续说“把刚才那个改成明天”这类上下文相关指令。
- 写入工具会走 MCP 运行时事务和操作日志。成功后会记录 MCP 操作日志，失败会回滚事务并记录失败日志。

当前边界：

- 聊天框的连续对话只保存在前端内存中。刷新页面、关闭聊天或重置对话后，聊天上下文会丢失。
- 后端已经执行工具，但前端当前不会显示“调用了哪个工具”。SSE 目前只把助手最终文本增量传给前端，没有传 `tool_start`、`tool_result`、`tool_error` 这类工具事件。
- 工具调用结果没有作为结构化消息保存在前端历史里。前端只能保留助手最终回复文本，不能基于工具轨迹做“查看调用详情”“撤销刚才操作”等交互。
- AI 聊天内部构建的 MCP 上下文当前没有绑定设备会话，因此不会受 MCP Bearer Token 的只读或读写 scope 限制。只要模型通过聊天服务发起 `full` 权限工具调用，后端会允许执行。后续如需收紧，应为 AI 聊天单独增加“只读 / 读写”配置项。

建议补齐的可视化工具调用事件：

```text
data: {"type":"tool_start","tool_name":"todos.create","summary":"正在创建待办"}

data: {"type":"tool_result","tool_name":"todos.create","summary":"已创建待办：整理 MCP 接入方案","target":{"type":"todo","id":"..."}}

data: {"type":"tool_error","tool_name":"todos.create","summary":"创建待办失败：标题不能为空"}
```

前端对应需要扩展：

- 在 `聊天消息` 中增加工具事件或步骤数组，保存工具名、状态、参数摘要、结果摘要、目标 ID 和操作日志 ID。
- 在 `解析数据流行` 中识别结构化 SSE 事件，不再只提取 `delta/text/content`。
- 在 `MessageList` 里展示紧凑状态条，例如“调用工具：创建待办”“已完成：创建待办”“调用失败：错误信息”。
- 如需支持撤销体验，应把 MCP 写操作返回的操作日志 ID 透传给前端，并提供“撤销本次操作”的入口。

## 推荐目录结构

当前目录已经存在大部分 MCP 基础文件，后续建议补齐文件和更多业务模块工具：

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

| 文件                  | 职责                                                           |
| --------------------- | -------------------------------------------------------------- |
| `server.py`           | 创建 MCP Server、注册工具、导出 ASGI app                       |
| `auth.py`             | 解析 MCP 请求里的 Bearer Token，得到用户和权限范围             |
| `runtime.py`          | 统一事务、日志、异常转换、耗时统计                             |
| `context.py`          | MCP 调用上下文，保存当前用户、设备会话、数据库会话等运行态信息 |
| `registry.py`         | MCP 工具注册表                                                 |
| `models.py`           | MCP 操作日志模型                                               |
| `operation_log.py`    | 写操作审计和撤销记录                                           |
| `tools/todos.py`      | 待办相关工具                                                   |
| `tools/system.py`     | 系统状态工具                                                   |
| `tools/operations.py` | MCP 操作查询和撤销工具                                         |
| `tools/articles.py`   | 文章相关工具                                                   |
| `tools/files.py`      | 文件相关工具                                                   |

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

| 范围           | 说明                     |
| -------------- | ------------------------ |
| `mcp_readonly` | 只允许调用读取类工具     |
| `mcp_full`     | 允许调用读取和写入类工具 |

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

第一版工具范围以待办、文章、操作日志和撤销为核心，后续新增模块仍然保持工具偏少、偏稳定，不把所有 HTTP API 原样暴露给 AI。

### 待办工具

建议提供：

| 工具               | 权限           | 是否可撤销 | 说明             |
| ------------------ | -------------- | ---------- | ---------------- |
| `todos.list`       | `mcp_readonly` | 否         | 查询当前用户待办 |
| `todos.get`        | `mcp_readonly` | 否         | 读取待办详情     |
| `todos.create`     | `mcp_full`     | 是         | 创建待办         |
| `todos.update`     | `mcp_full`     | 是         | 更新待办         |
| `todos.complete`   | `mcp_full`     | 是         | 完成待办         |
| `todos.uncomplete` | `mcp_full`     | 是         | 撤销完成         |
| `todos.delete`     | `mcp_full`     | 是         | 移入回收站       |
| `todos.restore`    | `mcp_full`     | 是         | 从回收站恢复     |

### 文章工具

建议提供：

| 工具                       | 权限           | 是否可撤销 | 说明                                                                          |
| -------------------------- | -------------- | ---------- | ----------------------------------------------------------------------------- |
| `articles.list_mine`       | `mcp_readonly` | 否         | 查询我的文章列表，只返回列表项和摘要，不返回正文                              |
| `articles.get_summary`     | `mcp_readonly` | 否         | 读取文章元信息、摘要、标签、分类、字数、状态和编辑时间，不返回正文            |
| `articles.get_outline`     | `mcp_readonly` | 否         | 从 Markdown 正文解析标题层级和片段定位信息，默认不返回完整正文                |
| `articles.get_content`     | `mcp_readonly` | 否         | 按需读取正文，可指定 `metadata`、`full`、`excerpt`、`heading` 或 `line_range` |
| `articles.create`          | `mcp_full`     | 是         | 创建文章，默认状态由入参决定，未指定时创建私有文章                            |
| `articles.update_metadata` | `mcp_full`     | 是         | 更新文章标题、摘要、封面、分类、标签、状态等元信息，不修改正文                |
| `articles.replace_content` | `mcp_full`     | 是         | 替换文章完整正文，需要提供 `expected_last_edited_at`                          |
| `articles.patch_content`   | `mcp_full`     | 是         | 局部修改文章正文，需要提供定位信息和 `expected_hash`                          |

当前文章模型在 `articles.content` 中保存完整 Markdown 正文，`articles.excerpt` 保存摘要，`articles.last_edited_at` 表示内容编辑时间；当前还没有独立的文章版本表、正文块表或稳定的 block id。因此文章 MCP 第一版要默认少读正文，局部写入也要先基于 Markdown heading、行范围和片段 hash 做保护。

第一版支持编辑当前用户名下所有未删除文章，包括私有、草稿和已发布文章。永久删除、批量修改仍然不建议开放；文章发布如果只是状态字段更新，可以走 `articles.update_metadata`，如果后续需要发布校验、定时发布或外部通知，再单独拆成两阶段工具。

#### 文章正文读取策略

MCP 默认不应该把完整正文返回给 AI。推荐按读取范围显式选择：

| `mode`       | 说明                                                   | 返回正文 |
| ------------ | ------------------------------------------------------ | -------- |
| `metadata`   | 只返回标题、slug、摘要、状态、标签、分类、字数、时间等 | 否       |
| `outline`    | 返回 Markdown 标题树、标题行号、标题锚点和片段 hash    | 否       |
| `excerpt`    | 返回摘要字段，必要时补充正文前 N 字                    | 部分     |
| `heading`    | 返回某个标题下的片段                                   | 部分     |
| `line_range` | 返回指定行范围                                         | 部分     |
| `full`       | 返回完整正文                                           | 是       |

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

| 定位方式      | 适用场景                              | 稳定性 |
| ------------- | ------------------------------------- | ------ |
| `heading`     | 修改某个标题下的章节                  | 较好   |
| `line_range`  | 用户明确指出第几行，或调试纯 Markdown | 一般   |
| `text_anchor` | 根据前后锚点和原片段查找              | 一般   |

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

文件 MCP 的边界建议区分“全部资源只读”和“普通文件写入”。云端资源管理器当前会把普通文件、文章图片、动态图片和文娱资源统一展示给用户，但这些资源的生命周期并不相同：

- 普通文件属于文件模块，可以移动、重命名、软删除和恢复。
- 文章图片归属于文章编辑器，删除和上传应由文章图片能力管理。
- 动态图片归属于动态编辑器，删除和上传应由动态图片能力管理。
- 文娱资源归属于文娱模块，封面、资源文件和外部来源不应通过普通文件工具写入。

第一版建议提供：

| 工具                  | 权限           | 是否可撤销 | 说明                                                                 |
| --------------------- | -------------- | ---------- | -------------------------------------------------------------------- |
| `files.explorer`      | `mcp_readonly` | 否         | 读取目录树、当前目录文件夹和文件；根目录可返回文章图片、动态图片和文娱资源 |
| `files.search`        | `mcp_readonly` | 否         | 跨普通文件、文件夹、文章图片、动态图片和文娱资源搜索                 |
| `files.get_metadata`  | `mcp_readonly` | 否         | 读取单个文件或文件夹元信息、路径、大小、MIME 和所属业务对象          |
| `files.trash_list`    | `mcp_readonly` | 否         | 查看普通文件和普通文件夹回收站                                       |
| `files.folder_create` | `mcp_full`     | 是         | 创建普通文件夹                                                       |
| `files.folder_rename` | `mcp_full`     | 是         | 重命名普通文件夹                                                     |
| `files.folder_move`   | `mcp_full`     | 是         | 移动普通文件夹                                                       |
| `files.folder_delete` | `mcp_full`     | 是         | 将普通文件夹移入回收站                                               |
| `files.folder_restore` | `mcp_full`     | 是         | 从回收站恢复普通文件夹                                               |
| `files.rename`        | `mcp_full`     | 是         | 重命名普通文件；文章图片、动态图片和文娱资源默认不通过该工具写       |
| `files.move`          | `mcp_full`     | 是         | 移动普通文件到目标普通文件夹                                         |
| `files.delete`        | `mcp_full`     | 是         | 将普通文件移入回收站，不做永久删除                                   |
| `files.restore`       | `mcp_full`     | 是         | 从回收站恢复普通文件                                                 |

文件工具返回的资源项建议显式带 `purpose`：

| `purpose`       | 说明     | MCP 写入策略                           |
| --------------- | -------- | -------------------------------------- |
| `file`          | 普通文件 | 允许移动、重命名、软删除和恢复         |
| `article_image` | 文章图片 | 只读展示和搜索；写操作交给文章图片能力 |
| `moment_image`  | 动态图片 | 只读展示和搜索；写操作交给动态图片能力 |
| `media_asset`   | 文娱资源 | 只读展示和搜索；写操作交给文娱资源能力 |

`files.explorer` 和 `files.search` 可以覆盖所有资源类型，用于让 AI 找到“这张图来自哪篇文章”“哪个文娱条目用了这个资源”等上下文。`files.move`、`files.delete`、`files.restore` 只处理 `purpose=file` 的普通文件，避免 AI 绕过文章、动态、文娱模块的业务约束。

上传、覆盖、按 URL 导入、对象存储永久删除和批量整理暂不放进第一版。后续如果要支持上传，建议优先做“创建预签名上传任务”或 `files.import_from_url`，不要让 MCP 通过 JSON 直接传大文件内容。

## 更多模块接入建议

除了待办和文章，后续可以按“只读优先、低风险写入其次、外部副作用最后”的顺序扩展 MCP 工具。新增模块前不建议只看 service 是否存在，还要看模块是否具备软删除、恢复、撤销快照、并发校验和日志脱敏能力。

### 推荐接入顺序

| 优先级 | 模块 | 建议范围 | 原因 |
| ------ | ---- | -------- | ---- |
| 1 | `stats` 统计 | 只读 | 只读查询风险最低，适合作为更多工具的练手机制 |
| 2 | `memos` 备忘录 | 读写 | 已有 `deleted_at`、恢复和状态流转，单条文本写入撤销成本较低 |
| 3 | `collections` 收藏/资料库 | 读写 | 已有软删除、恢复、标签和附件关系，适合暴露资料整理能力 |
| 4 | `files` 文件 | 全资源只读 + 普通文件低风险写入 | 资源管理器适合让 AI 检索上下文；写入只开放普通文件和普通文件夹，文章图片、动态图片、文娱资源保持只读 |
| 5 | `media` 文娱 | 只读 + 低风险元信息写入 | 已有软删除和恢复，但资源、封面、外部来源和对象存储要谨慎 |
| 6 | `moments` 动态 | 读写当前用户未删除动态 | 不再限制为草稿；动态文本较短，可以用普通更新工具承接标题、正文和发布状态 |
| 7 | `bills` 账单 | 只读优先 | 账务数据误操作成本高，写入必须先补确认、撤销和审计策略 |

### 备忘录工具

备忘录适合作为后续写工具。建议提供：

| 工具 | 权限 | 是否可撤销 | 说明 |
| ---- | ---- | ---------- | ---- |
| `memos.list` | `mcp_readonly` | 否 | 查询当前用户备忘录，可按状态、来源、关键词筛选 |
| `memos.get` | `mcp_readonly` | 否 | 读取单条备忘录详情 |
| `memos.create` | `mcp_full` | 是 | 创建备忘录 |
| `memos.update` | `mcp_full` | 是 | 更新正文、状态或来源 |
| `memos.delete` | `mcp_full` | 是 | 标记为废弃或移入回收站语义 |
| `memos.restore` | `mcp_full` | 是 | 从已删除状态恢复 |

备忘录已有转换为文章、收藏、待办的 service，但转换类工具第一版建议先不开放。转换会跨模块创建新对象并修改原备忘录状态，撤销时需要同时处理目标对象和原备忘录快照，建议等单模块写入稳定后再加。

### 收藏工具

收藏/资料库适合让 AI 辅助整理资料、打标签和归档。建议第一版提供：

| 工具 | 权限 | 是否可撤销 | 说明 |
| ---- | ---- | ---------- | ---- |
| `collections.list` | `mcp_readonly` | 否 | 查询收藏列表，不默认返回过大的附件详情 |
| `collections.get` | `mcp_readonly` | 否 | 读取单条收藏详情 |
| `collections.create` | `mcp_full` | 是 | 创建文本或链接收藏 |
| `collections.update` | `mcp_full` | 是 | 更新标题、正文、备注、状态、标签 |
| `collections.delete` | `mcp_full` | 是 | 软删除收藏 |
| `collections.restore` | `mcp_full` | 是 | 从回收站恢复收藏 |

收藏的附件关系要单独做快照，至少记录附件文件 ID、排序和标签关系。批量更新收藏状态属于高风险操作，必须走 `dry_run -> confirm`，不建议第一版直接暴露给 AI。

### 统计工具

统计工具建议只读，返回结构化数字和时间范围，避免把内部 SQL 或缓存键暴露给 AI。

建议工具：

| 工具 | 权限 | 是否可撤销 | 说明 |
| ---- | ---- | ---------- | ---- |
| `stats.blog_overview` | `mcp_readonly` | 否 | 读取博客概览统计 |
| `stats.content_overview` | `mcp_readonly` | 否 | 汇总文章、动态、收藏等内容数量 |
| `stats.activity_trend` | `mcp_readonly` | 否 | 按时间范围读取活动趋势 |

### 文娱工具

文娱模块已有软删除和恢复，但资源、封面、外部来源和对象存储会放大撤销成本。第一版建议只开放列表、详情、低风险元信息更新、软删除和恢复。

可先提供：

| 工具 | 权限 | 是否可撤销 | 说明 |
| ---- | ---- | ---------- | ---- |
| `media.list` | `mcp_readonly` | 否 | 查询当前用户文娱条目 |
| `media.facets` | `mcp_readonly` | 否 | 聚合读取类型、子分类、标签、个人标签和创作者统计 |
| `media.get` | `mcp_readonly` | 否 | 读取文娱条目详情 |
| `media.create` | `mcp_full` | 是 | 手动创建文娱条目，不绑定封面资源，撤销时软删除新建条目 |
| `media.update_metadata` | `mcp_full` | 是 | 更新标题、状态、评分、简介、标签、公开可见性等元信息 |
| `media.delete` | `mcp_full` | 是 | 将文娱条目移入回收站，只执行软删除 |
| `media.restore` | `mcp_full` | 是 | 从回收站恢复文娱条目 |

暂不开放资源上传、封面覆盖、外部封面下载、永久删除。永久删除会删除对象存储资源，必须单独设计对象回收站或版本保留。

### 动态工具

动态模块涉及公开展示、Feed 同步、缓存刷新、图片资源和互动计数。第一版支持读取和编辑当前用户名下所有未删除动态，包括草稿和已发布动态，不再限制为草稿保存。动态不像文章那样有长 Markdown、摘要、分类和局部正文定位，第一版不需要拆成元信息更新和正文替换；用一个普通更新工具承接标题、正文和发布状态即可。动态写入必须带 `expected_last_edited_at` 或等价版本校验，并在操作日志中保存足够恢复标题、正文、发布状态和时间字段的快照。

可先提供：

| 工具 | 权限 | 是否可撤销 | 说明 |
| ---- | ---- | ---------- | ---- |
| `moments.list_mine` | `mcp_readonly` | 否 | 查询我的动态列表 |
| `moments.get` | `mcp_readonly` | 否 | 读取动态详情 |
| `moments.create` | `mcp_full` | 是 | 创建动态，默认状态由入参决定，未指定时创建未发布动态 |
| `moments.update` | `mcp_full` | 是 | 更新动态标题、正文、发布状态等普通字段，需要提供 `expected_last_edited_at` |
| `moments.delete` | `mcp_full` | 是 | 软删除动态，不做永久删除 |
| `moments.restore` | `mcp_full` | 是 | 从回收站恢复动态 |

图片上传、排序和删除仍然单独作为图片工具设计，不塞进 `moments.update`。永久删除、批量修改和复杂发布流程仍然后置。动态发布如果只是状态字段更新，可以走 `moments.update`；如果后续需要发布校验、定时发布、外部通知或复杂 Feed 编排，再单独拆成两阶段工具。已发布动态允许通过普通动态写工具修改，但必须带版本校验，并明确同步 Feed、清缓存和发布前快照策略。

### 账单工具

账单属于高敏感数据。第一版只建议开放只读查询，例如账户、分类、月度收支和单条记录详情。写入账单、删除账单、修改账户余额都必须先补足确认和撤销策略。

写入账单前至少需要：

- 预览影响范围，包括账户、分类、金额、时间和统计影响
- 明确金额正负和币种/账户语义
- 操作日志保存完整 before/after 快照
- 撤销时能恢复账户、记录和关联统计的一致性
- 前端或聊天框展示待确认摘要，避免模型直接落库

## 新模块写工具接入门槛

新增任何 `mcp_full` 写工具前，必须先满足以下条件。满足不了时，该模块只能开放只读工具。

| 条件 | 要求 |
| ---- | ---- |
| 软删除/恢复 | 删除类工具必须默认软删除，并提供恢复能力；没有软删除的模块不开放 `delete` |
| 服务端撤销 | 每个写工具都要在 `operations.undo` 中有服务端定义的撤销处理器 |
| 操作快照 | 写入前后要保存足够恢复的字段快照，避免只保存自然语言摘要 |
| 并发保护 | 更新类工具建议带 `expected_updated_at`、`expected_last_edited_at`、版本号或内容 hash |
| 权限校验 | 必须校验目标对象属于当前用户，不能只依赖前端传参 |
| 日志脱敏 | 普通日志不能打印 token、完整正文、文件内容、敏感配置或大字段 |
| 事务边界 | 单次工具调用保持单事务；外部副作用要先设计补偿或延后执行 |
| 测试覆盖 | 覆盖 readonly 禁写、full 可写、rollback、operation log、撤销、重复撤销和越权 |

### 删除能力默认策略

MCP 中的删除不等同于普通后台里的永久删除。默认策略如下：

- `*.delete` 表示软删除或移入回收站。
- `*.restore` 表示从软删除状态恢复。
- `*.permanent_delete` 默认不提供。
- 已有永久删除 service 的模块，也不直接暴露给 MCP。
- 需要永久删除时，必须单独走高风险两阶段确认，并记录不可撤销说明。

如果某个模块还没有软删除字段，建议先给业务模型补齐 `is_deleted`/`deleted_at` 或等价状态，再考虑 MCP 写入。不要为了 MCP 临时硬删数据，也不要让 AI 通过更新状态字段模拟删除。

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

| 字段                     | 说明                                 |
| ------------------------ | ------------------------------------ |
| `user_id`                | 操作所属用户                         |
| `device_session_id`      | 调用来源设备会话                     |
| `tool_name`              | MCP 工具名                           |
| `status`                 | `success`、`failed`、`undone`        |
| `target_type`            | 业务对象类型，例如 `todo`、`article` |
| `target_id`              | 业务对象 ID                          |
| `args_json`              | 工具输入摘要                         |
| `before_json`            | 写入前快照                           |
| `after_json`             | 写入后快照                           |
| `result_json`            | 返回结果摘要                         |
| `error_message`          | 失败原因                             |
| `duration_ms`            | 调用耗时                             |
| `is_undoable`            | 是否允许撤销                         |
| `undo_tool_name`         | 对应撤销处理器                       |
| `undoable_until`         | 撤销截止时间                         |
| `undone_at`              | 实际撤销时间                         |
| `undone_by_operation_id` | 哪次撤销操作执行了回滚               |

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

| 工具                     | 权限           | 说明                |
| ------------------------ | -------------- | ------------------- |
| `operations.list_recent` | `mcp_readonly` | 查看最近 MCP 写操作 |
| `operations.get`         | `mcp_readonly` | 查看某次操作详情    |
| `operations.undo`        | `mcp_full`     | 撤销一次可撤销操作  |

`operations.undo` 只接收 `operation_id`，不接收任意 SQL 或任意反向参数。

## 各模块撤销策略

### 待办

待办最适合作为第一批可撤销工具。

建议：

| 原操作             | 撤销方式                          |
| ------------------ | --------------------------------- |
| `todos.create`     | 软删除新建的待办，必要时可硬删    |
| `todos.update`     | 根据 `before_json` 恢复字段和标签 |
| `todos.complete`   | 调用现有取消完成逻辑              |
| `todos.uncomplete` | 根据完成事件重新补一条完成记录    |

待办已经有软删除、完成事件和重复任务状态逻辑，所以撤销成本较低。

### 文章

文章写操作支持当前用户名下所有未删除文章，不再限制为草稿或私有文章。

建议：

| 原操作                     | 撤销方式                                                   |
| -------------------------- | ---------------------------------------------------------- |
| `articles.create`          | 软删除新建文章                                             |
| `articles.update_metadata` | 根据元信息快照恢复标题、摘要、封面、分类、标签、状态等字段 |
| `articles.replace_content` | 根据正文快照或文章版本恢复完整正文                         |
| `articles.patch_content`   | 根据局部片段快照反向替换原片段                             |

删除、批量修改第一版不开放给 MCP。已发布文章允许通过普通文章写工具修改，但必须带版本或片段校验；文章发布如果只是状态字段更新，可以走 `articles.update_metadata`，复杂发布流程后续再单独设计。

当前文章没有版本快照表，所以 `articles.patch_content` 的撤销要保存足够的局部 before/after 片段和定位信息。如果后续要支持完整正文替换或长文本多轮编辑，建议先做文章版本快照表，而不是只依赖 `mcp_operation_logs.before_json`。

### 文件

文件第一版采用“全资源只读 + 普通文件低风险写入”。只读工具可以返回普通文件、文章图片、动态图片和文娱资源；写工具只处理 `purpose=file` 的普通文件和普通文件夹。

建议：

| 原操作                  | 撤销方式                                                 |
| ----------------------- | -------------------------------------------------------- |
| `files.folder_create`   | 将新建文件夹移入回收站                                   |
| `files.folder_rename`   | 根据 `before_json` 恢复文件夹名称                        |
| `files.folder_move`     | 根据 `before_json` 恢复文件夹父级                        |
| `files.folder_delete`   | 从回收站恢复文件夹子树                                   |
| `files.folder_restore`  | 重新将文件夹子树移入回收站                               |
| `files.rename`          | 根据 `before_json` 恢复普通文件名                        |
| `files.move`            | 根据 `before_json` 恢复普通文件所在文件夹                |
| `files.delete`          | 从回收站恢复普通文件                                     |
| `files.restore`         | 重新将普通文件移入回收站                                 |

文件写工具必须保存足够的 before/after 快照，包括目标 ID、名称、父级目录、路径、`updated_at`、删除状态和清理时间。更新和移动类工具建议带 `expected_updated_at`，避免 AI 基于旧目录结构覆盖用户刚做的整理。

第一版仍不开放以下能力：

- 上传后的孤儿文件清理
- 删除前对象存储回收站
- 覆盖前版本保留
- MinIO 对象和数据库记录一致性

这些能力涉及对象存储副作用和二进制内容版本，后续需要单独设计。永久删除必须保持不暴露，上传和覆盖也不建议和普通整理工具一起开放。

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
- 复杂动态发布流程
- 文娱资源上传、封面覆盖和外部资源抓取
- 账单写入、删除和账户余额相关修改
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

## 后续计划

目标：

- [ ] 补齐 `memos` 读写工具，覆盖创建、更新、软删除、恢复和撤销
- [ ] 补齐 `collections` 读写工具，覆盖标签、附件关系快照、软删除、恢复和撤销
- [x] 补齐 `files` 工具，全资源只读，普通文件和普通文件夹支持低风险写入、软删除、恢复和撤销
- [x] 评估 `media` 元信息工具，先只开放只读和低风险元信息更新
- [x] 补齐 `moments` 读写工具，覆盖当前用户未删除动态的创建、普通更新、软删除、恢复和撤销
- [ ] 账单模块先只做只读调研，不开放写入
- [ ] 把新模块写工具接入门槛整理成测试模板，新增模块时复用

## 暂不做事项

第一版暂不做：

- [ ] OAuth 授权服务器
- [ ] 多租户 MCP 网关
- [ ] 通用 SQL 执行工具
- [ ] 任意文件写入工具
- [ ] 系统管理工具
- [ ] 复杂文章发布工具
- [ ] 复杂动态发布工具
- [ ] 文娱资源上传、封面覆盖和外部抓取工具
- [ ] 账单写入和删除工具
- [ ] 无校验的已发布文章写入工具
- [ ] 批量删除工具
- [ ] 永久删除工具
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
- 文章完整正文读取必须显式请求
- 文章写入支持当前用户名下所有未删除文章，且必须带版本或片段校验
- 下一批优先做 `stats` 只读、`memos` 读写、`collections` 读写
- 文件、文娱、账单按风险分层逐步开放，默认先只读；动态与文章一致，支持当前用户名下所有未删除内容写入
- 删除工具默认只做软删除，永久删除默认不暴露
- 新模块写工具必须先补齐软删除/恢复、撤销处理器、快照、并发保护、日志脱敏和测试

这样可以先把 AI 调用能力跑起来，同时保留可审计、可撤销、可收缩权限的空间。
