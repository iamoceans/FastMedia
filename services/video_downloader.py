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

        # yt-dlp基础配置
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

    def get_bilibili_opts(self, base_opts: dict = None, download_mode: bool = True) -> dict:
        """获取B站专用的yt-dlp配置"""
        if base_opts is None:
            base_opts = {}

        bilibili_opts = base_opts.copy()
        bilibili_opts.update({
            'noplaylist': True,     # 不下载播放列表，只下载单个视频
            'playlistend': 1,       # 如果是播放列表，只下载第一个视频
            'ignoreerrors': True,   # 忽略错误继续处理
            'no_warnings': True,    # 不显示警告
            'retries': 3,           # 重试次数
            'socket_timeout': 30,   # socket超时时间
            'fragment_retries': 5,  # 片段重试次数
            'skip_unavailable_fragments': True,  # 跳过不可用的片段
        })

        # 如果是下载模式，添加额外的配置
        if download_mode:
            bilibili_opts.update({
                'format': '30032+30232/30016+30232/best[height<=480]+bestaudio/best',  # 选择480p视频+音频或最佳组合
                'writeinfojson': False,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'writethumbnail': False,
            })

        return bilibili_opts
    
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
            # 预处理URL（处理短链接等）
            processed_url = self.preprocess_url(url)

            # 检测平台
            platform = self.detect_platform(processed_url)

            if platform == 'unsupported':
                raise Exception(f'不支持的平台: {url}')
            elif platform == 'kuaishou':
                # 使用专门的快手下载器
                return self.kuaishou_downloader.download_video(processed_url)
            
            # 根据平台调整配置
            if platform == 'bilibili':
                # 使用统一的B站配置
                opts = self.get_bilibili_opts(self.ydl_opts, download_mode=True)
            elif platform == 'douyin/tiktok':
                # TikTok特殊配置
                opts = self.ydl_opts.copy()
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
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    # 获取视频信息
                    info = ydl.extract_info(processed_url, download=False)

                    # 检查info是否为None
                    if info is None:
                        raise Exception('无法获取视频信息，可能是网络问题或视频不存在')

                    title = info.get('title', 'unknown')

                    # 针对B站特殊处理
                    if platform == 'bilibili':
                        try:
                            # 下载视频
                            ydl.download([processed_url])
                        except Exception as download_error:
                            error_msg = str(download_error).lower()
                            print(f"B站下载错误详情: {str(download_error)}")
                            
                            if 'json' in error_msg or 'parse' in error_msg:
                                raise Exception('B站API限制：该视频暂时无法下载，请稍后重试或尝试其他视频')
                            elif 'region' in error_msg or 'geoblock' in error_msg:
                                raise Exception('该视频有地区限制，无法在当前地区下载')
                            elif 'private' in error_msg or 'permission' in error_msg:
                                raise Exception('该视频为私人视频或需要权限才能下载')
                            elif 'playlist' in error_msg:
                                raise Exception('B站系列视频处理失败，请尝试视频的具体分集链接')
                            elif 'timeout' in error_msg or 'network' in error_msg:
                                raise Exception('网络超时，请检查网络连接后重试')
                            elif 'unavailable' in error_msg:
                                raise Exception('该视频不可用，可能已被删除或设为私密')
                            else:
                                raise Exception(f'B站下载失败: {str(download_error)}')
                    else:
                        # 其他平台正常下载
                        ydl.download([processed_url])

                    # 构建文件路径（包含平台信息）
                    extractor = info.get('extractor', platform.replace('/', '_'))
                    filename = f"{extractor}-{title}.{info.get('ext', 'mp4')}"
                    filepath = os.path.join(self.download_dir, filename)

                    return {
                        'url': url,  # 返回原始URL
                        'processed_url': processed_url,  # 返回处理后的URL
                        'status': 'success',
                        'title': title,
                        'platform': platform,
                        'filepath': filepath,
                        'filesize': os.path.getsize(filepath) if os.path.exists(filepath) else 0,
                        'duration': info.get('duration', 0),
                        'uploader': info.get('uploader', '')
                    }

            except Exception as e:
                # 提供更友好的错误信息
                error_msg = str(e)
                if 'NoneType' in error_msg and 'get' in error_msg:
                    raise Exception('B站视频信息获取失败，可能是网络问题或B站API限制')
                elif '无法获取视频信息' in error_msg:
                    raise Exception('无法获取视频信息，可能是网络问题或视频不存在')
                else:
                    raise Exception(f'下载失败: {error_msg}')
        except Exception as e:
            # 捕获 download_single 方法的其他错误
            raise Exception(f'视频下载失败: {str(e)}')

    def detect_platform(self, url: str) -> str:
        """检测视频平台"""
        domain = urlparse(url).netloc.lower()

        if 'douyin.com' in domain or 'tiktok.com' in domain:
            return 'douyin/tiktok'
        elif 'bilibili.com' in domain or 'b23.tv' in domain:
            return 'bilibili'
        elif 'youtube.com' in domain or 'youtu.be' in domain:
            return 'youtube'
        elif 'twitter.com' in domain or 'x.com' in domain:
            return 'twitter'
        elif 'kuaishou.com' in domain:
            return 'kuaishou'
        else:
            return 'unsupported'

    def preprocess_url(self, url: str) -> str:
        """预处理URL，处理短链接重定向和清理参数等"""
        try:
            parsed = urlparse(url)

            # 处理B站链接
            if 'bilibili.com' in parsed.netloc.lower() or 'b23.tv' in parsed.netloc.lower():
                # 清理B站URL，移除不必要的跟踪参数
                path = parsed.path
                query_params = {}

                # 保留重要的查询参数
                if parsed.query:
                    for param in ['p', 't', 'dm']:  # 保留页码、时间戳、弹幕开关等
                        if param in parsed.query:
                            query_params[param] = parsed.query.split(f'{param}=')[1].split('&')[0]

                # 重建干净的URL
                clean_url = f"https://www.bilibili.com{path}"
                if query_params:
                    query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
                    clean_url += f"?{query_string}"

                # 处理短链接重定向
                if 'b23.tv' in parsed.netloc.lower():
                    try:
                        response = requests.head(url, allow_redirects=True, timeout=10,
                                               headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
                        if response.status_code == 200 and 'bilibili.com' in response.url:
                            return response.url
                    except Exception:
                        pass

                return clean_url

            # 处理YouTube短链接
            elif 'youtu.be' in parsed.netloc.lower():
                try:
                    response = requests.head(url, allow_redirects=True, timeout=10,
                                           headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
                    if response.status_code == 200:
                        return response.url
                except Exception:
                    pass

            return url
        except Exception:
            return url

    def get_video_info(self, url: str) -> Dict:
        """获取视频信息而不下载"""
        try:
            # 预处理URL
            processed_url = self.preprocess_url(url)
            platform = self.detect_platform(processed_url)

            # 针对B站使用特殊配置
            if platform == 'bilibili':
                opts = self.get_bilibili_opts({'quiet': True}, download_mode=False)
                try:
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        info = ydl.extract_info(processed_url, download=False)
                except Exception as e:
                    # 如果失败，尝试使用更宽松的配置
                    print(f"B站信息获取失败，尝试宽松配置: {str(e)}")
                    relaxed_opts = self.get_bilibili_opts({'quiet': False, 'ignoreerrors': True}, download_mode=False)
                    with yt_dlp.YoutubeDL(relaxed_opts) as ydl:
                        info = ydl.extract_info(processed_url, download=False)
            else:
                # 其他平台使用默认配置
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(processed_url, download=False)

            if info is None:
                raise Exception('无法获取视频信息')

            return {
                'title': info.get('title', ''),
                'description': info.get('description', ''),
                'duration': info.get('duration', 0),
                'view_count': info.get('view_count', 0),
                'uploader': info.get('uploader', ''),
                'upload_date': info.get('upload_date', ''),
                'thumbnail': info.get('thumbnail', ''),
                'platform': platform,
                'original_url': url,
                'processed_url': processed_url
            }
        except Exception as e:
            raise Exception(f'获取视频信息失败: {str(e)}')