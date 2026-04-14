FROM node:24-alpine AS builder
WORKDIR /app
# ENV NPM_CONFIG_REGISTRY=https://registry.npmmirror.com \
# 腾讯云内网镜像
ENV NPM_CONFIG_REGISTRY=http://mirrors.tencent.com/npm/  \
    NPM_CONFIG_REPLACE_REGISTRY_HOST=always \
    NPM_CONFIG_FETCH_RETRIES=5 \
    NPM_CONFIG_FETCH_RETRY_FACTOR=2 \
    NPM_CONFIG_FETCH_RETRY_MINTIMEOUT=20000 \
    NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT=120000 \
    NPM_CONFIG_FETCH_TIMEOUT=600000
COPY package*.json ./
RUN npm ci --no-audit --fund=false
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
