"""
配置管理模块，支持环境变量
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """应用配置类，从环境变量加载配置"""

    hosts_file_path: str = "/app/docker-hosts"
    docker_host: Optional[str] = None
    enable_label_filter: bool = False
    label_key: str = "hoster.enable"
    label_value: str = "true"
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Config":
        """
        从环境变量加载配置

        环境变量说明:
            HOSTS_FILE: hosts 文件路径 (默认: /app/docker-hosts)
            DOCKER_HOST: Docker 守护进程 socket URL (默认: 自动检测)
            ENABLE_LABEL_FILTER: 启用容器标签过滤 (默认: false)
            LABEL_KEY: 过滤标签键 (默认: hoster.enable)
            LABEL_VALUE: 过滤标签值 (默认: true)
            LOG_LEVEL: 日志级别 (默认: INFO)
        """
        return cls(
            hosts_file_path=os.getenv("HOSTS_FILE", "/app/docker-hosts"),
            docker_host=os.getenv("DOCKER_HOST"),
            enable_label_filter=os.getenv("ENABLE_LABEL_FILTER", "false").lower() == "true",
            label_key=os.getenv("LABEL_KEY", "hoster.enable"),
            label_value=os.getenv("LABEL_VALUE", "true"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper()
        )

    def validate(self) -> None:
        """验证配置是否有效"""
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level not in valid_log_levels:
            raise ValueError(
                f"无效的 LOG_LEVEL: {self.log_level}. "
                f"必须是以下之一: {', '.join(valid_log_levels)}"
            )
