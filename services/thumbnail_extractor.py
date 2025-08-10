import os
import yt_dlp
from moviepy.editor import VideoFileClip
from PIL import Image
from typing import List, Dict
import tempfile
import requests

class ThumbnailExtractor:
    def __init__(self):
        self.output_dir = 'downloads/thumbnails'
        self.temp_dir = tempfile.gettempdir()
        os.makedirs(self.output_dir, exist_ok=True)
        
        # yt-dlp配置
        self.ydl_opts = {
            'outtmpl': os.path.join(self.temp_dir, '%(title)s.%(ext)s'),
            'format': 'best[height<=720]',
            'writeinfojson': False,
        }
    
    def extract_batch(self, urls: List[str], timestamp: float = 0) -> List[Dict]:
        """批量提取缩略图"""
        results = []
        
        for url in urls:
            try:
                result = self.extract_single(url, timestamp)
                results.append(result)
            except Exception as e:
                results.append({
                    'url': url,
                    'status': 'error',
                    'error': str(e),
                    'filepath': None
                })
        
        return results
    
    def extract_single(self, url: str, timestamp: float = 0) -> Dict:
        """提取单个视频的缩略图"""
        temp_video_path = None
        try:
            # 首先尝试获取视频信息和原始缩略图
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown')
                thumbnail_url = info.get('thumbnail')
                duration = info.get('duration', 0)
            
            # 如果请求的时间戳超过视频长度，使用视频长度的一半
            if timestamp > duration:
                timestamp = duration / 2 if duration > 0 else 0
            
            output_filename = f"{self.sanitize_filename(title)}_thumbnail.jpg"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # 如果时间戳为0且有原始缩略图，优先下载原始缩略图
            if timestamp == 0 and thumbnail_url:
                try:
                    self.download_original_thumbnail(thumbnail_url, output_path)
                    return {
                        'url': url,
                        'status': 'success',
                        'title': title,
                        'filepath': output_path,
                        'filesize': os.path.getsize(output_path),
                        'timestamp': 0,
                        'method': 'original_thumbnail'
                    }
                except:
                    # 如果下载原始缩略图失败，继续使用视频帧提取
                    pass
            
            # 下载视频并提取帧
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([url])
                temp_video_path = os.path.join(self.temp_dir, f"{title}.{info.get('ext', 'mp4')}")
            
            # 从视频中提取帧
            self.extract_frame_from_video(temp_video_path, output_path, timestamp)
            
            return {
                'url': url,
                'status': 'success',
                'title': title,
                'filepath': output_path,
                'filesize': os.path.getsize(output_path),
                'timestamp': timestamp,
                'method': 'video_frame'
            }
            
        except Exception as e:
            raise Exception(f'缩略图提取失败: {str(e)}')
        
        finally:
            # 清理临时文件
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                except:
                    pass
    
    def download_original_thumbnail(self, thumbnail_url: str, output_path: str):
        """下载原始缩略图"""
        try:
            response = requests.get(thumbnail_url, timeout=10)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            # 验证图片是否有效
            with Image.open(output_path) as img:
                img.verify()
                
        except Exception as e:
            raise Exception(f'原始缩略图下载失败: {str(e)}')
    
    def extract_frame_from_video(self, video_path: str, output_path: str, timestamp: float = 0):
        """从视频中提取指定时间的帧"""
        try:
            if not os.path.exists(video_path):
                raise Exception('视频文件不存在')
            
            # 使用moviepy提取帧
            video = VideoFileClip(video_path)
            
            # 确保时间戳在有效范围内
            if timestamp > video.duration:
                timestamp = video.duration / 2
            
            # 提取帧
            frame = video.get_frame(timestamp)
            
            # 转换为PIL图像并保存
            img = Image.fromarray(frame)
            img.save(output_path, 'JPEG', quality=90)
            
            # 清理资源
            video.close()
            
        except Exception as e:
            raise Exception(f'视频帧提取失败: {str(e)}')
    
    def extract_multiple_frames(self, url: str, timestamps: List[float]) -> List[Dict]:
        """从单个视频提取多个时间点的帧"""
        temp_video_path = None
        results = []
        
        try:
            # 下载视频
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown')
                duration = info.get('duration', 0)
                
                ydl.download([url])
                temp_video_path = os.path.join(self.temp_dir, f"{title}.{info.get('ext', 'mp4')}")
            
            # 为每个时间戳提取帧
            for i, timestamp in enumerate(timestamps):
                try:
                    # 确保时间戳在有效范围内
                    if timestamp > duration:
                        timestamp = duration / 2 if duration > 0 else 0
                    
                    output_filename = f"{self.sanitize_filename(title)}_frame_{i+1}_{int(timestamp)}s.jpg"
                    output_path = os.path.join(self.output_dir, output_filename)
                    
                    self.extract_frame_from_video(temp_video_path, output_path, timestamp)
                    
                    results.append({
                        'timestamp': timestamp,
                        'status': 'success',
                        'filepath': output_path,
                        'filesize': os.path.getsize(output_path)
                    })
                    
                except Exception as e:
                    results.append({
                        'timestamp': timestamp,
                        'status': 'error',
                        'error': str(e),
                        'filepath': None
                    })
            
            return results
            
        except Exception as e:
            raise Exception(f'多帧提取失败: {str(e)}')
        
        finally:
            # 清理临时文件
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                except:
                    pass
    
    def extract_from_local_video(self, video_path: str, output_path: str = None, timestamp: float = 0) -> Dict:
        """从本地视频文件提取缩略图"""
        try:
            if not os.path.exists(video_path):
                raise Exception('视频文件不存在')
            
            if output_path is None:
                filename = os.path.splitext(os.path.basename(video_path))[0]
                output_path = os.path.join(self.output_dir, f"{filename}_thumbnail.jpg")
            
            self.extract_frame_from_video(video_path, output_path, timestamp)
            
            return {
                'status': 'success',
                'filepath': output_path,
                'filesize': os.path.getsize(output_path),
                'timestamp': timestamp
            }
            
        except Exception as e:
            raise Exception(f'本地视频缩略图提取失败: {str(e)}')
    
    def create_thumbnail_grid(self, video_path: str, output_path: str, 
                            grid_size: tuple = (3, 3), thumbnail_size: tuple = (160, 90)) -> Dict:
        """创建视频缩略图网格"""
        try:
            if not os.path.exists(video_path):
                raise Exception('视频文件不存在')
            
            video = VideoFileClip(video_path)
            duration = video.duration
            
            rows, cols = grid_size
            total_thumbnails = rows * cols
            
            # 计算时间间隔
            time_interval = duration / (total_thumbnails + 1)
            
            # 创建网格图像
            grid_width = cols * thumbnail_size[0]
            grid_height = rows * thumbnail_size[1]
            grid_image = Image.new('RGB', (grid_width, grid_height), 'black')
            
            # 提取并放置缩略图
            for i in range(total_thumbnails):
                timestamp = time_interval * (i + 1)
                
                # 提取帧
                frame = video.get_frame(timestamp)
                thumbnail = Image.fromarray(frame)
                thumbnail = thumbnail.resize(thumbnail_size, Image.Resampling.LANCZOS)
                
                # 计算位置
                row = i // cols
                col = i % cols
                x = col * thumbnail_size[0]
                y = row * thumbnail_size[1]
                
                # 粘贴到网格
                grid_image.paste(thumbnail, (x, y))
            
            # 保存网格图像
            grid_image.save(output_path, 'JPEG', quality=90)
            
            # 清理资源
            video.close()
            
            return {
                'status': 'success',
                'filepath': output_path,
                'filesize': os.path.getsize(output_path),
                'grid_size': grid_size,
                'thumbnail_count': total_thumbnails
            }
            
        except Exception as e:
            raise Exception(f'缩略图网格创建失败: {str(e)}')
    
    def sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        if len(filename) > 100:
            filename = filename[:100]
        return filename