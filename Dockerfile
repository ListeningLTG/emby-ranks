# ==========================================
# Stage 1: Build Frontend
# ==========================================
FROM node:20-alpine AS build-stage
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci --prefer-offline --no-audit

COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Production Runtime
# ==========================================
FROM python:3.12-slim

WORKDIR /app

# 安装必要的运行时依赖（字体渲染支持与时区数据）
RUN apt-get update && apt-get install -y --no-install-recommends \
    fontconfig \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# 创建持久化目录
RUN mkdir -p /app/config /app/data /app/assets /app/static

# 安装 Python 后端依赖
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# 复制后端代码与内置静态资源
COPY core/ ./core/
COPY backend/ ./backend/
COPY notifiers/ ./notifiers/
COPY assets/ ./assets/
COPY scheduler.py .
COPY main.py .

# 复制前端打包产物至 static 目录
COPY --from=build-stage /app/static ./static

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TZ=Asia/Shanghai
ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE 8000

# 默认启动 Web 控制台与定时调度服务
ENTRYPOINT ["python", "main.py"]
