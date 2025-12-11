"""
Docker 事件处理和监控模块
"""

import logging
from typing import Callable, Set

import docker


class DockerEventHandler:
    """
    处理 Docker 事件并触发 hosts 文件更新

    监控容器生命周期事件（start、stop、die、destroy、rename）
    并触发 hosts 文件的重建。
    """

    # 应该触发 hosts 文件重建的事件
    WATCHED_EVENTS: Set[str] = {'start', 'stop', 'die', 'destroy', 'rename'}

    def __init__(
        self,
        client: docker.DockerClient,
        rebuild_callback: Callable[[], None],
        logger: logging.Logger
    ):
        """
        初始化事件处理器

        参数:
            client: Docker 客户端实例
            rebuild_callback: 需要重建时调用的函数
            logger: 日志记录器实例
        """
        self.client = client
        self.rebuild_callback = rebuild_callback
        self.logger = logger
        self.running = True

    def listen_events(self) -> None:
        """
        监听 Docker 事件并处理容器变化

        在循环中运行直到停止。过滤容器事件并在必要时触发重建。

        异常:
            docker.errors.APIError: 如果 Docker API 通信失败
        """
        self.logger.info("启动 Docker 事件监听器")

        try:
            for event in self.client.events(decode=True):
                if not self.running:
                    self.logger.info("事件监听器已停止")
                    break

                # 只过滤容器事件
                if event.get('Type') != 'container':
                    continue

                action = event.get('Action')
                if action in self.WATCHED_EVENTS:
                    container_id = event.get('id', 'unknown')[:12]
                    container_name = event.get('Actor', {}).get('Attributes', {}).get('name', 'unknown')

                    self.logger.info(
                        f"容器事件: {action} - {container_name} ({container_id})"
                    )

                    # 触发 hosts 文件重建
                    try:
                        self.rebuild_callback()
                    except Exception as e:
                        self.logger.error(
                            f"{action} 事件后重建时出错: {e}",
                            exc_info=True
                        )

        except docker.errors.APIError as e:
            self.logger.error(f"事件监听器中的 Docker API 错误: {e}")
            raise
        except Exception as e:
            self.logger.error(f"事件监听器中的意外错误: {e}", exc_info=True)
            raise

    def stop(self) -> None:
        """停止监听事件"""
        self.running = False
        self.logger.info("正在停止事件监听器...")
