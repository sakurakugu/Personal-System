FROM python:3.12-slim

WORKDIR /app

# TOFO: 自动检测是否在腾讯内网中
# 根据基础镜像自动识别发行版代号，避免 bookworm/trixie 混源导致更新变慢。
RUN set -eux; \
	rm -f /etc/apt/sources.list.d/*.sources; \
	. /etc/os-release; \
	echo "deb http://mirrors.tencentyun.com/debian ${VERSION_CODENAME} main contrib non-free non-free-firmware" > /etc/apt/sources.list; \
	echo "deb http://mirrors.tencentyun.com/debian ${VERSION_CODENAME}-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list; \
	echo "deb http://mirrors.tencentyun.com/debian-security ${VERSION_CODENAME}-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list; \
	apt-get update; \
	apt-get install -y --no-install-recommends gcc libpq-dev; \
	rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --retries 5 --timeout 120 -i https://mirrors.tencent.com/pypi/simple -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
