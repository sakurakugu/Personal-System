# AI 与 MCP 工具接入规划

## 背景

后续希望让 AI 可以远程辅助操作个人系统，例如：

- 查询待办
- 新增待办
- 修改待办
- 完成待办
- 将待办移动到回收站
- 从回收站恢复待办

同时需要明确禁止高风险能力，例如：

- 永久删除待办
- 删除账号
- 清空数据
- 删除对象存储文件
- 执行任意 SQL
- 执行任意 Shell 命令

这类能力不应该直接暴露给 AI。AI 只能调用系统明确注册过的安全工具，不能拿完整用户登录态访问全部业务 API。

## 核心原则

AI 接入层的定位是“受限工具网关”，不是“远程管理员”。

原则如下：

- AI 不直接访问数据库
- AI 不直接复用浏览器 Session 或手机设备令牌
- AI 不直接调用完整业务 API
- AI 只能调用工具注册表中显式注册的工具
- 工具参数必须使用明确的 Schema 校验
- 工具执行前必须校验 AI Token、scope、风险等级
- 所有 AI 工具调用必须记录审计日志
- 永久删除、清空、账号删除、任意 SQL、任意 Shell 永远不进入工具注册表

## 推进顺序

AI 工具和 MCP 不应该先做协议接入，再回头补业务安全。推荐顺序是：

```text
盘点模块能力和风险
  -> 补齐业务模块自己的数据保护能力
  -> 设计 AI 工具清单
  -> 实现后端 AI 工具网关
  -> 实现本地 MCP 薄代理
  -> 评估是否开放远程 MCP
```

原因是 MCP 只是工具协议，不能替业务模块保证数据安全。如果某个模块本身没有回收站、版本历史、局部更新、审计日志，AI 工具层只能选择不开放对应写入能力，或者先把这些基础能力补齐。

## 业务安全前置改造

设计 AI 工具清单前，需要先逐个模块确认业务 API 是否适合被自动化调用。

### 没有回收站的模块

没有回收站或可恢复状态的模块，不能直接向 AI 开放删除能力。

处理策略：

- 如果业务上需要删除，先补软删除字段，例如 `is_deleted`、`deleted_at`
- 如果业务上不适合叫删除，补归档状态，例如 `archived_at`、`status=archived`
- 如果只是临时隐藏，补可见性状态，例如 `is_visible`
- 如果涉及附件或对象存储，不允许 AI 删除底层对象，只允许解除业务引用或移动到回收站
- 如果短期不补回收站，则 AI 工具清单中只开放查询、新增、修改，不开放删除

### 没有版本历史的长文本模块

文章、动态正文、收藏正文这类长文本内容，不能只依赖“整段覆盖更新”。

建议先补：

- 内容版本表或编辑快照
- 修改前后的 diff 摘要
- 最近版本恢复能力
- 乐观锁字段，例如 `updated_at` 或 `revision`
- 更新失败时提示内容已被其他操作修改

没有版本历史前，AI 只能创建草稿或追加备注，不应该直接覆盖正式正文。

### 没有局部更新能力的模块

如果模块只支持整对象更新，AI 很容易误改无关字段。需要优先补局部更新语义。

建议支持：

- 字段级 PATCH
- 标签增删工具，而不是一次性覆盖全部标签
- 状态切换工具，例如归档、发布、取消发布
- 长文本局部修改工具，例如按片段、标题、块 ID 或上下文替换
- dry-run 预览，返回将要修改的字段和差异

AI 工具应该优先设计成小动作，而不是“传一个完整对象让 AI 覆盖”。

### 文章管理的修改方式

文章模块需要区分草稿编辑和正式发布内容修改。

建议工具分层：

```text
articles.create_draft
articles.append_to_draft
articles.replace_draft_section
articles.update_draft_metadata
articles.preview_draft_diff
articles.publish_draft
articles.create_revision
articles.restore_revision
```

不建议初期开放：

```text
articles.overwrite_body
articles.replace_published_body
articles.bulk_publish
articles.permanent_delete
```

如果确实要支持“修改中间部分”，建议不要让 AI 直接提交完整正文，而是提供结构化局部修改：

```text
按标题替换某一节
按 block_id 替换某一块
按唯一上下文片段替换
向某个标题后追加内容
返回 diff，确认后应用
```

这样可以让 AI 精确修改中间部分，同时避免把整篇文章改乱。

### 写入工具的通用保护

所有写入工具都应尽量具备：

- 输入 Schema 严格校验
- 只允许白名单字段
- 默认 dry-run 或返回 diff
- 中高风险动作需要确认
- 乐观锁校验
- 审计日志
- 失败后能定位原因
- 可恢复或可撤销

如果某个动作做不到可恢复，就不应该开放给 AI 自动执行。

## 推荐架构

在后端新增通用 AI 工具模块：

```text
apps/cloud/backend/app/modules/ai_tools/
  api.py              # 普通 HTTP 工具调用入口，给自家前端、自动化脚本或外部 Agent 使用
  mcp.py              # MCP 协议适配层，只负责 tools/list 和 tools/call
  auth.py             # AI Token 鉴权、scope 校验
  registry.py         # 工具注册表
  policy.py           # 风险等级、禁止动作、确认策略
  audit.py            # 调用审计日志
  schemas.py          # 通用请求、响应、错误结构
  tools/
    todos.py          # 待办工具
    moments.py        # 动态工具
    articles.py       # 文章工具
    bills.py          # 账单工具
    files.py          # 文件工具
    collections.py    # 收藏收纳库工具
```

整体调用链：

```text
AI 客户端
  -> MCP Server 或 HTTP AI 工具入口
  -> AI Token 鉴权
  -> 工具注册表
  -> 风险策略校验
  -> 模块工具适配器
  -> 现有业务 service
  -> 审计日志
```

MCP 只作为协议适配层。业务安全边界必须落在后端 `ai_tools` 模块内，不能落在某个 MCP 客户端配置里。

## AI Token 与权限

AI Token 应独立建表，不复用现有网页登录态。

建议新增表：

```text
ai_tool_tokens
  id
  user_id
  name
  token_hash
  scopes
  expires_at
  revoked_at
  created_at
  last_used_at
```

建议新增审计表：

```text
ai_tool_invocations
  id
  user_id
  token_id
  tool_name
  input_json
  output_summary
  status
  risk_level
  error_message
  created_at
```

scope 示例：

```text
todos:read
todos:create
todos:update
todos:complete
todos:soft_delete
todos:restore
moments:create
moments:update
moments:soft_delete
articles:create_draft
articles:update_draft
bills:create
bills:update
files:read
collections:create
collections:update
```

禁止出现：

```text
todos:permanent_delete
moments:permanent_delete
articles:permanent_delete
users:delete
storage:delete
admin:*
sql:execute
shell:run
```

## 工具注册方式

每个业务模块只负责注册自己的 AI 工具，不直接关心 MCP 协议。

示例：

```python
注册工具(
    name="todos.soft_delete",
    scope="todos:soft_delete",
    risk="medium",
    confirm_required=True,
    input_schema=TodoSoftDeleteInput,
    handler=软删除待办,
)
```

工具注册信息至少包含：

```text
name
description
scope
risk
confirm_required
input_schema
output_schema
handler
```

风险等级建议：

```text
low       查询、新建草稿、添加普通记录
medium    修改数据、完成待办、软删除、批量少量操作
high      批量修改、跨模块转换、公开发布、覆盖正文
blocked   永久删除、清空、删除账号、任意 SQL、任意 Shell
```

## 待办工具设计

当前待办后端已有普通删除和永久删除能力：

- `DELETE /todos/{todo_id}?permanent=false`：移动到回收站
- `DELETE /todos/{todo_id}?permanent=true`：永久删除

AI 工具层不能直接暴露这个参数，必须拆成安全工具。

允许注册：

```text
todos.list
todos.get
todos.create
todos.update
todos.complete
todos.uncomplete
todos.soft_delete
todos.restore
```

禁止注册：

```text
todos.permanent_delete
todos.empty_trash
```

`todos.soft_delete` 内部固定调用：

```python
await delete_todo_service(db, user, todo_id, permanent=False)
```

不允许工具输入中出现：

```text
permanent
force
hard_delete
```

## 其他模块扩展方式

AI 工具能力按模块逐步开放，不一次性暴露所有后台能力。

每个模块设计工具清单前，需要先写清楚：

- 现有业务 API 是否支持软删除或恢复
- 是否需要先补回收站、归档、版本历史或审计
- 哪些字段允许 AI 改
- 哪些字段只能人工改
- 哪些动作需要 dry-run
- 哪些动作需要确认
- 哪些动作永远禁止
- 工具是否支持幂等或重复调用保护

### 动态

建议允许：

```text
moments.list_own
moments.create_draft
moments.publish
moments.update
moments.soft_delete
moments.restore
```

建议禁止：

```text
moments.permanent_delete
moments.delete_image_permanent
```

### 文章

建议允许：

```text
articles.list_own
articles.create_draft
articles.update_draft
articles.append_to_draft
articles.replace_draft_section
articles.preview_draft_diff
articles.publish
articles.unpublish
articles.soft_delete
articles.restore
articles.create_revision
articles.restore_revision
```

建议禁止：

```text
articles.permanent_delete
articles.bulk_publish
articles.overwrite_body
articles.replace_published_body
```

### 账单

建议允许：

```text
bills.list
bills.create
bills.update
bills.mark_paid
```

建议禁止：

```text
bills.permanent_delete
bills.bulk_delete
```

### 文件

文件模块风险较高，初期只开放只读和低风险整理能力。

建议允许：

```text
files.search
files.list
files.create_folder
files.rename
```

建议禁止：

```text
files.delete
files.permanent_delete
files.delete_storage_object
files.move_outside_user_scope
```

### 收藏收纳库

建议允许：

```text
collections.list
collections.create
collections.update
collections.archive
collections.convert_to_todo
collections.convert_to_article_draft
collections.convert_to_moment_draft
```

建议禁止：

```text
collections.permanent_delete
collections.bulk_delete
```

## MCP 接入方式

MCP 建议分两阶段接入。

### 第一阶段：本地 MCP Server

本地 MCP Server 作为薄代理运行：

```text
Claude Desktop / Cursor / Codex
  -> 本地 MCP Server
  -> 后端 /ai/tools/call
  -> ai_tools 注册表
```

优点：

- 容易调试
- 不需要立即公开远程 MCP 入口
- 权限和审计仍然由后端统一负责
- 不同 AI 客户端可以共用同一套后端工具层

### 第二阶段：远程 MCP Server

后端直接提供 MCP HTTP 入口：

```text
POST /mcp
Authorization: Bearer <AI_TOOL_TOKEN>
```

远程 MCP 必须满足：

- 只允许 HTTPS
- 必须使用 Bearer Token
- 必须校验 token 是否绑定当前服务
- 必须校验 scope
- 必须限流
- 必须记录审计日志
- 高风险工具必须支持确认机制

## 确认机制

建议工具支持三种执行模式：

```text
dry_run   只返回将要做什么，不真正写入
confirm   创建待确认操作，等待用户确认
execute   直接执行低风险动作
```

需要确认的操作示例：

- 批量软删除
- 批量修改标签
- 发布文章
- 发布动态
- 大段覆盖正文
- 跨模块转换并自动发布

永远不能通过确认放开的操作：

- 永久删除
- 清空回收站
- 删除账号
- 删除对象存储文件
- 执行任意 SQL
- 执行任意 Shell

## 日志与排查

AI 工具调用必须记录结构化日志，方便排查：

```text
工具名
用户 ID
token ID
scope
风险等级
输入参数摘要
输出摘要
执行耗时
成功或失败
错误信息
```

日志中不要记录完整 token、密码、密钥、Cookie。

## 实施清单

1. 

- [ ] 盘点所有模块现有删除能力，标记是否支持回收站或恢复
- [ ] 盘点所有模块现有更新能力，标记是否存在整对象覆盖风险
- [ ] 盘点所有长文本模块，标记是否支持版本历史和恢复
- [ ] 盘点所有附件相关模块，标记是否会删除对象存储文件
- [ ] 为缺少回收站但需要删除能力的模块补软删除或归档能力
- [ ] 为文章、动态、收藏正文等长文本模块补版本历史或编辑快照
- [ ] 为文章模块设计局部修改能力，例如按标题、块 ID 或上下文替换
- [ ] 为长文本修改增加 diff 预览能力
- [ ] 为写入接口增加乐观锁或版本号校验
- [ ] 为高风险业务动作补人工确认流程

2. 


- [ ] 新增 `apps/cloud/backend/app/modules/ai_tools/` 后端模块
- [ ] 新增 AI Token 数据模型和迁移文件
- [ ] 新增 AI 工具调用审计日志数据模型和迁移文件
- [ ] 实现 AI Token 创建、撤销、过期、hash 校验
- [ ] 实现 scope 校验逻辑
- [ ] 实现工具注册表 `registry.py`
- [ ] 实现风险策略 `policy.py`
- [ ] 实现统一工具调用入口 `/ai/tools/call`
- [ ] 实现工具列表入口 `/ai/tools`
- [ ] 实现审计日志写入逻辑
- [ ] 为待办模块注册 `todos.list`
- [ ] 为待办模块注册 `todos.get`
- [ ] 为待办模块注册 `todos.create`
- [ ] 为待办模块注册 `todos.update`
- [ ] 为待办模块注册 `todos.complete`
- [ ] 为待办模块注册 `todos.uncomplete`
- [ ] 为待办模块注册 `todos.soft_delete`
- [ ] 为待办模块注册 `todos.restore`
- [ ] 确认待办工具层不暴露 `permanent`、`force`、`hard_delete`
- [ ] 在工具策略中硬拒绝 `todos.permanent_delete`
- [ ] 为动态模块设计 AI 工具清单
- [ ] 为文章模块设计 AI 工具清单
- [ ] 为账单模块设计 AI 工具清单
- [ ] 为文件模块设计 AI 工具清单
- [ ] 为收藏收纳库模块设计 AI 工具清单
- [ ] 实现本地 MCP Server 薄代理
- [ ] 本地 MCP Server 通过环境变量读取 `AI_TOOL_TOKEN`
- [ ] 本地 MCP Server 将 `tools/list` 映射到 `/ai/tools`
- [ ] 本地 MCP Server 将 `tools/call` 映射到 `/ai/tools/call`
- [ ] 增加工具调用 dry-run 能力
- [ ] 增加中高风险工具确认机制
- [ ] 增加 AI 工具限流
- [ ] 增加 AI 工具调用测试
- [ ] 增加待办软删除工具测试，确认不会永久删除
- [ ] 增加禁止永久删除的策略测试
- [ ] 增加无 scope 调用失败测试
- [ ] 增加 token 过期和撤销测试
- [ ] 前端增加 AI Token 管理页面
- [ ] 前端增加 AI 工具调用审计页面
- [ ] 文档补充本地 MCP 客户端配置示例
- [ ] 文档补充远程 MCP 安全要求

## 验收标准

- [ ] AI 可以通过工具新增待办
- [ ] AI 可以通过工具查询待办
- [ ] AI 可以通过工具更新待办
- [ ] AI 可以通过工具完成待办
- [ ] AI 可以通过工具将待办移动到回收站
- [ ] AI 无法永久删除待办
- [ ] AI 无法清空回收站
- [ ] 没有对应 scope 的 AI Token 无法调用工具
- [ ] 所有 AI 工具调用都有审计记录
- [ ] MCP 工具列表只包含注册表允许的工具
- [ ] MCP 工具调用和普通 HTTP 工具调用走同一套权限、策略和审计逻辑
