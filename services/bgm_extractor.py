import os
import yt_dlp
from typing import List, Dict
import tempfile
import shutil
from .kuaishou_downloader import KuaishouDownloader

class BGMExtractor:
    def __init__(self):
        # 使用临时目录存储BGM文件
        self.temp_dir = tempfile.mkdtemp(prefix='fastmedia_bgm_')
        self.output_dir = 'downloads/bgm'  # 保留作为默认目录
        os.makedirs(self.output_dir, exist_ok=True)

        # 初始化快手下载器
        self.kuaishou_downloader = KuaishouDownloader('downloads/videos')

        # yt-dlp配置，直接提取音频
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.temp_dir, '%(extractor)s-%(title)s_bgm.%(ext)s'),
            'writeinfojson': False,
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': '192',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    
    def extract_batch(self, urls: List[str]) -> List[Dict]:
        """批量提取BGM"""
        results = []
        
        for url in urls:
            try:
                result = self.extract_single(url)
                results.append(result)
            except Exception as e:
                results.append({
                    'url': url,
                    'status': 'error',
                    'error': str(e),
                    'filepath': None
                })
        
        return results
    
    def extract_single(self, url: str) -> Dict:
        """提取单个视频的BGM"""
        try:
            # 检测平台
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.lower()
            if 'kuaishou.com' in domain:
                # 使用专门的快手下载器进行BGM提取
                return self.kuaishou_downloader.extract_bgm(url)
            
            # 使用yt-dlp直接提取音频
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # 获取视频信息
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown')
                
                # 清理文件名
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                extractor = info.get('extractor', 'unknown')
                output_filename = f"{extractor}-{safe_title}_bgm.mp3"
                output_path = os.path.join(self.output_dir, output_filename)
                
                # 临时修改yt-dlp配置以确保输出mp3格式
                temp_opts = self.ydl_opts.copy()
                temp_opts['outtmpl'] = os.path.join(self.temp_dir, f"{extractor}-{safe_title}_bgm.%(ext)s")

                # 下载并提取音频
                with yt_dlp.YoutubeDL(temp_opts) as temp_ydl:
                    temp_ydl.download([url])

                # 检查文件是否存在（可能有不同的扩展名）
                base_name = f"{extractor}-{safe_title}_bgm"
                temp_output_path = None

                for ext in ['.mp3', '.m4a', '.webm', '.ogg']:
                    potential_path = os.path.join(self.temp_dir, base_name + ext)
                    if os.path.exists(potential_path):
                        if ext != '.mp3':
                            # 重命名为mp3
                            final_path = os.path.join(self.temp_dir, base_name + '.mp3')
                            shutil.move(potential_path, final_path)
                            temp_output_path = final_path
                        else:
                            temp_output_path = potential_path
                        break

                # 如果没有找到文件，检查是否有其他格式的文件
                if temp_output_path is None or not os.path.exists(temp_output_path):
                    # 查找所有可能的文件
                    import glob
                    pattern = os.path.join(self.temp_dir, f"{extractor}-{safe_title}_bgm.*")
                    files = glob.glob(pattern)
                    if files:
                        # 使用第一个找到的文件
                        found_file = files[0]
                        if not found_file.endswith('.mp3'):
                            # 重命名为mp3
                            final_path = os.path.join(self.temp_dir, base_name + '.mp3')
                            shutil.move(found_file, final_path)
                            temp_output_path = final_path
                        else:
                            temp_output_path = found_file

                # 构建建议的文件名
                download_filename = f"{extractor}-{safe_title}_bgm.mp3"

                return {
                    'url': url,
                    'status': 'success',
                    'title': title,
                    'temp_filepath': temp_output_path if temp_output_path and os.path.exists(temp_output_path) else None,
                    'download_filename': download_filename,
                    'filesize': os.path.getsize(temp_output_path) if temp_output_path and os.path.exists(temp_output_path) else 0,
                    'duration': info.get('duration', 0)
                }
                
        except Exception as e:
            raise Exception(f'BGM提取失败: {str(e)}')
    

    
    def extract_from_local_video(self, video_path: str, output_path: str = None) -> Dict:
        """从本地视频文件提取BGM"""
        try:
            if not os.path.exists(video_path):
                raise Exception('视频文件不存在')
            
            # 由于避免ffmpeg依赖，暂不支持本地视频BGM提取
            # 建议用户使用在线视频URL进行BGM提取
            raise Exception('暂不支持本地视频BGM提取，请使用在线视频URL进行BGM提取功能')
            
        except Exception as e:
            raise Exception(f'本地视频BGM提取失败: {str(e)}')

    def cleanup_temp_file(self, filepath: str):
        """清理临时文件"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"已清理BGM临时文件: {filepath}")
        except Exception as e:
            print(f"清理BGM临时文件失败: {str(e)}")

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