import os
import yt_dlp
import re
from typing import List, Dict
import requests
from urllib.parse import urlparse

class TextExtractor:
    def __init__(self):
        self.output_dir = 'downloads/texts'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def extract_batch(self, urls: List[str]) -> List[Dict]:
        """批量提取文案"""
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
                    'text_content': None,
                    'filepath': None
                })
        
        return results
    
    def extract_single(self, url: str) -> Dict:
        """提取单个视频的文案"""
        try:
            # 使用yt-dlp获取视频信息
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                
                title = info.get('title', '')
                description = info.get('description', '')
                uploader = info.get('uploader', '')
                tags = info.get('tags', [])
                
                # 提取字幕（如果有）
                subtitles = self.extract_subtitles(info)
                
                # 组合文案内容
                text_content = self.format_text_content({
                    'title': title,
                    'description': description,
                    'uploader': uploader,
                    'tags': tags,
                    'subtitles': subtitles
                })
                
                # 保存到文件
                filename = f"{self.sanitize_filename(title)}_text.txt"
                filepath = os.path.join(self.output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                
                return {
                    'url': url,
                    'status': 'success',
                    'title': title,
                    'text_content': text_content,
                    'filepath': filepath,
                    'filesize': os.path.getsize(filepath),
                    'has_subtitles': bool(subtitles)
                }
                
        except Exception as e:
            raise Exception(f'文案提取失败: {str(e)}')
    
    def extract_subtitles(self, video_info: Dict) -> str:
        """提取字幕内容"""
        subtitles_text = ""
        
        try:
            # 获取字幕信息
            subtitles = video_info.get('subtitles', {})
            automatic_captions = video_info.get('automatic_captions', {})
            
            # 优先使用手动字幕，然后是自动字幕
            all_subs = {**automatic_captions, **subtitles}
            
            # 尝试获取中文字幕
            for lang in ['zh', 'zh-CN', 'zh-Hans', 'en', 'en-US']:
                if lang in all_subs:
                    sub_list = all_subs[lang]
                    if sub_list:
                        # 获取第一个可用的字幕格式
                        sub_url = sub_list[0].get('url')
                        if sub_url:
                            subtitles_text = self.download_subtitle(sub_url)
                            break
            
        except Exception as e:
            print(f"字幕提取错误: {e}")
        
        return subtitles_text
    
    def download_subtitle(self, subtitle_url: str) -> str:
        """下载字幕文件并提取文本"""
        try:
            response = requests.get(subtitle_url, timeout=10)
            response.raise_for_status()
            
            subtitle_content = response.text
            
            # 解析字幕格式（支持VTT和SRT）
            if subtitle_url.endswith('.vtt') or 'webvtt' in subtitle_content.lower():
                return self.parse_vtt(subtitle_content)
            elif subtitle_url.endswith('.srt') or '-->' in subtitle_content:
                return self.parse_srt(subtitle_content)
            else:
                # 尝试提取纯文本
                return self.extract_plain_text(subtitle_content)
                
        except Exception as e:
            print(f"字幕下载错误: {e}")
            return ""
    
    def parse_vtt(self, vtt_content: str) -> str:
        """解析VTT字幕格式"""
        lines = vtt_content.split('\n')
        text_lines = []
        
        for line in lines:
            line = line.strip()
            # 跳过时间戳行和空行
            if '-->' in line or line.startswith('WEBVTT') or not line:
                continue
            # 跳过样式标签
            if line.startswith('<') and line.endswith('>'):
                continue
            # 移除HTML标签
            clean_line = re.sub(r'<[^>]+>', '', line)
            if clean_line:
                text_lines.append(clean_line)
        
        return '\n'.join(text_lines)
    
    def parse_srt(self, srt_content: str) -> str:
        """解析SRT字幕格式"""
        lines = srt_content.split('\n')
        text_lines = []
        
        for line in lines:
            line = line.strip()
            # 跳过序号行、时间戳行和空行
            if line.isdigit() or '-->' in line or not line:
                continue
            text_lines.append(line)
        
        return '\n'.join(text_lines)
    
    def extract_plain_text(self, content: str) -> str:
        """提取纯文本内容"""
        # 移除HTML标签
        clean_content = re.sub(r'<[^>]+>', '', content)
        # 移除时间戳
        clean_content = re.sub(r'\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}', '', clean_content)
        # 移除多余的空白
        clean_content = re.sub(r'\s+', ' ', clean_content)
        return clean_content.strip()
    
    def format_text_content(self, content_dict: Dict) -> str:
        """格式化文案内容"""
        formatted_text = []
        
        if content_dict['title']:
            formatted_text.append(f"标题: {content_dict['title']}")
        
        if content_dict['uploader']:
            formatted_text.append(f"作者: {content_dict['uploader']}")
        
        if content_dict['description']:
            formatted_text.append(f"\n描述:\n{content_dict['description']}")
        
        if content_dict['tags']:
            tags_str = ', '.join(content_dict['tags'][:10])  # 限制标签数量
            formatted_text.append(f"\n标签: {tags_str}")
        
        if content_dict['subtitles']:
            formatted_text.append(f"\n字幕内容:\n{content_dict['subtitles']}")
        
        return '\n'.join(formatted_text)
    
    def sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        # 移除或替换非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        return filename
    
    def extract_from_text(self, text: str, title: str = "custom_text") -> Dict:
        """从自定义文本创建文案文件"""
        try:
            filename = f"{self.sanitize_filename(title)}_custom.txt"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            
            return {
                'status': 'success',
                'title': title,
                'text_content': text,
                'filepath': filepath,
                'filesize': os.path.getsize(filepath)
            }
            
        except Exception as e:
            raise Exception(f'文本保存失败: {str(e)}')