"""
容器检查和主机条目提取模块
"""

import logging
from typing import List, Set

from docker.models.containers import Container

from hoster.config import Config
from hoster.models import HostEntry


class ContainerInspector:
    """
    从 Docker 容器提取主机信息

    支持每个容器多个网络和基于标签的过滤。
    """

    def __init__(self, config: Config, logger: logging.Logger):
        """
        初始化容器检查器

        参数:
            config: 应用配置
            logger: 日志记录器实例
        """
        self.config = config
        self.logger = logger

    def should_process_container(self, container: Container) -> bool:
        """
        根据标签过滤检查是否应该处理此容器

        参数:
            container: Docker 容器对象

        返回:
            如果应该处理容器返回 True，否则返回 False
        """
        if not self.config.enable_label_filter:
            return True

        labels = container.labels or {}
        label_value = labels.get(self.config.label_key)
        should_process = label_value == self.config.label_value

        if should_process:
            self.logger.debug(
                f"容器 {container.name} 匹配标签过滤器: "
                f"{self.config.label_key}={label_value}"
            )
        else:
            self.logger.debug(
                f"容器 {container.name} 被标签过滤器跳过"
            )

        return should_process

    def _extract_hostnames(self, container: Container) -> List[str]:
        """
        提取容器的所有可能主机名

        包括:
        - 容器名


        参数:
            container: Docker 容器对象

        返回:
            容器名列表
        """
        hostnames: Set[str] = set()

        try:
            # 只提取容器名（去掉开头的 /）
            container_name = container.name.lstrip('/')
            if container_name:
                hostnames.add(container_name)

        except Exception as e:
            self.logger.error(
                f"从容器 {container.name} 提取主机名时出错: {e}"
            )

        return sorted(list(hostnames))

    def extract_host_entries(self, container: Container) -> List[HostEntry]:
        """
        提取容器的所有主机条目

        只使用第一个网络的 IP - 避免同一容器名出现多次。

        参数:
            container: Docker 容器对象

        返回:
            HostEntry 对象列表
        """
        if not self.should_process_container(container):
            self.logger.debug(f"跳过容器 {container.name}（标签过滤）")
            return []

        entries = []
        container_name = container.name

        try:
            # 提取所有主机名
            hostnames = self._extract_hostnames(container)

            if not hostnames:
                self.logger.warning(
                    f"容器 {container_name} 没有主机名"
                )
                return []

            # 获取所有网络
            networks = container.attrs.get('NetworkSettings', {}).get('Networks', {})

            if not networks:
                self.logger.debug(
                    f"容器 {container_name} 没有网络"
                )
                return []

            # 只使用第一个有效网络的 IP
            for network_name, network_data in networks.items():
                ip_address = network_data.get('IPAddress')

                if not ip_address:
                    self.logger.debug(
                        f"容器 {container_name} 在 {network_name} 上没有 IP"
                    )
                    continue

                # 为每个主机名创建条目（只使用第一个网络的 IP）
                for hostname in hostnames:
                    entries.append(HostEntry(
                        ip_address=ip_address,
                        hostname=hostname,
                        container_name=container_name
                    ))

                self.logger.debug(
                    f"容器 {container_name} 使用网络 {network_name}: "
                    f"{ip_address} -> {hostnames}"
                )

                # 找到第一个有效 IP 后就退出循环
                break

        except KeyError as e:
            self.logger.error(
                f"容器 {container_name} 缺少预期字段: {e}"
            )
        except Exception as e:
            self.logger.error(
                f"处理容器 {container_name} 时出错: {e}",
                exc_info=True
            )

        return entries
