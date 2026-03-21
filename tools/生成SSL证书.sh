#!/bin/bash
set -e

# -----------------------------
# 0️⃣ 解析参数
# -----------------------------
# 参数变量
AUTO_YES=false
DOMAIN=""
AK_ID=""
AK_SECRET=""
PROVIDER=""
APT_YES=""
$AUTO_YES && APT_YES="-y"

while [[ $# -gt 0 ]]; do
  case $1 in
    --domain)
      DOMAIN="$2"
      shift 2
      ;;
    --provider)
      PROVIDER="$2"
      shift 2
      ;;
    --ak)
      AK_ID="$2"
      shift 2
      ;;
    --sk)
      AK_SECRET="$2"
      shift 2
      ;;
    -y|--yes)
      AUTO_YES=true
      shift
      ;;
    -h|--help)
      echo "用法:"
      echo "  $0 [options]"
      echo
      echo "选项:"
      echo "  --domain DOMAIN     主域名"
      echo "  --provider PROVIDER 解析平台: aliyun / tencent"
      echo "  --ak KEY             AccessKey / SecretId"
      echo "  --sk SECRET          Secret / SecretKey"
      echo "  -y, --yes           非交互模式"
      exit 0
      ;;
    *)
      echo "未知参数: $1"
      exit 1
      ;;
  esac
done

# -----------------------------
# 1️⃣ 安装必要工具
# -----------------------------
echo "更新系统并安装 python3-venv、pip..."
sudo apt update
sudo apt install python3-venv python3-pip $APT_YES

# -----------------------------
# 2️⃣ 创建虚拟环境
# -----------------------------
# VENV_DIR=/opt/certbot-venv
# echo "创建 Certbot 虚拟环境：$VENV_DIR"
# sudo mkdir -p "$VENV_DIR"
# cd "$VENV_DIR"
# sudo python3 -m venv .
# source "$VENV_DIR/bin/activate"

# # 升级 pip / setuptools / wheel
# pip install --upgrade pip setuptools wheel

# # 安装 Certbot + Aliyun 插件
# pip install certbot certbot-dns-aliyun

# 安装 Certbot + DNS 插件
if ! command -v certbot &> /dev/null; then
  sudo apt install certbot $APT_YES
fi
sudo pip install --break-system-packages certbot-dns-aliyun
sudo pip install --break-system-packages certbot-dns-tencentcloud

# -----------------------------
# 3️⃣ 检测解析平台
# -----------------------------
detect_provider() {
  if curl -s cip.cc | grep -qi "腾讯云"; then
    echo "tencent"
    return 0
  fi
  if curl -s ipinfo.io | grep -qi "Tencent"; then
    echo "tencent"
    return 0
  fi
  echo "aliyun"
}

if [ -z "$PROVIDER" ]; then
  PROVIDER="$(detect_provider)"
fi

if [ "$PROVIDER" != "aliyun" ] && [ "$PROVIDER" != "tencent" ]; then
  echo "解析平台仅支持 aliyun 或 tencent"
  exit 1
fi

echo "解析平台：$PROVIDER"

# -----------------------------
# 4️⃣ 创建 API Key 文件
# -----------------------------
SECRETS_DIR=/root/.config/.secrets
if [ "$PROVIDER" = "tencent" ]; then
  INI_FILE=$SECRETS_DIR/tencentcloud.ini
else
  INI_FILE=$SECRETS_DIR/aliyun.ini
fi
sudo mkdir -p "$SECRETS_DIR"

if [ "$PROVIDER" = "tencent" ]; then
  echo "创建腾讯云 API Key"
  echo "1. 进入腾讯云控制台 ➡ 访问管理"
  echo "   创建：用户 → 访问方式 (SecretId/SecretKey)"
  echo "   然后给予DNS权限：QcloudDNSPodFullAccess"
else
  echo "创建阿里云 API Key"
  echo "1. 进入阿里云控制台 ➡ RAM 访问控制"
  echo "   创建：用户 → 编程访问 (AccessKey)"
  echo "   得到："
  echo "      - AccessKey ID"
  echo "      - AccessKey Secret"
  echo "   然后给予DNS权限：AliyunDNSFullAccess"
fi
echo ""

if [ -z "$AK_ID" ]; then
  read -p "输入 AccessKey ID: " AK_ID
fi

if [ -z "$AK_SECRET" ]; then
  read -sp "输入 AccessKey Secret: " AK_SECRET
  echo
fi

# 备份旧文件（如果存在）
if [ -f "$INI_FILE" ]; then
    sudo cp "$INI_FILE" "$INI_FILE.bak.$(date +%F-%H%M%S)"
    echo "旧 aliyun.ini 已备份到 $INI_FILE.bak"
fi

# 写入 ini 文件
if [ "$PROVIDER" = "tencent" ]; then
  sudo tee "$INI_FILE" > /dev/null <<EOF
dns_tencentcloud_secret_id = $AK_ID
dns_tencentcloud_secret_key = $AK_SECRET
EOF
else
  sudo tee "$INI_FILE" > /dev/null <<EOF
dns_aliyun_access_key = $AK_ID
dns_aliyun_access_key_secret = $AK_SECRET
EOF
fi

sudo chmod 600 "$INI_FILE"
echo "API Key 文件已创建并设置权限 600"

# -----------------------------
# 5️⃣ 输入域名并申请证书
# -----------------------------
if [ -z "$DOMAIN" ]; then
  read -p "请输入你的主域名（例如 sakurakugu.top）: " DOMAIN
fi
echo "即将生成泛域名证书：*.$DOMAIN 和 $DOMAIN"

# sudo "$VENV_DIR/bin/certbot" certonly \
if [ "$PROVIDER" = "tencent" ]; then
  sudo "certbot" certonly \
    --authenticator dns-tencentcloud \
    --dns-tencentcloud-credentials "$INI_FILE" \
    -d "*.$DOMAIN" \
    -d "$DOMAIN"
else
  sudo "certbot" certonly \
    --authenticator dns-aliyun \
    --dns-aliyun-credentials "$INI_FILE" \
    -d "*.$DOMAIN" \
    -d "$DOMAIN"
fi

echo
echo "证书生成完成！路径如下："
echo "  /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
echo "  /etc/letsencrypt/live/$DOMAIN/privkey.pem"
echo
echo "请将证书挂载到 nginx 并 reload 容器或服务"
echo "例如：docker exec nginx_container nginx -s reload"

# -----------------------------
# 6️⃣ 提示自动续期测试
# -----------------------------
echo
echo "你可以测试模拟续期是否成功："
# echo "source $VENV_DIR/bin/activate && certbot renew --dry-run"
echo "certbot renew --dry-run"
systemctl status certbot.timer
