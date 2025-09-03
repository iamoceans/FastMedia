#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastMedia 工具函数模块
包含日志设置和文件清理等功能
"""

import os
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta

def setup_logging(log_level='INFO', log_file=None):
    """
    设置日志配置
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日志文件路径，如果为None则只输出到控制台
    """
    # 创建日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 设置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，创建文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        logger.addHandler(file_handler)
    
    logging.info(f"日志系统已初始化，级别: {log_level}")
    if log_file:
        logging.info(f"日志文件: {log_file}")

def clean_old_files(directory, max_age_days=7):
    """
    清理指定目录中超过指定天数的旧文件
    
    Args:
        directory: 要清理的目录路径
        max_age_days: 最大保留天数，默认为7天
    """
    if not os.path.exists(directory):
        logging.warning(f"目录不存在: {directory}")
        return
    
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60
    removed_count = 0
    total_size = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # 获取文件修改时间
                file_mtime = os.path.getmtime(file_path)
                file_age = current_time - file_mtime
                
                if file_age > max_age_seconds:
                    # 删除旧文件
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    removed_count += 1
                    total_size += file_size
                    logging.debug(f"已删除旧文件: {file_path} (年龄: {file_age/86400:.1f}天)")
                    
            except (OSError, PermissionError) as e:
                logging.warning(f"无法删除文件 {file_path}: {e}")
    
    if removed_count > 0:
        size_mb = total_size / (1024 * 1024)
        logging.info(f"清理完成: 删除了 {removed_count} 个文件，释放 {size_mb:.2f} MB 空间")
    else:
        logging.info(f"目录 {directory} 中没有需要清理的旧文件")

def create_directories(directories):
    """
    创建必要的目录
    
    Args:
        directories: 目录路径列表
    """
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logging.debug(f"确保目录存在: {directory}")

def get_file_size(file_path):
    """
    获取文件大小（人类可读格式）
    
    Args:
        file_path: 文件路径
    
    Returns:
        str: 格式化的文件大小
    """
    if not os.path.exists(file_path):
        return "0 Bytes"
    
    size = os.path.getsize(file_path)
    
    for unit in ['Bytes', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    
    return f"{size:.2f} TB"

if __name__ == "__main__":
    # 测试代码
    setup_logging('DEBUG')
    logging.info("Utils 模块测试")
    print("文件大小示例:", get_file_size(__file__))