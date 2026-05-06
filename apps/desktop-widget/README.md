# 桌面小工具

这是 `Personal System` 的 `Qt` 桌面小工具最小骨架。

当前目标：

- 接收桌面端主程序签发的 `widget_basic` 凭证
- 本地保存小工具配置
- 提供基础连通性测试
- 为后续待办、摘要、提醒等轻量能力预留入口

## 当前能力

- 配置 API 基地址
- 配置小工具名称
- 粘贴并保存设备令牌到系统安全存储
- 读取并显示本地配置
- 通过 `GET /widget/summary` 验证当前令牌是否可用
- 显示待办数量、今日到期数量、逾期数量摘要

当前的连通性测试已经切换到 widget 专用摘要接口，不再依赖 `/users/me`。

## 运行方式

当前推荐直接通过仓库统一启动脚本启动：

```bash
python ./tools/1.启动项目.py --desktop-widget
```

统一启动脚本会处理：

- 依赖安装与变更检测
- 日志输出与日志文件落盘
- 进程状态记录
- `--status` / `--stop` 联动

如果只想单独调试小工具目录，也可以直接安装并运行：

```bash
python -m pip install -e ./apps/desktop-widget
python ./apps/desktop-widget/main.py
```

常用命令：

```bash
python ./tools/1.启动项目.py --desktop-widget
python ./tools/1.启动项目.py --status
python ./tools/1.启动项目.py --stop
```

## 默认配置

- 默认 API 基地址：`http://127.0.0.1:8000/api/v1`
- 默认配置文件（仅保存非敏感配置，不含 token）：
  - Windows：`%APPDATA%/PersonalSystem/desktop-widget/config.json`
  - 其他平台：`~/.config/PersonalSystem/desktop-widget/config.json`
- 小工具 Token：
  - 保存在系统安全存储中
  - Windows 默认使用“Windows Credential Manager”

## 后续建议

- 增加 widget 专用只读/轻写接口
- 增加待办摘要卡片
- 增加提醒轮询与系统通知
- 增加系统托盘与无边框悬浮样式
