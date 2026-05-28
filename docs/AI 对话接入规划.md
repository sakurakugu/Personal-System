# AI 对话接入规划

## 背景

当前云端前端已经在全局应用壳中挂载了 `AIChatWidget`：

- `apps/cloud/frontend/src/App.vue`
- `packages/ui/src/components/AIChatWidget`

组件目前通过 `url` 属性连接后端，云端前端传入的是：

```vue
<AIChatWidget url="/api/chat" />
```

组件内部使用原生 `fetch` 发起 `POST` 请求，并支持两类请求体：

- 无附件：`application/json`
- 有附件：`FormData`，其中包含 `messages` 和 `files`

响应格式支持：

- `application/json`
- `text/event-stream`
- `application/x-ndjson`
- `text/plain`

这说明当前组件已经具备基本聊天 UI 和流式响应展示能力，但后端接口、权限边界、CSRF 处理和管理页面还没有形成完整闭环。

---

## 当前问题

### `/api/chat` 不符合现有后端路由风格

后端当前主业务接口统一注册在：

```text
/api/v1
```

也就是新增聊天接口时，更适合使用：

```text
POST /api/v1/ai/chat
```

而不是继续使用裸路径：

```text
POST /api/chat
```

如果没有额外 Nginx 代理或独立服务注册 `/api/chat`，当前组件请求大概率会返回 404。

### 登录态会携带，但 CSRF 头缺失

`AIChatWidget` 当前请求带有：

```ts
credentials: 'include'
```

因此浏览器会携带当前站点的登录 Cookie。

但后端对携带 Session Cookie 的写请求会执行 CSRF 校验，需要同时提交：

```text
X-CSRF-Token
```

统一 API 客户端 `packages/api/src/client.ts` 已经处理了这个逻辑，但 `AIChatWidget` 当前直接使用原生 `fetch`，没有复用统一 API 客户端，也没有自行读取 `csrf_token` Cookie 写入请求头。

所以如果聊天接口要求登录，当前写法很可能被后端中间件拦截并返回 403。

### `packages/ui` 不应该绑定云端业务细节

`AIChatWidget` 位于 `packages/ui`，它更适合保持为纯 UI 组件。

不建议在这里直接绑定：

- 云端 API base URL
- 登录态恢复逻辑
- 设备 Token
- CSRF 规则
- 业务权限判断

这些属于应用层或接口层职责。

---

## 推荐目标

第一阶段目标：

- 后端新增真实聊天接口
- 前端聊天组件能稳定请求后端
- 只有登录用户可以使用
- 后台提供 AI 配置与运行状态管理页面
- 保留后续扩展工具调用、会话存储、调用日志的空间

推荐接口：

```text
POST /api/v1/ai/chat
```

推荐前端挂载：

```vue
<AIChatWidget url="/api/v1/ai/chat" />
```

但更理想的长期方案是让组件接收应用层注入的发送函数，而不是让 `packages/ui` 自己处理后端请求。

---

## 后端设计

### 模块目录

建议新增后端模块：

```text
apps/cloud/backend/app/modules/ai_chat/
  __init__.py
  api.py
  schemas.py
  service.py
  models.py
```

如果后续要支持可调用工具，可以继续扩展：

```text
apps/cloud/backend/app/modules/ai_chat/
  providers.py
  usage.py
  audit.py
  tools/
```

### 路由注册

在：

```text
apps/cloud/backend/app/api/v1/router.py
```

注册：

```python
from app.modules.ai_chat.api import router as ai_chat_router
```

并加入 `routers` 列表。

最终路径为：

```text
POST /api/v1/ai/chat
```

### 权限要求

建议第一版聊天接口要求登录：

```python
user: 用户 = Depends(获取当前用户)
```

原因：

- AI 调用有成本
- 接口容易被刷
- 后续可能接入个人数据、待办、文章、收藏、文件等能力
- 登录用户便于做调用日志、额度限制和问题排查

不建议匿名开放。如果确实需要博客访客试用，应单独设计低权限匿名接口，并增加频率限制、验证码或每日额度。

### 请求格式

建议兼容当前组件格式。

无附件请求：

```json
{
  "messages": [
    {
      "id": "message-id",
      "role": "user",
      "content": "你好",
      "parts": [
        { "type": "text", "text": "你好" }
      ]
    }
  ]
}
```

有附件请求：

```text
Content-Type: multipart/form-data

messages: JSON 字符串
files: File[]
```

第一版可以先只支持文本消息，把附件保存为后续任务；但接口需要明确返回“不支持附件”的错误，避免静默失败。

### 响应格式

推荐使用 SSE：

```text
Content-Type: text/event-stream
```

返回内容示例：

```text
data: {"delta":"你好"}
data: {"delta":"，我可以帮你整理待办。"}
data: [DONE]
```

当前组件的流式解析已经能处理 `data:` 行和 JSON 文本提取。

### 服务层职责

`service.py` 建议负责：

- 读取 AI 设置
- 校验模型是否启用
- 组装系统提示词
- 调用模型供应商
- 处理超时和异常
- 写入调用日志
- 产出流式响应

路由层只做：

- 权限校验
- 请求解析
- 参数校验
- 调用服务层
- 返回响应

### 日志

后端需要增加结构化日志，至少包含：

- 当前用户 ID
- 模型供应商
- 模型名
- 请求消息数量
- 是否包含附件
- 耗时
- 错误类型

不要记录完整密钥。用户输入内容是否落库需要做开关，默认建议只记录摘要和用量，避免以后隐私数据混在日志里。

---

## 前端接入设计

### 短期方案

短期可以继续使用 `AIChatWidget` 的 `url` 参数，但需要补齐 CSRF 头。

可选做法：

1. 在 `AIChatWidget` 内部读取 `csrf_token` Cookie 并设置 `X-CSRF-Token`
2. 给 `AIChatWidget` 增加 `headers` 或 `beforeRequest` 属性，由应用层注入
3. 给 `AIChatWidget` 增加 `sendMessage` 属性，完全由应用层负责请求

推荐优先级：

```text
sendMessage > beforeRequest > 组件内读取 Cookie
```

原因是 `packages/ui` 应尽量不感知云端认证细节。

### 推荐长期方案

将聊天请求能力放到应用层或接口层：

```text
apps/cloud/frontend/src/modules/AI/api.ts
```

或如果未来跨端复用：

```text
packages/api/src/ai-chat.ts
```

`AIChatWidget` 只负责：

- 展示消息
- 选择附件
- 触发发送
- 展示流式内容
- 展示错误

请求逻辑由外部注入：

```ts
async function 发送AI消息(payload, signal) {
  // 使用统一 API 基地址、认证、CSRF、设备 Token 等能力
}
```

### 未登录状态

前端建议按登录态控制入口：

- 未登录：隐藏聊天按钮，或点击后弹登录框
- 已登录：正常展示
- 请求返回 401：清理会话并提示重新登录
- 请求返回 403：提示权限不足或 CSRF 校验失败

如果聊天只给后台用户用，可以只在 `/dashboard` 路由下挂载。

如果博客页也希望使用，则建议所有登录用户可用，但功能权限由后端继续控制。

---

## AI 管理页面

### 路由位置

建议新增后台页面：

```text
/dashboard/ai
```

前端文件：

```text
apps/cloud/frontend/src/modules/管理/dashboard/pages/AI管理页面.vue
```

路由注册：

```text
apps/cloud/frontend/src/app/router/dashboard.routes.ts
```

菜单注册：

```text
apps/cloud/frontend/src/app/navigation/dashboard-navigation.ts
```

权限建议：

```ts
meta: { requiresSuperAdmin: true }
access: 'super-admin'
```

### 第一版页面内容

建议第一版管理页包含：

- 启用状态：是否开启 AI 对话
- 访问策略：仅登录用户、仅管理员、仅超级管理员
- 供应商配置：OpenAI、OpenAI 兼容接口、本地模型等
- 模型配置：模型名、Base URL、默认模型
- 密钥状态：只显示是否已配置，不回显完整密钥
- 生成参数：max tokens、timeout
- 系统提示词：默认助手人设和边界
- 附件策略：是否允许附件、最大大小、允许类型
- 调用限制：每用户每日次数、每分钟频率限制
- 测试面板：后台发送一条测试消息验证配置
- 调用日志：时间、用户、模型、耗时、状态、错误摘要

### 后端管理接口

建议新增：

```text
GET    /api/v1/admin/ai/settings
PATCH  /api/v1/admin/ai/settings
POST   /api/v1/admin/ai/test
GET    /api/v1/admin/ai/logs
```

这些接口都要求超级管理员权限。

密钥更新建议单独处理：

```text
PATCH /api/v1/admin/ai/secret
```

返回时只返回：

```json
{
  "has_secret": true,
  "secret_updated_at": "2026-05-29T00:00:00Z"
}
```

不要返回明文密钥。

---

## 数据库建议

如果只读环境变量，第一版可以不建表。

但如果要支持后台页面动态修改配置，需要建表和迁移。

推荐表：

```text
ai_settings
ai_call_logs
```

### `ai_settings`

用于保存 AI 配置。

建议字段：

- `id`
- `enabled`
- `access_policy`
- `provider`
- `base_url`
- `model`
- `max_tokens`
- `timeout_seconds`
- `system_prompt`
- `allow_attachments`
- `max_attachment_size_mb`
- `daily_limit_per_user`
- `secret_ciphertext`
- `secret_updated_at`
- `created_at`
- `updated_at`

### `ai_call_logs`

用于排查问题和统计用量。

建议字段：

- `id`
- `user_id`
- `provider`
- `model`
- `status`
- `prompt_tokens`
- `completion_tokens`
- `total_tokens`
- `duration_ms`
- `message_count`
- `attachment_count`
- `error_type`
- `error_message`
- `created_at`

是否记录用户原始输入应做成开关，默认不记录。

---

## 推荐实施顺序

- [ ] 新增后端 `ai_chat` 模块，先支持文本聊天
- [ ] 注册 `POST /api/v1/ai/chat`
- [ ] 接入登录校验和基础日志
- [ ] 前端将 `url` 改为 `/api/v1/ai/chat`
- [ ] 补齐 CSRF 头，或改为应用层注入发送函数
- [ ] 增加未登录状态处理
- [ ] 新增后台 AI 管理页，只读展示配置状态
- [ ] 增加设置保存、测试面板和调用日志
- [ ] 再考虑附件、多模型、工具调用、会话历史

---

## 最终建议

当前 `AIChatWidget` 的 UI 可以继续保留，但连接方式建议调整。

推荐最终形态：

- `packages/ui`：只保留聊天窗口和交互组件
- `packages/api` 或云端前端模块：负责 AI 请求、CSRF、认证、流式解析
- `apps/cloud/backend/app/modules/ai_chat`：负责聊天接口和模型调用
- `apps/cloud/frontend/src/modules/管理`：负责 AI 管理页面
- 后端接口默认只允许登录用户使用
- 管理接口只允许超级管理员使用

这样可以避免 UI 组件绑定云端业务细节，也方便后续扩展到手机端、桌面端和更多 AI 工具。
