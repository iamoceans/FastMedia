from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
from werkzeug.utils import secure_filename
from services.video_downloader import VideoDownloader
from services.bgm_extractor import BGMExtractor
from services.text_extractor import TextExtractor
from services.watermark_adder import WatermarkAdder
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
text_extractor = TextExtractor()
watermark_adder = WatermarkAdder()
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

@app.route('/api/extract_text', methods=['POST'])
def extract_text():
    """批量视频提取文案"""
    try:
        data = request.get_json()
        urls = data.get('urls', '').split(',')
        urls = [url.strip() for url in urls if url.strip()]
        
        if not urls:
            return jsonify({'error': '请提供有效的视频URL'}), 400
        
        results = text_extractor.extract_batch(urls)
        return jsonify({'results': results})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add_watermark', methods=['POST'])
def add_watermark():
    """批量视频添加水印"""
    try:
        data = request.get_json()
        urls = data.get('urls', '').split(',')
        urls = [url.strip() for url in urls if url.strip()]
        watermark_text = data.get('watermark_text', '')
        watermark_image = data.get('watermark_image', '')
        
        if not urls:
            return jsonify({'error': '请提供有效的视频URL'}), 400
        
        if not watermark_text and not watermark_image:
            return jsonify({'error': '请提供水印文字或水印图片'}), 400
        
        results = watermark_adder.add_watermark_batch(urls, watermark_text, watermark_image)
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

@app.route('/api/upload_watermark', methods=['POST'])
def upload_watermark():
    """上传水印图片"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            return jsonify({'filepath': filepath})
        
        return jsonify({'error': '不支持的文件格式'}), 400
    
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