import os
import requests
import re
from urllib.parse import urlparse
import yt_dlp
import subprocess
import json
from typing import List, Dict
from .kuaishou_downloader import KuaishouDownloader
from .xiaohongshu_downloader import XiaohongshuDownloader

# Debug logging
def debug_log(message):
    """Write debug messages to a file"""
    with open('debug_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"{message}\n")

def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除或替换Windows文件系统不支持的字符
    """
    if not filename:
        return filename

    # Windows文件系统不允许的字符: < > : " | ? * 以及控制字符
    # 替换为下划线
    invalid_chars = r'[<>:"|?*\x00-\x1f]'
    filename = re.sub(invalid_chars, '_', filename)

    # 移除连续的空格和点
    filename = re.sub(r'[.\s]+', '_', filename)

    # 移除开头和结尾的空格和点
    filename = filename.strip(' .')

    # 限制文件名长度（Windows通常限制为260个字符，但路径也会占用长度）
    if len(filename) > 100:
        filename = filename[:100]

    return filename

class VideoDownloader:
    def __init__(self):
        # 使用固定的临时目录存储下载的文件，避免Flask重启时路径失效
        import tempfile
        import os

        # 使用固定的临时目录，而不是每次创建新的
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'fastmedia_temp')
        os.makedirs(self.temp_dir, exist_ok=True)

        self.download_dir = 'downloads/videos'  # 保留作为默认下载目录
        os.makedirs(self.download_dir, exist_ok=True)

        # 初始化快手和小红书下载器
        self.kuaishou_downloader = KuaishouDownloader(self.temp_dir)
        self.xiaohongshu_downloader = XiaohongshuDownloader(self.temp_dir)

        # yt-dlp基础配置
        self.ydl_opts = {
            'outtmpl': os.path.join(self.temp_dir, '%(extractor)s-%(title)s.%(ext)s'),
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
            debug_log(f"DEBUG: download_single called with URL: {url}")
            # 预处理URL（处理短链接等）
            processed_url = self.preprocess_url(url)
            debug_log(f"DEBUG: processed_url: {processed_url}")

            # 检测平台
            platform = self.detect_platform(processed_url)
            debug_log(f"DEBUG: detected platform: {platform}")

            if platform == 'unsupported':
                raise Exception(f'不支持的平台: {url}')
            elif platform == 'kuaishou':
                # 使用专门的快手下载器
                return self.kuaishou_downloader.download_video(processed_url)
            elif platform == 'xiaohongshu':
                # 使用专门的小红书下载器
                return self.xiaohongshu_downloader.download_video(processed_url)
            
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
                opts = self.ydl_opts.copy()
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
            elif platform == 'xiaohongshu':
                # 小红书特殊配置 - 增强版本，添加更多浏览器模拟头
                opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'format': 'best/worst',
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.xiaohongshu.com/',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache',
                        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                        'Sec-Ch-Ua-Mobile': '?0',
                        'Sec-Ch-Ua-Platform': '"Windows"',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                        'Upgrade-Insecure-Requests': '1'
                    }
                }
                debug_log(f"DEBUG: 小红书配置 - 使用增强的浏览器模拟配置: {opts}")
            else:
                # 其他平台（YouTube等）使用默认配置，但需要处理文件名编码问题
                opts = self.ydl_opts.copy()

                # 针对YouTube的文件名编码问题，使用ASCII文件名
                if platform in ['youtube', 'youtu.be']:
                    # 创建一个自定义的outtmpl来处理文件名编码问题
                    # 使用时间戳和ID来避免中文字符导致的文件系统问题
                    opts['outtmpl'] = os.path.join(self.temp_dir, 'youtube-%(id)s-%(timestamp)s.%(ext)s')
                    debug_log(f"DEBUG: YouTube使用特殊文件名模板: {opts['outtmpl']}")
            
            # 使用yt-dlp下载
            try:
                debug_log(f"DEBUG: 开始提取小红书视频信息 - URL: {processed_url}")
                debug_log(f"DEBUG: 使用的yt-dlp配置: {opts}")

                # 针对小红书使用与测试脚本完全相同的方式
                if platform == 'xiaohongshu':
                    debug_log(f"DEBUG: 使用与测试脚本完全相同的方式处理小红书")
                    try:
                        # 完全复制测试脚本的逻辑
                        xiaohongshu_opts = {
                            'quiet': True,
                            'no_warnings': True,
                            'format': 'best/worst',
                            'http_headers': {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                                'Referer': 'https://www.xiaohongshu.com/',
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                                'Accept-Encoding': 'gzip, deflate, br'
                            }
                        }

                        debug_log(f"DEBUG: 小红书测试脚本配置: {xiaohongshu_opts}")

                        with yt_dlp.YoutubeDL(xiaohongshu_opts) as ydl:
                            debug_log(f"DEBUG: 开始使用与测试脚本相同的方式提取信息")
                            info = ydl.extract_info(processed_url, download=False)
                            debug_log(f"DEBUG: 小红书测试脚本方式获取到的信息: {info}")

                        if info is None:
                            debug_log(f"DEBUG: 小红书测试脚本方式返回None")
                            raise Exception('无法获取视频信息，可能是网络问题或视频不存在')

                    except Exception as e:
                        debug_log(f"DEBUG: 小红书测试脚本方式失败: {str(e)}")
                        raise Exception(f'小红书视频处理失败: {str(e)}')
                else:
                    # 其他平台使用原有的yt-dlp Python API
                    debug_log(f"DEBUG: 即将创建YoutubeDL实例")
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        debug_log(f"DEBUG: YoutubeDL实例创建成功，开始提取信息")
                        # 获取视频信息
                        info = ydl.extract_info(processed_url, download=False)
                        debug_log(f"DEBUG: 提取到的视频信息: {info}")

                        # 检查info是否为None
                        if info is None:
                            debug_log(f"DEBUG: 视频信息提取失败 - info为None")
                            raise Exception('无法获取视频信息，可能是网络问题或视频不存在')

                    # 下载视频
                if platform == 'xiaohongshu':
                    # 小红书使用subprocess下载
                    debug_log(f"DEBUG: 使用subprocess下载小红书视频")
                    download_opts = opts.copy()
                    download_opts['outtmpl'] = os.path.join(self.temp_dir, '%(extractor)s-%(title)s.%(ext)s')

                    # 构建下载命令
                    cmd = [
                        'python', '-m', 'yt_dlp',
                        '--quiet', '--no-warnings',
                        '--format', 'best/worst',
                        '--output', os.path.join(self.temp_dir, '%(extractor)s-%(title)s.%(ext)s'),
                        processed_url
                    ]
                    debug_log(f"DEBUG: 小红书下载命令: {' '.join(cmd)}")

                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                        debug_log(f"DEBUG: 小红书下载返回码: {result.returncode}")
                        debug_log(f"DEBUG: 小红书下载输出: {result.stdout}")
                        debug_log(f"DEBUG: 小红书下载错误: {result.stderr}")

                        if result.returncode != 0:
                            error_msg = result.stderr.strip() if result.stderr else '下载失败'
                            raise Exception(f'小红书视频下载失败: {error_msg}')

                        debug_log(f"DEBUG: 小红书视频下载完成")
                    except subprocess.TimeoutExpired:
                        raise Exception('小红书视频下载超时，请稍后重试')
                else:
                    # 其他平台的下载逻辑
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
                original_title = info.get('title', 'unknown')

                # 针对YouTube使用特殊文件名处理
                if platform in ['youtube', 'youtu.be']:
                    # YouTube使用的是 youtube-%(id)s-%(timestamp)s.%(ext)s 格式
                    # 这与outtmpl设置保持一致
                    video_id = info.get('id', 'unknown')
                    import time
                    timestamp = int(time.time())
                    extension = info.get('ext', 'mp4')
                    filename = f"youtube-{video_id}-{timestamp}.{extension}"
                    # 对于下载文件名，使用清理过的原始标题
                    download_filename = f"youtube-{sanitize_filename(original_title)}.{extension}"
                else:
                    # 其他平台使用原有逻辑，但是要使用sanitize_filename清理标题
                    filename = f"{extractor}-{sanitize_filename(original_title)}.{info.get('ext', 'mp4')}"
                    download_filename = filename

                # 实际下载的文件路径在临时目录中
                actual_filepath = os.path.join(self.temp_dir, filename)

                return {
                    'url': url,  # 返回原始URL
                    'processed_url': processed_url,  # 返回处理后的URL
                    'status': 'success',
                    'title': info.get('title', 'unknown'),
                    'platform': platform,
                    'temp_filepath': actual_filepath,  # 临时文件路径
                    'download_filename': download_filename,  # 建议的文件名
                    'filesize': os.path.getsize(actual_filepath) if os.path.exists(actual_filepath) else 0,
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', '')
                }

            except Exception as e:
                # 提供更友好的错误信息
                error_msg = str(e)
                debug_log(f"DEBUG: yt-dlp异常: {error_msg}")
                if 'NoneType' in error_msg and 'get' in error_msg:
                    raise Exception('B站视频信息获取失败，可能是网络问题或B站API限制')
                elif '无法获取视频信息' in error_msg:
                    raise Exception('无法获取视频信息，可能是网络问题或视频不存在')
                else:
                    raise Exception(f'下载失败: {error_msg}')
        except Exception as e:
            # 捕获 download_single 方法的其他错误
            debug_log(f"DEBUG: download_single异常: {str(e)}")
            raise Exception(f'视频下载失败: {str(e)}')

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
        elif 'xiaohongshu.com' in domain or 'xhslink.com' in domain:
            return 'xiaohongshu'
        else:
            return 'unsupported'

    def preprocess_url(self, url: str) -> str:
        """预处理URL，处理短链接重定向和清理参数等"""
        try:
            # 处理URL中的分享文本（如抖音、小红书等）
            cleaned_url = url

            # 移除常见的分享文本前缀
            import re
            # 匹配类似 "4 【AUG自述 - 武器大师 | 小红书 - 你的生活兴趣社区】 😆 HIbzka9uzjpGbxB 😆 https://www.xiaohongshu.com/..."
            pattern = r'.*?(https?://[^\s]+)'
            match = re.search(pattern, url)
            if match:
                cleaned_url = match.group(1)

            parsed = urlparse(cleaned_url)

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

            # 处理小红书链接，保留必要的访问参数
            elif 'xiaohongshu.com' in parsed.netloc.lower():
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

            return cleaned_url
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