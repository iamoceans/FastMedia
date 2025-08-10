import os
import yt_dlp
from moviepy.editor import VideoFileClip, TextClip, ImageClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict
import tempfile

class WatermarkAdder:
    def __init__(self):
        self.output_dir = 'downloads/watermarked'
        self.temp_dir = tempfile.gettempdir()
        os.makedirs(self.output_dir, exist_ok=True)
        
        # yt-dlp配置
        self.ydl_opts = {
            'outtmpl': os.path.join(self.temp_dir, '%(title)s.%(ext)s'),
            'format': 'best[height<=720]',
            'writeinfojson': False,
        }
    
    def add_watermark_batch(self, urls: List[str], watermark_text: str = None, watermark_image: str = None) -> List[Dict]:
        """批量添加水印"""
        results = []
        
        for url in urls:
            try:
                result = self.add_watermark_single(url, watermark_text, watermark_image)
                results.append(result)
            except Exception as e:
                results.append({
                    'url': url,
                    'status': 'error',
                    'error': str(e),
                    'filepath': None
                })
        
        return results
    
    def add_watermark_single(self, url: str, watermark_text: str = None, watermark_image: str = None) -> Dict:
        """为单个视频添加水印"""
        temp_video_path = None
        try:
            # 下载视频
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown')
                
                ydl.download([url])
                temp_video_path = os.path.join(self.temp_dir, f"{title}.{info.get('ext', 'mp4')}")
            
            # 添加水印
            output_filename = f"{self.sanitize_filename(title)}_watermarked.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            if watermark_text:
                self.add_text_watermark(temp_video_path, output_path, watermark_text)
            elif watermark_image:
                self.add_image_watermark(temp_video_path, output_path, watermark_image)
            else:
                raise Exception('请提供水印文字或水印图片')
            
            return {
                'url': url,
                'status': 'success',
                'title': title,
                'filepath': output_path,
                'filesize': os.path.getsize(output_path) if os.path.exists(output_path) else 0,
                'watermark_type': 'text' if watermark_text else 'image'
            }
            
        except Exception as e:
            raise Exception(f'水印添加失败: {str(e)}')
        
        finally:
            # 清理临时文件
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                except:
                    pass
    
    def add_text_watermark(self, video_path: str, output_path: str, text: str, 
                          position: str = 'bottom-right', font_size: int = 24, 
                          color: str = 'white', opacity: float = 0.8):
        """添加文字水印"""
        try:
            # 加载视频
            video = VideoFileClip(video_path)
            
            # 创建文字剪辑
            text_clip = TextClip(text, 
                               fontsize=font_size, 
                               color=color, 
                               font='Arial-Bold')
            
            # 设置文字位置
            text_clip = text_clip.set_opacity(opacity).set_duration(video.duration)
            
            # 根据位置设置文字剪辑的位置
            if position == 'bottom-right':
                text_clip = text_clip.set_position(('right', 'bottom')).set_margin(10)
            elif position == 'bottom-left':
                text_clip = text_clip.set_position(('left', 'bottom')).set_margin(10)
            elif position == 'top-right':
                text_clip = text_clip.set_position(('right', 'top')).set_margin(10)
            elif position == 'top-left':
                text_clip = text_clip.set_position(('left', 'top')).set_margin(10)
            elif position == 'center':
                text_clip = text_clip.set_position('center')
            
            # 合成视频
            final_video = CompositeVideoClip([video, text_clip])
            
            # 输出视频
            final_video.write_videofile(output_path, 
                                      codec='libx264', 
                                      audio_codec='aac',
                                      verbose=False,
                                      logger=None)
            
            # 清理资源
            text_clip.close()
            video.close()
            final_video.close()
            
        except Exception as e:
            raise Exception(f'文字水印添加失败: {str(e)}')
    
    def add_image_watermark(self, video_path: str, output_path: str, watermark_image_path: str,
                           position: str = 'bottom-right', scale: float = 0.1, opacity: float = 0.8):
        """添加图片水印"""
        try:
            if not os.path.exists(watermark_image_path):
                raise Exception('水印图片文件不存在')
            
            # 加载视频
            video = VideoFileClip(video_path)
            
            # 加载水印图片
            watermark = ImageClip(watermark_image_path)
            
            # 调整水印大小
            watermark_width = int(video.w * scale)
            watermark = watermark.resize(width=watermark_width)
            
            # 设置水印持续时间和透明度
            watermark = watermark.set_duration(video.duration).set_opacity(opacity)
            
            # 根据位置设置水印位置
            if position == 'bottom-right':
                watermark = watermark.set_position(('right', 'bottom')).set_margin(10)
            elif position == 'bottom-left':
                watermark = watermark.set_position(('left', 'bottom')).set_margin(10)
            elif position == 'top-right':
                watermark = watermark.set_position(('right', 'top')).set_margin(10)
            elif position == 'top-left':
                watermark = watermark.set_position(('left', 'top')).set_margin(10)
            elif position == 'center':
                watermark = watermark.set_position('center')
            
            # 合成视频
            final_video = CompositeVideoClip([video, watermark])
            
            # 输出视频
            final_video.write_videofile(output_path, 
                                      codec='libx264', 
                                      audio_codec='aac',
                                      verbose=False,
                                      logger=None)
            
            # 清理资源
            watermark.close()
            video.close()
            final_video.close()
            
        except Exception as e:
            raise Exception(f'图片水印添加失败: {str(e)}')
    
    def add_watermark_to_local_video(self, video_path: str, output_path: str, 
                                   watermark_text: str = None, watermark_image: str = None,
                                   position: str = 'bottom-right') -> Dict:
        """为本地视频添加水印"""
        try:
            if not os.path.exists(video_path):
                raise Exception('视频文件不存在')
            
            if watermark_text:
                self.add_text_watermark(video_path, output_path, watermark_text, position)
            elif watermark_image:
                self.add_image_watermark(video_path, output_path, watermark_image, position)
            else:
                raise Exception('请提供水印文字或水印图片')
            
            return {
                'status': 'success',
                'filepath': output_path,
                'filesize': os.path.getsize(output_path),
                'watermark_type': 'text' if watermark_text else 'image'
            }
            
        except Exception as e:
            raise Exception(f'本地视频水印添加失败: {str(e)}')
    
    def create_watermark_image(self, text: str, output_path: str, 
                             width: int = 200, height: int = 50, 
                             font_size: int = 20, color: str = 'white', 
                             background_color: str = 'transparent') -> str:
        """创建文字水印图片"""
        try:
            # 创建图片
            if background_color == 'transparent':
                img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            else:
                img = Image.new('RGB', (width, height), background_color)
            
            draw = ImageDraw.Draw(img)
            
            # 尝试加载字体
            try:
                font = ImageFont.truetype('arial.ttf', font_size)
            except:
                font = ImageFont.load_default()
            
            # 计算文字位置（居中）
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # 绘制文字
            draw.text((x, y), text, fill=color, font=font)
            
            # 保存图片
            img.save(output_path)
            
            return output_path
            
        except Exception as e:
            raise Exception(f'水印图片创建失败: {str(e)}')
    
    def sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        if len(filename) > 100:
            filename = filename[:100]
        return filename