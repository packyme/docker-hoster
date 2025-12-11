"""
Docker Hoster - 自动管理 Docker 容器的 /etc/hosts 条目
"""

__version__ = "1.0.0"
__author__ = "Docker Hoster Project"

from hoster.app import DockerHoster
from hoster.config import Config
from hoster.models import HostEntry

__all__ = ["DockerHoster", "Config", "HostEntry"]
