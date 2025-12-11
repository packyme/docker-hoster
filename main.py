#!/usr/bin/env python3
"""
Docker Hoster - 主入口点

自动管理 Docker 容器的 /etc/hosts 条目。
"""

import signal
import sys
from pathlib import Path

# 将当前目录添加到路径以导入 hoster 模块
sys.path.insert(0, str(Path(__file__).parent))

from hoster import DockerHoster, Config


def main() -> None:
    """主入口点，带信号处理"""

    # 从环境变量加载配置
    config = Config.from_env()

    # 初始化 Docker Hoster
    try:
        hoster = DockerHoster(config)
    except Exception as e:
        print(f"初始化 Docker Hoster 失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 定义信号处理器以实现优雅关闭
    def signal_handler(signum: int, frame) -> None:
        """处理关闭信号"""
        signal_name = signal.Signals(signum).name
        hoster.logger.info(f"收到信号 {signal_name}，正在关闭...")
        hoster.cleanup()
        sys.exit(0)

    # 注册信号处理器
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # 运行应用
    try:
        hoster.run()
    except KeyboardInterrupt:
        hoster.logger.info("被用户中断")
        hoster.cleanup()
        sys.exit(0)
    except Exception as e:
        hoster.logger.error(f"致命错误: {e}", exc_info=True)
        hoster.cleanup()
        sys.exit(1)


if __name__ == '__main__':
    main()
