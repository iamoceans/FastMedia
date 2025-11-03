# FastMedia

🎬 **FastMedia** 是一个功能强大的媒体处理平台，基于 Flask 框架构建，提供全方位的视频处理服务。支持多平台视频下载、BGM提取和封面生成等功能。

## ✨ 核心功能

### 🎥 批量视频无水印下载
- 支持多平台：抖音、TikTok、B站、YouTube、Twitter、快手、**小红书**等
- 批量处理：通过逗号分隔的URL列表快速下载多个视频
- 智能解析：自动识别平台并选择最佳下载策略
- 质量控制：支持720p以下分辨率，平衡质量与存储空间
- **临时存储**：文件存储在临时目录中，用户控制下载
- **持久访问**：固定临时目录确保服务器重启后文件仍可访问

### 🎵 批量视频BGM提取
- 高质量音频：192kbps音频质量输出
- 格式支持：自动选择最佳音频格式
- 批量处理：同时处理多个视频的BGM提取
- 平台兼容：支持所有主流视频平台，包括小红书
- **临时存储**：BGM文件临时存储，用户控制下载
- **灵活访问**：提取的音频文件持久可访问



### 🖼️ 批量视频封面提取
- 多种模式：支持提取视频第一帧或指定时间点帧
- 标准尺寸：320x180 (16:9比例) 高质量缩略图
- 格式优化：90%质量的JPEG格式输出
- 批量生成：一次性处理多个视频封面，包括小红书视频
- **临时存储**：封面文件临时存储，用户控制下载
- **自定义时间点**：可提取任意时间点的视频帧

## 🏗️ 技术架构

### 后端技术栈
- **框架**: Flask 2.3.3 - 轻量级Web框架
- **视频处理**: yt-dlp - 强大的视频下载工具
- **视频编辑**: MoviePy - 视频处理和编辑
- **图像处理**: Pillow - Python图像处理库
- **日志系统**: loguru - 现代化日志记录
- **HTTP请求**: requests - 简洁的HTTP库
- **跨域支持**: Flask-CORS - 跨域资源共享
- **环境管理**: python-dotenv - 环境变量管理

### 核心服务模块
- `VideoDownloader` - 视频下载服务
- `BGMExtractor` - BGM提取服务
- `ThumbnailExtractor` - 封面提取服务
- `KuaishouDownloader` - 快手专用下载器

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 操作系统: Windows/Linux/macOS

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/FastMedia.git
cd FastMedia
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动服务**
```bash
python run.py
```

4. **访问应用**
打开浏览器访问: `http://localhost:5000`

### 配置说明

项目支持多环境配置，可在 `config.py` 中调整：

- **开发环境**: `DevelopmentConfig`
- **生产环境**: `ProductionConfig`
- **测试环境**: `TestingConfig`

### 界面功能模块

#### 📥 任务输入区
- **功能选择**: 下拉菜单选择处理类型（下载/BGM/封面）
- **URL输入**: 多行文本框，支持批量粘贴URL列表
- **参数配置**: 根据选择功能动态显示相关配置选项

#### ⚙️ 高级设置
- **输出路径**: 自定义文件保存位置
- **并发控制**: 最大3个并发下载任务
- **超时设置**: 5分钟下载超时保护
- **日志级别**: INFO/DEBUG级别选择

#### 📊 任务状态区
- **实时进度**: 显示成功/失败/总数统计
- **错误详情**: 失败任务的详细错误信息
- **结果下载**: 处理完成文件的下载链接

#### 📋 历史记录
- **任务追踪**: 任务ID、时间、功能类型记录
- **结果预览**: 处理结果的快速预览
- **筛选功能**: 按时间或功能类型筛选历史记录

## 🔌 API接口

FastMedia 提供RESTful API接口，支持程序化调用：

### 视频下载
```http
POST /api/download_videos
Content-Type: application/json

{
  "urls": "https://example.com/video1,https://example.com/video2"
}
```

### BGM提取
```http
POST /api/extract_bgm
Content-Type: application/json

{
  "urls": "https://example.com/video1,https://example.com/video2"
}
```



### 封面提取
```http
POST /api/extract_thumbnail
Content-Type: application/json

{
  "urls": "https://example.com/video1",
  "timestamp": "00:00:05"
}
```

## 🌐 支持平台

| 平台 | 域名 | 状态 | 特殊说明 |
|------|------|------|----------|
| 抖音 | douyin.com | ✅ 支持 | 无水印下载 |
| TikTok | tiktok.com | ✅ 支持 | 国际版抖音 |
| 哔哩哔哩 | bilibili.com, b23.tv | ✅ 支持 | 支持短链接 |
| YouTube | youtube.com, youtu.be | ✅ 支持 | 多分辨率选择 |
| Twitter/X | twitter.com, x.com | ✅ 支持 | 视频和GIF |
| 快手 | kuaishou.com | ✅ 支持 | 专用解析器 |

## 📁 目录结构

```
FastMedia/
├── app.py                 # Flask应用主文件
├── config.py             # 配置文件
├── requirements.txt      # 依赖包列表
├── run.py               # 启动脚本
├── utils.py             # 工具函数
├── services/            # 核心服务模块
│   ├── __init__.py
│   ├── video_downloader.py
│   ├── bgm_extractor.py
│   ├── thumbnail_extractor.py
│   └── kuaishou_downloader.py
├── static/              # 静态资源
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/           # HTML模板
│   └── index.html
├── downloads/           # 下载文件存储
│   ├── videos/
│   ├── bgm/
│   └── thumbnails/
└── logs/               # 日志文件
    └── fastmedia.log
```

## ⚠️ 注意事项

### 使用限制
- **并发限制**: 最大3个并发下载任务，避免服务器压力过大
- **文件大小**: 上传文件限制100MB
- **超时设置**: 单个下载任务超时时间为5分钟
- **分辨率限制**: 视频下载限制在720p以下，平衡质量与存储

### 法律声明
- 本工具仅供学习和研究使用
- 请遵守各平台的服务条款和版权政策
- 下载的内容请勿用于商业用途
- 使用者需自行承担法律责任

### 技术限制
- 部分平台可能有反爬虫机制，影响下载成功率
- 快手等平台可能需要特殊处理，已提供专用解析器
- 某些私有或受限视频无法下载

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- 项目主页: [GitHub Repository](https://github.com/your-username/FastMedia)
- 问题反馈: [Issues](https://github.com/your-username/FastMedia/issues)
- 邮箱: your-email@example.com

---

⭐ 如果这个项目对你有帮助，请给它一个星标！