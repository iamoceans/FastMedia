import re
import requests
import yt_dlp
import json
from urllib.parse import urlparse, parse_qs
from typing import Dict, Optional
import tempfile
import os

class XiaohongshuDownloader:
    def __init__(self, temp_dir: str = None):
        """初始化小红书下载器"""
        if temp_dir is None:
            # 使用固定的临时目录，而不是每次创建新的
            temp_dir = os.path.join(tempfile.gettempdir(), 'fastmedia_xiaohongshu_temp')
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    def clean_url(self, url: str) -> str:
        """清理小红书URL，保留必要的访问参数"""
        try:
            # 处理URL中的分享文本
            cleaned_url = url

            # 移除常见的分享文本前缀
            pattern = r'.*?(https?://[^\s]+)'
            match = re.search(pattern, url)
            if match:
                cleaned_url = match.group(1)

            parsed = urlparse(cleaned_url)

            # 小红书链接需要特定参数才能访问，必须保留这些参数
            path = parsed.path
            query_params = {}

            # 解析查询参数
            if parsed.query:
                for param in parsed.query.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        # 保留对访问至关重要的参数
                        if key in ['source', 'xhsshare', 'xsec_token', 'xsec_source']:
                            query_params[key] = value

            # 重建URL，保留必要的参数
            clean_url = f"https://www.xiaohongshu.com{path}"
            if query_params:
                query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
                clean_url += f"?{query_string}"

            return clean_url
        except Exception:
            return url

    def download_video(self, url: str) -> Dict:
        """下载小红书视频"""
        try:
            # 清理URL
            cleaned_url = self.clean_url(url)
            print(f"原始URL: {url}")
            print(f"清理后URL: {cleaned_url}")

            # 尝试多种方法获取视频信息
            info = None

            # 方法1: 使用标准yt-dlp方法
            info = self._try_standard_download(cleaned_url)

            # 方法2: 如果标准方法失败，尝试备用方法
            if info is None:
                info = self._try_alternative_download(cleaned_url)

            if info is None:
                raise Exception('无法获取视频信息，可能是网络问题或视频不存在')

            # 构建返回结果
            extractor = info.get('extractor', 'XiaoHongShu')
            title = info.get('title', 'XiaoHongShu_video')
            filename = f"{extractor}-{title}.mp4"
            actual_filepath = os.path.join(self.temp_dir, filename)

            return {
                'url': url,
                'processed_url': cleaned_url,
                'status': 'success',
                'title': title,
                'platform': 'xiaohongshu',
                'temp_filepath': actual_filepath,
                'download_filename': filename,
                'filesize': os.path.getsize(actual_filepath) if os.path.exists(actual_filepath) else 0,
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', '')
            }

        except Exception as e:
            return {
                'url': url,
                'status': 'error',
                'error': str(e),
                'filepath': None
            }

    def _try_standard_download(self, url: str) -> Optional[Dict]:
        """尝试标准yt-dlp下载方法"""
        try:
            print("尝试标准yt-dlp方法...")

            # 使用与测试脚本完全相同的配置
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'best/worst',
                'outtmpl': os.path.join(self.temp_dir, '%(extractor)s-%(title)s.%(ext)s'),
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.xiaohongshu.com/',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br'
                }
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 先获取信息
                info = ydl.extract_info(url, download=False)
                if info:
                    print(f"成功获取视频信息: {info.get('title', 'N/A')}")

                    # 然后下载
                    ydl.download([url])
                    print("视频下载完成")
                    return info
                else:
                    print("无法获取视频信息")
                    return None

        except Exception as e:
            print(f"标准方法失败: {str(e)}")
            return None

    def _try_alternative_download(self, url: str) -> Optional[Dict]:
        """尝试备用下载方法"""
        try:
            print("尝试备用下载方法...")

            # 尝试不同的格式选择
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'best',  # 只选择最佳格式
                'outtmpl': os.path.join(self.temp_dir, '%(extractor)s-%(title)s.%(ext)s'),
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                    'Referer': 'https://www.xiaohongshu.com/',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br'
                }
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    print(f"备用方法成功获取视频信息: {info.get('title', 'N/A')}")
                    ydl.download([url])
                    print("备用方法视频下载完成")
                    return info
                else:
                    print("备用方法无法获取视频信息")
                    return None

        except Exception as e:
            print(f"备用方法失败: {str(e)}")
            return None

    def cleanup_temp_file(self, filepath: str):
        """清理临时文件"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"已清理临时文件: {filepath}")
        except Exception as e:
            print(f"清理临时文件失败: {str(e)}")

    def get_temp_file_info(self, filepath: str) -> dict:
        """获取临时文件信息"""
        try:
            if os.path.exists(filepath):
                stat = os.stat(filepath)
                return {
                    'exists': True,
                    'size': stat.st_size,
                    'modified_time': stat.st_mtime
                }
            else:
                return {'exists': False}
        except Exception as e:
            return {'exists': False, 'error': str(e)}