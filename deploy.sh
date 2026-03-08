#!/usr/bin/env bash
set -euo pipefail

echo "🌸 Sakurakugu Blog - 部署脚本"
echo "========================="

# ── 检查 .env 文件 ──
if [ ! -f .env ]; then
    echo "❌ 未找到 .env 文件，正在从 .env.example 复制..."
    cp .env.example .env
    echo "⚠️  请先编辑 .env 文件中的敏感信息（密码、JWT密钥等），然后重新运行此脚本"
    exit 1
fi

# ── 生成随机 JWT 密钥（如未修改默认值） ──
JWT_KEY=$(grep JWT_SECRET_KEY .env | cut -d'=' -f2)
if [ "$JWT_KEY" = "replace-with-a-very-long-random-string" ]; then
    NEW_KEY=$(openssl rand -hex 32)
    sed -i "s/replace-with-a-very-long-random-string/$NEW_KEY/" .env
    echo "✅ 已自动生成 JWT_SECRET_KEY"
fi

# TODO: 如果证书到期，需要自动重启nginx（要先检查是否存在等条件）
# sudo nano /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
# #!/bin/bash
# docker exec nginx nginx -s reload
# sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh

echo ""
echo "1️⃣  构建并启动所有容器..."
docker compose up -d --build

echo ""
echo "2️⃣  等待服务启动..."
sleep 10

echo ""
echo "3️⃣  检查服务状态..."
docker compose ps

echo ""
echo "4️⃣  测试 API 健康检查..."
curl -sf http://localhost:8000/api/health && echo " ✅ API 正常" || echo " ❌ API 异常"

echo ""
echo "========================="
echo "🎉 部署完成！"
echo ""
echo "   前端:  http://www.sakurakugu.top"
echo "   API:   http://api.sakurakugu.top"
echo "   文档:  http://api.sakurakugu.top/api/docs"
echo ""
echo "后续步骤："
echo "  1. 配置 DNS: www.sakurakugu.top → 服务器IP"
echo "  2. 配置 DNS: api.sakurakugu.top → 服务器IP"
echo "  3. 安装 SSL 证书（见下方命令）"
echo ""
echo "SSL 证书命令（需要先安装 certbot）："
echo "  apt install certbot"
echo "  certbot certonly --webroot -w /var/www/certbot -d www.sakurakugu.top -d api.sakurakugu.top"
echo "  # 然后将证书复制到 nginx/ssl/ 并取消 nginx 配置中 HTTPS 部分的注释"
echo ""
