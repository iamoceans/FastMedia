import os
import requests
import re
from urllib.parse import urlparse
import yt_dlp
from typing import List, Dict
from .kuaishou_downloader import KuaishouDownloader

class VideoDownloader:
    def __init__(self):
        self.download_dir = 'downloads/videos'
        os.makedirs(self.download_dir, exist_ok=True)
        
        # 初始化快手下载器
        self.kuaishou_downloader = KuaishouDownloader(self.download_dir)
        
        # yt-dlp配置
        self.ydl_opts = {
            'outtmpl': os.path.join(self.download_dir, '%(extractor)s-%(title)s.%(ext)s'),
            'format': 'best[height<=720]/best[height<=480]/best/worst',  # 更灵活的格式选择
            'writeinfojson': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': False,
            'no_warnings': False,
            'extractflat': False,
            'writethumbnail': False,
            'writeinfojson': False,
            'cookiefile': None,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    
    def download_batch(self, urls: List[str]) -> List[Dict]:
        """批量下载视频"""
        results = []
        
        for url in urls:
            try:
                result = self.download_single(url)
                results.append(result)
            except Exception as e:
                results.append({
                    'url': url,
                    'status': 'error',
                    'error': str(e),
                    'filepath': None
                })
        
        return results
    
    def download_single(self, url: str) -> Dict:
        """下载单个视频"""
        try:
            # 检测平台
            platform = self.detect_platform(url)
            
            if platform == 'unsupported':
                raise Exception(f'不支持的平台: {url}')
            elif platform == 'kuaishou':
                # 使用专门的快手下载器
                return self.kuaishou_downloader.download_video(url)
            
            # 根据平台调整配置
            opts = self.ydl_opts.copy()
            if platform == 'douyin/tiktok':
                # TikTok特殊配置
                opts['format'] = 'best/worst'
                opts['http_headers'] = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Referer': 'https://www.tiktok.com/'
                }
            elif platform == 'kuaishou':
                # 快手特殊配置
                opts['format'] = 'best/worst'
                opts['http_headers'] = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.kuaishou.com/',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br'
                }
                opts['extractor_args'] = {
                    'kuaishou': {
                        'api_hostname': 'www.kuaishou.com'
                    }
                }
                opts['cookiefile'] = None
                opts['ignoreerrors'] = True
            
            # 使用yt-dlp下载
            with yt_dlp.YoutubeDL(opts) as ydl:
                # 获取视频信息
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown')
                
                # 下载视频
                ydl.download([url])
                
                # 构建文件路径（包含平台信息）
                extractor = info.get('extractor', platform.replace('/', '_'))
                filename = f"{extractor}-{title}.{info.get('ext', 'mp4')}"
                filepath = os.path.join(self.download_dir, filename)
                
                return {
                    'url': url,
                    'status': 'success',
                    'title': title,
                    'platform': platform,
                    'filepath': filepath,
                    'filesize': os.path.getsize(filepath) if os.path.exists(filepath) else 0
                }
                
        except Exception as e:
            raise Exception(f'下载失败: {str(e)}')
    
    def detect_platform(self, url: str) -> str:
        """检测视频平台"""
        domain = urlparse(url).netloc.lower()
        
        if 'douyin.com' in domain or 'tiktok.com' in domain:
            return 'douyin/tiktok'
        elif 'bilibili.com' in domain:
            return 'bilibili'
        elif 'youtube.com' in domain or 'youtu.be' in domain:
            return 'youtube'
        elif 'twitter.com' in domain or 'x.com' in domain:
            return 'twitter'
        elif 'kuaishou.com' in domain:
            return 'kuaishou'
        else:
            return 'unsupported'
    
    def get_video_info(self, url: str) -> Dict:
        """获取视频信息而不下载"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', ''),
                    'description': info.get('description', ''),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'uploader': info.get('uploader', ''),
                    'upload_date': info.get('upload_date', ''),
                    'thumbnail': info.get('thumbnail', ''),
                    'platform': self.detect_platform(url)
                }
        except Exception as e:
            raise Exception(f'获取视频信息失败: {str(e)}')