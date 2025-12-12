# Docker Hoster

自动管理 Docker 容器的 `/etc/hosts` 条目，实时同步容器 IP 和主机名。

## 特性

- 🔄 自动发现运行中的容器
- ⚡ 实时监听容器启停事件
- 🌐 支持多网络容器
- 🏷️ 可选的标签过滤
- 🔒 原子性文件更新，防止损坏
- 🧹 优雅退出时自动清理

## 快速开始

### Docker 运行

```bash
docker run -d \
  --name docker-hoster \
  --restart=unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /etc/hosts:/app/docker-hosts \
  docker-hoster
```

### 使用 Docker Compose

```yaml
services:
  app:
    image: docker-hoster:latest
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /etc/hosts:/app/docker-hosts
```

## 配置

通过环境变量配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HOSTS_FILE` | `/app/docker-hosts` | hosts 文件路径（容器内） |
| `ENABLE_LABEL_FILTER` | `false` | 启用标签过滤 |
| `LABEL_KEY` | `hoster.enable` | 过滤标签键 |
| `LABEL_VALUE` | `true` | 过滤标签值 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 为什么使用 `/app/docker-hosts`？

docker-hoster 将宿主机的 `/etc/hosts` 挂载到容器内的 `/app/docker-hosts` 路径，而不是直接挂载到容器的 `/etc/hosts`。

**原因：**
- Docker 会自动在容器的 `/etc/hosts` 中注入必要的条目（如 localhost、容器自己的 hostname）
- 直接覆盖会导致这些条目丢失，可能影响容器内部的网络功能
- 使用独立路径可以避免这个问题，同时仍然能够修改宿主机的 hosts 文件

### 标签过滤示例

只管理带标签的容器：

```bash
# 启动 hoster 并启用过滤
docker run -d \
  --name docker-hoster \
  -e ENABLE_LABEL_FILTER=true \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /etc/hosts:/app/docker-hosts \
  docker-hoster

# 启动需要管理的容器
docker run -d --label hoster.enable=true nginx
```

## Hosts 文件格式

```
# Begin Docker Hoster
172.18.0.2	nginx
172.18.0.2	web-server
# End Docker Hoster
```

## 本地开发

```bash
# 克隆项目
git clone <repo-url>
cd docker-hoster

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行（需要 Docker 和 root 权限）
sudo venv/bin/python main.py

# 或使用环境变量指定测试用的 hosts 文件
HOSTS_FILE=/tmp/test_hosts python main.py
```

## 项目结构

```
docker-hoster/
├── hoster/              # 主应用包
│   ├── config.py       # 配置管理
│   ├── models.py       # 数据模型
│   ├── hosts_manager.py # 文件管理
│   ├── inspector.py    # 容器检查
│   ├── events.py       # 事件处理
│   └── app.py          # 主控制器
├── main.py             # 入口点
├── Dockerfile          # 容器构建
└── README.md           # 本文件
```

## 常见问题

**Q: 权限被拒绝？**
A: 确保容器有 `/etc/hosts` 写入权限

**Q: 连接 Docker 失败？**
A: 检查 socket 挂载：`-v /var/run/docker.sock:/var/run/docker.sock:ro`

**Q: 没有添加条目？**
A: 启用 `LOG_LEVEL=DEBUG` 查看详细日志

## 安全建议

- ✅ 始终以只读方式挂载 Docker socket（`:ro`）
- ✅ 使用标签过滤控制管理范围
- ✅ 在生产环境考虑网络隔离

## 技术栈

- Python 3.12
- Docker SDK for Python 7.1.0
- python-dotenv

## 许可证

MIT

---

**构建使用：** [Docker SDK](https://docker-py.readthedocs.io/) | [python-dotenv](https://github.com/theskumar/python-dotenv)
