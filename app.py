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
        urls = data.get('urls', '').split(',')
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


@app.route('/download/<path:filename>')
def download_file(filename):
    """下载文件"""
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