#!/bin/bash
set -e

echo "云端部署已改用 Caddy 自动申请和续期 HTTPS 证书。"
echo
echo "生产环境启动后，Caddy 会根据 apps/cloud/caddy/Caddyfile 中的域名自动申请证书："
echo "  - sakurakugu.top"
echo "  - www.sakurakugu.top"
echo "  - api.sakurakugu.top"
echo
echo "使用前请确认："
echo "  1. 域名 A/AAAA 记录已经指向当前服务器"
echo "  2. 服务器 80、443 TCP 端口已开放"
echo "  3. 如需 HTTP/3，443 UDP 端口也已开放"
echo
echo "常用命令："
echo "  cd apps/cloud && docker compose up -d caddy"
echo "  cd apps/cloud && docker compose logs -f caddy"
echo
echo "证书数据保存在 Docker volume："
echo "  personal-system_caddydata"
echo "  personal-system_caddyconfig"
