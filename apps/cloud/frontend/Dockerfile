# syntax=docker/dockerfile:1

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

# 先只复制依赖清单，让源码改动不会导致 npm 安装层失效。
COPY --parents package.json package-lock.json ./
COPY --parents apps/cloud/frontend/package.json ./
COPY --parents packages/*/package.json packages/modules/*/package.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --workspace frontend --include-workspace-root=true --no-audit --fund=false --include=optional

COPY apps/cloud/frontend ./apps/cloud/frontend
COPY configs ./configs
COPY packages ./packages

WORKDIR /app/apps/cloud/frontend
ARG VITE_TWIKOO_ENV_ID=
ARG VITE_TWIKOO_REGION=
ENV VITE_TWIKOO_ENV_ID=${VITE_TWIKOO_ENV_ID}
ENV VITE_TWIKOO_REGION=${VITE_TWIKOO_REGION}
RUN npm run build --workspace frontend

FROM nginx:alpine
COPY --from=builder /app/apps/cloud/frontend/dist /usr/share/nginx/html
COPY apps/cloud/frontend/nginx.conf /etc/nginx/conf.d/default.conf
