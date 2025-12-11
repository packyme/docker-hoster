FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY hoster/ ./hoster/
COPY main.py .

# 设置 Python 以无缓冲模式运行以实现实时日志
ENV PYTHONUNBUFFERED=1

# 安全考虑：以非 root 用户运行（已注释，因为需要访问 hosts 文件）
# 在生产环境中，改为以适当权限运行容器
# RUN useradd -m -u 1000 hoster && chown -R hoster:hoster /app
# USER hoster

# 健康检查（可选 - 检查进程是否正在运行）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python.*main.py" || exit 1

# 运行应用
CMD ["python", "-u", "main.py"]
