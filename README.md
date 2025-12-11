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
  -v /etc/hosts:/etc/hosts \
  docker-hoster
```

### 使用 Docker Compose

```yaml
version: '3.8'

services:
  hoster:
    build: .
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /etc/hosts:/etc/hosts
```

## 配置

通过环境变量配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HOSTS_FILE` | `/etc/hosts` | hosts 文件路径 |
| `ENABLE_LABEL_FILTER` | `false` | 启用标签过滤 |
| `LABEL_KEY` | `hoster.enable` | 过滤标签键 |
| `LABEL_VALUE` | `true` | 过滤标签值 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 标签过滤示例

只管理带标签的容器：

```bash
# 启动 hoster 并启用过滤
docker run -d \
  --name docker-hoster \
  -e ENABLE_LABEL_FILTER=true \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /etc/hosts:/etc/hosts \
  docker-hoster

# 启动需要管理的容器
docker run -d --label hoster.enable=true nginx
```

## Hosts 文件格式

```
# Docker Hoster 管理的条目
172.18.0.2	nginx	# docker-hoster: web-server
172.18.0.2	web-server	# docker-hoster: web-server
```

## 本地开发

```bash
# 克隆项目
git clone <repo-url>
cd docker-hoster

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
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
