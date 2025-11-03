# FastMedia

🎬 **FastMedia** is a powerful media processing platform built on Flask framework, providing comprehensive video processing services. It supports multi-platform video downloading, BGM extraction, and thumbnail generation.

## ✨ Core Features

### 🎥 Batch Video Download (Watermark-Free)
- **Multi-platform Support**: Douyin, TikTok, Bilibili, YouTube, Twitter, Kuaishou, **Xiaohongshu**, etc.
- **Batch Processing**: Quick download of multiple videos via comma-separated URL lists
- **Smart Parsing**: Automatic platform recognition and optimal download strategy selection
- **Quality Control**: Support for resolutions up to 720p, balancing quality and storage space
- **Intelligent URL Handling**: Automatic parameter preservation for platform-specific access requirements
- **Temporary Storage**: Files are stored in temporary directories with user-controlled download
- **Persistent Access**: Fixed temporary directories ensure files remain accessible across server restarts

### 🎵 Batch Video BGM Extraction
- **High-Quality Audio**: 192kbps audio quality output
- **Format Support**: Automatic selection of optimal audio formats
- **Batch Processing**: Simultaneous BGM extraction from multiple videos
- **Platform Compatibility**: Support for all mainstream video platforms including Xiaohongshu
- **Temporary Storage**: BGM files stored temporarily with user-controlled download
- **Flexible Access**: Persistent access to extracted audio files



### 🖼️ Batch Video Thumbnail Extraction
- **Multiple Modes**: Support for extracting first frame or specific timestamp frames
- **Standard Size**: 320x180 (16:9 ratio) high-quality thumbnails
- **Format Optimization**: 90% quality JPEG format output
- **Batch Generation**: Process multiple video thumbnails at once, including Xiaohongshu videos
- **Temporary Storage**: Thumbnail files stored temporarily with user-controlled download
- **Custom Timestamps**: Extract frames at any specific time point

## 🏗️ Technical Architecture

### Backend Tech Stack
- **Framework**: Flask 2.3.3 - Lightweight web framework
- **Video Processing**: yt-dlp - Powerful video download tool
- **Video Editing**: MoviePy - Video processing and editing
- **Image Processing**: Pillow - Python image processing library
- **Logging System**: loguru - Modern logging
- **HTTP Requests**: requests - Simple HTTP library
- **CORS Support**: Flask-CORS - Cross-origin resource sharing
- **Environment**: python-dotenv - Environment variable management

### Core Service Modules
- `VideoDownloader` - Video download service with multi-platform support
- `BGMExtractor` - BGM extraction service with audio processing
- `ThumbnailExtractor` - Thumbnail extraction service with frame capture
- `KuaishouDownloader` - Kuaishou-specific downloader with optimized parsing
- `XiaohongshuDownloader` - Xiaohongshu-specific downloader with parameter preservation

## 🚀 Quick Start

### Requirements
- Python 3.8+
- Operating System: Windows/Linux/macOS

### Installation Steps

1. **Clone the Project**
```bash
git clone https://github.com/your-username/FastMedia.git
cd FastMedia
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Start the Service**
```bash
python run.py
```

4. **Access the Application**
Open your browser and visit: `http://localhost:5000`

### Configuration

The project supports multi-environment configuration, adjustable in `config.py`:

- **Development Environment**: `DevelopmentConfig`
- **Production Environment**: `ProductionConfig`
- **Testing Environment**: `TestingConfig`

### Platform-Specific Usage Notes

#### 🔴 Xiaohongshu (小红书) URLs

Xiaohongshu links require specific parameters for proper access:

❌ **Incorrect (will fail):**
```
https://www.xiaohongshu.com/discovery/item/68fc7476000000000700f3ca?
```

✅ **Correct (will work):**
```
https://www.xiaohongshu.com/discovery/item/68fc7476000000000700f3ca?source=webshare&xhsshare=pc_web&xsec_token=AB2z9H4LdGP6Rne6M6DUdbCbBaP20JxrM_hY5ToFmMgGY=&xsec_source=pc_share
```

**How to get the correct URL:**
1. Use the official share function in the Xiaohongshu app
2. Copy the complete share link (contains all required parameters)
3. Paste the full link into FastMedia

**Required Parameters:**
- `source=webshare`
- `xhsshare=pc_web`
- `xsec_token=[unique_token]`
- `xsec_source=pc_share`

### 🌐 Modern Web Interface

FastMedia features a modern, responsive web interface designed for optimal user experience:

#### 📋 Persistent URL Input
- **Always-Visible**: URL input area remains fixed at the top of the page
- **Batch Support**: Paste multiple URLs separated by commas for batch processing
- **Platform Display**: Visual showcase of all supported platforms with modern tags

#### 🎯 Intuitive Feature Selection
- **Card-Based Layout**: Three main functions displayed as interactive cards
- **Visual Feedback**: Hover effects and selection states for better UX
- **Real-time Processing**: Live progress indicators and status updates

#### 📱 Responsive Design
- **Mobile Optimized**: Fully responsive layout that works on all devices
- **Touch-Friendly**: Large tap targets and mobile-optimized controls
- **Progressive Enhancement**: Graceful degradation for older browsers

#### 🎨 Modern Aesthetics
- **Clean Design**: Minimalist interface with focus on functionality
- **Platform Tags**: Visual representation of supported platforms
- **Smooth Animations**: Subtle transitions and micro-interactions

### Interface Modules

#### 📥 Task Input Area
- **Function Selection**: Dropdown menu for processing type selection (Download/BGM/Thumbnail)
- **URL Input**: Multi-line text box supporting batch URL list pasting
- **Parameter Configuration**: Dynamic display of relevant configuration options based on selected function

#### ⚙️ Advanced Settings
- **Output Path**: Custom file save location
- **Concurrency Control**: Maximum 3 concurrent download tasks
- **Timeout Settings**: 5-minute download timeout protection
- **Log Level**: INFO/DEBUG level selection

#### 📊 Task Status Area
- **Real-time Progress**: Display success/failure/total statistics
- **Error Details**: Detailed error information for failed tasks
- **Result Downloads**: Download links for processed files

#### 📋 History Records
- **Task Tracking**: Task ID, time, function type records
- **Result Preview**: Quick preview of processing results
- **Filter Function**: Filter history records by time or function type

## 🔌 API Endpoints

FastMedia provides RESTful API endpoints for programmatic access:

### Video Download
```http
POST /api/download_videos
Content-Type: application/json

{
  "urls": "https://example.com/video1,https://example.com/video2"
}
```

### BGM Extraction
```http
POST /api/extract_bgm
Content-Type: application/json

{
  "urls": "https://example.com/video1,https://example.com/video2"
}
```



### Thumbnail Extraction
```http
POST /api/extract_thumbnail
Content-Type: application/json

{
  "urls": "https://example.com/video1",
  "timestamp": 5
}
```

### Temporary File Management
```http
POST /api/download_temp_file
Content-Type: application/json

{
  "temp_filepath": "C:\\path\\to\\temp\\file.mp4",
  "download_filename": "video.mp4",
  "file_type": "video"
}
```

```http
POST /api/check_temp_file
Content-Type: application/json

{
  "temp_filepath": "C:\\path\\to\\temp\\file.mp4",
  "file_type": "video"
}
```

```http
POST /api/cleanup_temp_file
Content-Type: application/json

{
  "temp_filepath": "C:\\path\\to\\temp\\file.mp4",
  "file_type": "video"
}
```

### Platform Testing
```http
POST /api/check_bilibili_video
Content-Type: application/json

{
  "url": "https://www.bilibili.com/video/BV1234567890"
}
```

```http
POST /api/test_bilibili
Content-Type: application/json

{
  "url": "https://www.bilibili.com/video/BV1234567890"
}
```

## 🌐 Supported Platforms

| Platform | Domain | Status | Special Notes |
|----------|--------|--------|---------------|
| Douyin | douyin.com | ✅ Supported | Watermark-free download |
| TikTok | tiktok.com | ✅ Supported | International version |
| Bilibili | bilibili.com, b23.tv | ✅ Supported | Short link support |
| YouTube | youtube.com, youtu.be | ✅ Supported | Multi-resolution options |
| Twitter/X | twitter.com, x.com | ✅ Supported | Videos and GIFs |
| Kuaishou | kuaishou.com | ✅ Supported | Dedicated parser |
| Xiaohongshu | xiaohongshu.com, xhslink.com | ✅ Supported | Requires full share URL with parameters |

## 📁 Directory Structure

```
FastMedia/
├── app.py                 # Flask application main file
├── config.py             # Configuration file
├── requirements.txt      # Dependencies list
├── run.py               # Startup script
├── utils.py             # Utility functions
├── services/            # Core service modules
│   ├── __init__.py
│   ├── video_downloader.py
│   ├── bgm_extractor.py
│   ├── thumbnail_extractor.py
│   ├── kuaishou_downloader.py
│   └── xiaohongshu_downloader.py
├── static/              # Static resources
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/           # HTML templates
│   └── index.html
├── downloads/           # Downloaded files storage
│   ├── videos/
│   ├── bgm/
│   └── thumbnails/
└── logs/               # Log files
    └── fastmedia.log
```

## ⚠️ Important Notes

### Usage Limitations
- **Concurrency Limit**: Maximum 3 concurrent download tasks to avoid server overload
- **File Size**: Upload file limit of 100MB
- **Timeout Settings**: Single download task timeout of 5 minutes
- **Resolution Limit**: Video downloads limited to 720p and below for quality-storage balance

### Legal Disclaimer
- This tool is for educational and research purposes only
- Please comply with each platform's terms of service and copyright policies
- Downloaded content should not be used for commercial purposes
- Users are responsible for their own legal compliance

### Technical Limitations
- Some platforms may have anti-crawling mechanisms affecting download success rates
- Platforms like Kuaishou and Xiaohongshu require special handling (dedicated parsers provided)
- Some private or restricted videos cannot be downloaded
- **Xiaohongshu URLs require complete share parameters** (source, xhsshare, xsec_token, xsec_source) for access

## 🤝 Contributing

Welcome to submit Issues and Pull Requests to improve the project:

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 📞 Contact

- Project Homepage: [GitHub Repository](https://github.com/your-username/FastMedia)
- Issue Reports: [Issues](https://github.com/your-username/FastMedia/issues)
- Email: your-email@example.com

---

⭐ If this project helps you, please give it a star!