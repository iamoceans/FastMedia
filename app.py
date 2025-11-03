from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
from werkzeug.utils import secure_filename
from services.video_downloader import VideoDownloader
from services.bgm_extractor import BGMExtractor
from services.thumbnail_extractor import ThumbnailExtractor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('downloads', exist_ok=True)

# 初始化服务
video_downloader = VideoDownloader()
bgm_extractor = BGMExtractor()

thumbnail_extractor = ThumbnailExtractor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/download_videos', methods=['POST'])
def download_videos():
    """批量视频无水印下载"""
    try:
        data = request.get_json()
        urls_input = data.get('urls', '')
        
        # 支持数组和字符串两种格式
        if isinstance(urls_input, list):
            urls = [url.strip() for url in urls_input if url.strip()]
        else:
            urls = urls_input.split(',')
            urls = [url.strip() for url in urls if url.strip()]
        
        if not urls:
            return jsonify({'error': '请提供有效的视频URL'}), 400
        
        results = video_downloader.download_batch(urls)
        return jsonify({'results': results})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract_bgm', methods=['POST'])
def extract_bgm():
    """批量视频提取BGM"""
    try:
        data = request.get_json()
        urls = data.get('urls', '').split(',')
        urls = [url.strip() for url in urls if url.strip()]
        
        if not urls:
            return jsonify({'error': '请提供有效的视频URL'}), 400
        
        results = bgm_extractor.extract_batch(urls)
        return jsonify({'results': results})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract_thumbnail', methods=['POST'])
def extract_thumbnail():
    """批量视频提取封面"""
    try:
        data = request.get_json()
        urls = data.get('urls', '').split(',')
        urls = [url.strip() for url in urls if url.strip()]
        timestamp = data.get('timestamp', 0)  # 提取指定时间点的帧，默认为0（第一帧）
        
        if not urls:
            return jsonify({'error': '请提供有效的视频URL'}), 400
        
        results = thumbnail_extractor.extract_batch(urls, timestamp)
        return jsonify({'results': results})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/test_bilibili', methods=['POST'])
def test_bilibili():
    """测试B站链接支持"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()

        if not url:
            return jsonify({'error': '请提供B站视频URL'}), 400

        # 测试平台检测
        platform = video_downloader.detect_platform(url)

        # 测试信息获取
        try:
            info = video_downloader.get_video_info(url)
            return jsonify({
                'platform_detected': platform,
                'video_info': {
                    'title': info.get('title', ''),
                    'uploader': info.get('uploader', ''),
                    'duration': info.get('duration', 0),
                    'platform': info.get('platform', ''),
                    'thumbnail': info.get('thumbnail', '')
                },
                'status': 'success'
            })
        except Exception as e:
            return jsonify({
                'platform_detected': platform,
                'error': str(e),
                'status': 'info_error'
            }), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check_bilibili_video', methods=['POST'])
def check_bilibili_video():
    """检测B站视频可用性"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()

        if not url:
            return jsonify({'error': '请提供B站视频URL'}), 400

        # 预处理URL
        processed_url = video_downloader.preprocess_url(url)
        platform = video_downloader.detect_platform(processed_url)

        if platform != 'bilibili':
            return jsonify({
                'error': '这不是B站视频链接',
                'platform_detected': platform
            }), 400

        # 使用简单的yt-dlp命令检查视频可用性
        import subprocess
        import json

        try:
            result = subprocess.run([
                'python', '-m', 'yt_dlp',
                '--no-warnings',
                '--no-download',
                '--print', '%(title)s|%(duration)s|%(uploader)s|%(view_count)s',
                '--no-playlist',
                processed_url
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split('|')
                if len(parts) >= 3:
                    return jsonify({
                        'platform_detected': platform,
                        'is_available': True,
                        'video_info': {
                            'title': parts[0],
                            'duration': int(parts[1]) if parts[1].isdigit() else 0,
                            'uploader': parts[2],
                            'view_count': int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
                        },
                        'status': 'success'
                    })
                else:
                    return jsonify({
                        'platform_detected': platform,
                        'is_available': False,
                        'error': '视频信息格式异常',
                        'status': 'parse_error'
                    }), 400
            else:
                error_msg = result.stderr.strip() if result.stderr else '视频不可访问或不存在'
                return jsonify({
                    'platform_detected': platform,
                    'is_available': False,
                    'error': error_msg,
                    'status': 'unavailable'
                }), 400

        except subprocess.TimeoutExpired:
            return jsonify({
                'platform_detected': platform,
                'is_available': False,
                'error': '检查视频超时，请稍后重试',
                'status': 'timeout'
            }), 400
        except Exception as e:
            return jsonify({
                'platform_detected': platform,
                'is_available': False,
                'error': f'检查失败: {str(e)}',
                'status': 'check_error'
            }), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download_temp_file', methods=['POST'])
def download_temp_file():
    """下载临时文件"""
    try:
        data = request.get_json()
        temp_filepath = data.get('temp_filepath')
        download_filename = data.get('download_filename', 'video.mp4')
        file_type = data.get('file_type', 'video')  # 根据文件类型设置mimetype

        if not temp_filepath or not os.path.exists(temp_filepath):
            return jsonify({'error': '文件不存在或已被清理'}), 404

        # 根据文件类型设置mimetype
        if file_type == 'bgm':
            mimetype = 'audio/mpeg'
        elif file_type == 'thumbnail':
            mimetype = 'image/jpeg'
        else:
            mimetype = 'video/mp4'

        
        return send_file(
            temp_filepath,
            as_attachment=True,
            download_name=download_filename,
            mimetype=mimetype
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cleanup_temp_file', methods=['POST'])
def cleanup_temp_file():
    """清理临时文件"""
    try:
        data = request.get_json()
        temp_filepath = data.get('temp_filepath')
        file_type = data.get('file_type', 'video')  # 'video', 'bgm' 或 'thumbnail'

        if temp_filepath:
            if file_type == 'bgm':
                bgm_extractor.cleanup_temp_file(temp_filepath)
            elif file_type == 'thumbnail':
                thumbnail_extractor.cleanup_temp_file(temp_filepath)
            elif file_type == 'xiaohongshu':
                video_downloader.xiaohongshu_downloader.cleanup_temp_file(temp_filepath)
            else:
                video_downloader.cleanup_temp_file(temp_filepath)
            return jsonify({'status': 'success', 'message': '文件已清理'})
        else:
            return jsonify({'error': '未提供文件路径'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check_temp_file', methods=['POST'])
def check_temp_file():
    """检查临时文件状态"""
    try:
        data = request.get_json()
        temp_filepath = data.get('temp_filepath')
        file_type = data.get('file_type', 'video')  # 'video', 'bgm' 或 'thumbnail'

        if not temp_filepath:
            return jsonify({'error': '未提供文件路径'}), 400

        if file_type == 'bgm':
            file_info = bgm_extractor.get_temp_file_info(temp_filepath)
        elif file_type == 'thumbnail':
            file_info = thumbnail_extractor.get_temp_file_info(temp_filepath)
        else:
            file_info = video_downloader.get_temp_file_info(temp_filepath)
        return jsonify(file_info)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<path:filename>')
def download_file(filename):
    """下载文件（保留原有功能）"""
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

def allowed_file(filename):
    """检查文件扩展名"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)