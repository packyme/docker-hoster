"""
Docker Hoster 数据模型
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HostEntry:
    """
    代表 hosts 文件中的单个条目

    属性:
        ip_address: 容器的 IP 地址
        hostname: 要映射的主机名
        container_name: Docker 容器名称
    """

    ip_address: str
    hostname: str
    container_name: str

    def to_hosts_line(self) -> str:
        """
        转换为 hosts 文件行格式

        格式: <IP>\t<主机名>\t# docker-hoster: <容器名>

        返回:
            格式化的 hosts 文件行
        """
        return f"{self.ip_address}\t{self.hostname}\t# docker-hoster: {self.container_name}"

    def __str__(self) -> str:
        return f"{self.hostname} -> {self.ip_address} ({self.container_name})"
