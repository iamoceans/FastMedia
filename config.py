import os
from pathlib import Path

class Config:
    """基础配置类"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
    
    # 文件上传配置
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    
    # 下载目录配置
    DOWNLOAD_BASE_DIR = 'downloads'
    VIDEO_DOWNLOAD_DIR = os.path.join(DOWNLOAD_BASE_DIR, 'videos')
    BGM_DOWNLOAD_DIR = os.path.join(DOWNLOAD_BASE_DIR, 'bgm')
    TEXT_DOWNLOAD_DIR = os.path.join(DOWNLOAD_BASE_DIR, 'texts')
    WATERMARK_DOWNLOAD_DIR = os.path.join(DOWNLOAD_BASE_DIR, 'watermarked')
    THUMBNAIL_DOWNLOAD_DIR = os.path.join(DOWNLOAD_BASE_DIR, 'thumbnails')
    
    # 视频处理配置
    MAX_VIDEO_RESOLUTION = '720p'  # 限制视频分辨率以节省空间
    VIDEO_QUALITY = 'best[height<=720]'
    AUDIO_QUALITY = '192'  # kbps
    
    # 水印配置
    DEFAULT_WATERMARK_POSITION = 'bottom-right'
    DEFAULT_WATERMARK_OPACITY = 0.8
    DEFAULT_WATERMARK_SCALE = 0.1
    DEFAULT_FONT_SIZE = 24
    
    # 缩略图配置
    THUMBNAIL_SIZE = (320, 180)  # 16:9 比例
    THUMBNAIL_QUALITY = 90
    
    # 并发处理配置
    MAX_CONCURRENT_DOWNLOADS = 3
    DOWNLOAD_TIMEOUT = 300  # 5分钟
    
    # 缓存配置
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/fastmedia.log'
    
    # 支持的平台
    SUPPORTED_PLATFORMS = {
        'douyin': ['douyin.com'],
        'tiktok': ['tiktok.com'],
        'bilibili': ['bilibili.com', 'b23.tv'],
        'youtube': ['youtube.com', 'youtu.be'],
        'twitter': ['twitter.com', 'x.com'],
        'kuaishou': ['kuaishou.com']
    }
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 创建必要的目录
        directories = [
            Config.UPLOAD_FOLDER,
            Config.DOWNLOAD_BASE_DIR,
            Config.VIDEO_DOWNLOAD_DIR,
            Config.BGM_DOWNLOAD_DIR,
            Config.TEXT_DOWNLOAD_DIR,
            Config.WATERMARK_DOWNLOAD_DIR,
            Config.THUMBNAIL_DOWNLOAD_DIR,
            'logs'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    
class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
    # 生产环境安全配置
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    WTF_CSRF_ENABLED = False

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}