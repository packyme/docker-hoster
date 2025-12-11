"""
Hosts 文件管理模块，支持原子性更新
"""

import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import List

from hoster.models import HostEntry


class HostsFileManager:
    """
    管理 hosts 文件的原子性更新

    线程安全的 hosts 文件读写操作。
    使用原子性文件操作（临时文件 + 重命名）防止文件损坏。
    """

    MARKER = "# docker-hoster:"

    def __init__(self, hosts_path: str, logger: logging.Logger):
        """
        初始化 hosts 文件管理器

        参数:
            hosts_path: hosts 文件路径
            logger: 日志记录器实例
        """
        self.hosts_path = Path(hosts_path)
        self.logger = logger
        self.lock = threading.Lock()

    def read_existing_entries(self) -> List[str]:
        """
        读取现有的 hosts 条目，排除 docker-hoster 管理的条目

        返回:
            非 docker-hoster 管理的 hosts 文件行列表
        """
        existing_lines = []
        try:
            if not self.hosts_path.exists():
                self.logger.warning(f"Hosts 文件不存在: {self.hosts_path}")
                return existing_lines

            with open(self.hosts_path, 'r') as f:
                for line in f:
                    # 保留不包含 docker-hoster 标记的行
                    if self.MARKER not in line:
                        existing_lines.append(line.rstrip('\n'))

        except PermissionError:
            self.logger.error(f"读取 hosts 文件权限被拒绝: {self.hosts_path}")
            raise
        except Exception as e:
            self.logger.error(f"读取 hosts 文件时出错: {e}")
            raise

        return existing_lines

    def update_hosts(self, entries: List[HostEntry]) -> None:
        """
        原子性更新 hosts 文件

        参数:
            entries: 要写入的 HostEntry 对象列表

        异常:
            PermissionError: 如果没有写入 hosts 文件的权限
            OSError: 如果文件系统操作失败
        """
        with self.lock:
            try:
                # 1. 读取现有的非 docker-hoster 条目
                existing_lines = self.read_existing_entries()

                # 2. 构建新内容
                new_content = existing_lines.copy()
                if entries:
                    new_content.append('')  # 空行分隔符
                    new_content.append('# Docker Hoster 管理的条目')
                    for entry in entries:
                        new_content.append(entry.to_hosts_line())

                # 3. 写入临时文件（同一目录）
                temp_fd, temp_path = tempfile.mkstemp(
                    dir=self.hosts_path.parent,
                    prefix='.hosts.tmp.',
                    text=True
                )

                try:
                    with os.fdopen(temp_fd, 'w') as f:
                        f.write('\n'.join(new_content) + '\n')

                    # 4. 原子性替换（同一文件系统内有效）
                    os.replace(temp_path, self.hosts_path)
                    self.logger.info(f"已更新 {len(entries)} 条 host 记录")

                except Exception:
                    # 出错时清理临时文件
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    raise

            except PermissionError:
                self.logger.error(
                    f"写入 hosts 文件权限被拒绝: {self.hosts_path}. "
                    "请确保容器具有适当的权限。"
                )
                raise
            except Exception as e:
                self.logger.error(f"更新 hosts 文件失败: {e}")
                raise

    def remove_all_docker_entries(self) -> None:
        """
        移除所有 docker-hoster 管理的条目

        在清理/关闭时使用，恢复 hosts 文件。
        """
        with self.lock:
            try:
                existing_lines = self.read_existing_entries()

                # 只写回非 docker-hoster 的行
                temp_fd, temp_path = tempfile.mkstemp(
                    dir=self.hosts_path.parent,
                    prefix='.hosts.tmp.',
                    text=True
                )

                try:
                    with os.fdopen(temp_fd, 'w') as f:
                        f.write('\n'.join(existing_lines) + '\n')

                    os.replace(temp_path, self.hosts_path)
                    self.logger.info("已移除所有 docker-hoster 条目")

                except Exception:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    raise

            except Exception as e:
                self.logger.error(f"清理 hosts 文件失败: {e}")
                raise
