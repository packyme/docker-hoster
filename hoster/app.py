"""
Docker Hoster 主应用模块
"""

import logging
import sys
from typing import List

import docker
from docker.errors import DockerException

from hoster.config import Config
from hoster.events import DockerEventHandler
from hoster.hosts_manager import HostsFileManager
from hoster.inspector import ContainerInspector
from hoster.models import HostEntry


class DockerHoster:
    """
    主应用控制器，协调所有组件

    管理 Docker Hoster 应用的生命周期：
    - 初始化 Docker 客户端和组件
    - 启动时扫描现有容器
    - 监控 Docker 事件以处理容器变化
    - 原子性更新 hosts 文件
    - 处理优雅关闭
    """

    def __init__(self, config: Config):
        """
        初始化 Docker Hoster 应用

        参数:
            config: 应用配置

        异常:
            DockerException: 如果无法连接到 Docker 守护进程
            ValueError: 如果配置无效
        """
        self.config = config
        self.config.validate()

        self.logger = self._setup_logging()

        # 初始化 Docker 客户端
        try:
            if config.docker_host:
                self.logger.info(f"正在连接到 Docker: {config.docker_host}")
                self.client = docker.DockerClient(base_url=config.docker_host)
            else:
                self.logger.info("使用环境检测连接到 Docker")
                self.client = docker.from_env()

            # 测试连接
            self.client.ping()
            self.logger.info("成功连接到 Docker 守护进程")

        except DockerException as e:
            self.logger.error(f"连接到 Docker 守护进程失败: {e}")
            self.logger.error(
                "请确保 Docker 正在运行且 socket 可访问。"
                "如果使用自定义 socket，请检查 DOCKER_HOST 环境变量。"
            )
            raise

        # 初始化组件
        self.inspector = ContainerInspector(config, self.logger)
        self.hosts_manager = HostsFileManager(
            config.hosts_file_path,
            self.logger
        )
        self.event_handler = DockerEventHandler(
            self.client,
            self.rebuild_hosts,
            self.logger
        )

    def _setup_logging(self) -> logging.Logger:
        """
        配置日志系统

        返回:
            配置好的日志记录器实例
        """
        logger = logging.getLogger('docker-hoster')
        logger.setLevel(self.config.log_level)

        # 避免重复的处理器
        if logger.handlers:
            return logger

        # 带格式的控制台处理器
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.config.log_level)

        # 格式: 时间戳 - 名称 - 级别 - 消息
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        return logger

    def initialize(self) -> None:
        """
        初始化：扫描所有运行中的容器并构建初始 hosts 文件
        """
        self.logger.info("=" * 60)
        self.logger.info("Docker Hoster 启动中...")
        self.logger.info(f"Hosts 文件: {self.config.hosts_file_path}")
        self.logger.info(f"标签过滤: {self.config.enable_label_filter}")
        if self.config.enable_label_filter:
            self.logger.info(
                f"过滤条件: {self.config.label_key}={self.config.label_value}"
            )
        self.logger.info("=" * 60)

        self.rebuild_hosts()

    def rebuild_hosts(self) -> None:
        """
        从所有运行中的容器重建整个 hosts 文件

        扫描所有运行中的容器，提取主机条目，并原子性更新 hosts 文件。
        """
        try:
            containers = self.client.containers.list(all=False)
            self.logger.debug(f"发现 {len(containers)} 个运行中的容器")

            all_entries: List[HostEntry] = []

            for container in containers:
                try:
                    entries = self.inspector.extract_host_entries(container)
                    all_entries.extend(entries)

                except Exception as e:
                    # 隔离错误 - 单个容器失败不影响其他容器
                    self.logger.error(
                        f"处理容器 {container.name} 失败: {e}",
                        exc_info=True
                    )
                    continue

            # 更新 hosts 文件
            self.hosts_manager.update_hosts(all_entries)

            if all_entries:
                self.logger.info(
                    f"成功更新 hosts 文件，添加了 {len(all_entries)} 条记录"
                    f"（来自 {len(containers)} 个容器）"
                )
            else:
                self.logger.info("没有要添加的主机条目")

        except DockerException as e:
            self.logger.error(f"重建期间 Docker API 错误: {e}")
            raise
        except Exception as e:
            self.logger.critical(f"重建 hosts 文件失败: {e}", exc_info=True)
            raise

    def run(self) -> None:
        """
        启动主事件循环

        初始化应用并开始监听 Docker 事件。
        阻塞直到停止。
        """
        self.initialize()
        self.logger.info("正在监听 Docker 事件...")
        self.event_handler.listen_events()

    def cleanup(self) -> None:
        """
        清理：停止事件监听器并移除所有 docker-hoster 条目

        在优雅关闭期间调用，以恢复 hosts 文件。
        """
        self.logger.info("正在关闭 Docker Hoster...")

        try:
            self.event_handler.stop()
            self.hosts_manager.remove_all_docker_entries()
            self.client.close()
            self.logger.info("清理成功完成")
        except Exception as e:
            self.logger.error(f"清理期间出错: {e}", exc_info=True)
