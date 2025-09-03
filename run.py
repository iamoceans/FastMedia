#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastMedia 启动脚本

使用方法:
    python run.py                    # 开发模式启动
    python run.py --prod             # 生产模式启动
    python run.py --host 0.0.0.0     # 指定主机
    python run.py --port 8080        # 指定端口
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import app
from config import config
from utils import setup_logging, clean_old_files

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='FastMedia 媒体处理服务')
    
    parser.add_argument(
        '--env', 
        choices=['development', 'production', 'testing'],
        default='development',
        help='运行环境 (默认: development)'
    )
    
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='服务器主机地址 (默认: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='服务器端口 (默认: 5000)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    parser.add_argument(
        '--prod',
        action='store_true',
        help='生产模式启动 (等同于 --env production)'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='启动前清理旧文件'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别 (默认: INFO)'
    )
    
    return parser.parse_args()

def setup_environment(env_name: str):
    """设置环境配置"""
    config_class = config.get(env_name, config['default'])
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    return config_class

def check_dependencies():
    """检查依赖是否安装"""
    required_packages = [
        'flask',
        'yt_dlp',
        'moviepy',
        'PIL',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少以下依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

def print_startup_info(host: str, port: int, env: str, debug: bool):
    """打印启动信息"""
    print("\n" + "="*50)
    print("🚀 FastMedia 媒体处理服务")
    print("="*50)
    print(f"📍 服务地址: http://{host}:{port}")
    print(f"🌍 运行环境: {env}")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    print(f"📁 工作目录: {project_root}")
    print("="*50)
    print("\n功能列表:")
    print("  📥 批量视频下载 (支持抖音、TikTok、B站、YouTube等)")
    print("  🎵 BGM提取")
    print("  🖼️  封面提取")
    print("\n按 Ctrl+C 停止服务")
    print("="*50 + "\n")

def main():
    """主函数"""
    args = parse_arguments()
    
    # 确定运行环境
    env = 'production' if args.prod else args.env
    debug = args.debug or (env == 'development')
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 设置环境配置
    config_class = setup_environment(env)
    
    # 设置日志
    setup_logging(
        log_level=args.log_level,
        log_file=config_class.LOG_FILE if hasattr(config_class, 'LOG_FILE') else None
    )
    
    # 清理旧文件
    if args.clean:
        print("🧹 清理旧文件...")
        clean_old_files('downloads', max_age_days=7)
    
    # 打印启动信息
    print_startup_info(args.host, args.port, env, debug)
    
    try:
        # 启动应用
        app.run(
            host=args.host,
            port=args.port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()