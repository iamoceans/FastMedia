// 全局变量
let currentFeature = null;
let uploadedWatermarkPath = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
});

// 初始化事件监听器
function initializeEventListeners() {
    // 功能卡片点击事件
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('click', function() {
            const feature = this.dataset.feature;
            selectFeature(feature);
        });
    });

    // 文件上传事件
    const fileUpload = document.getElementById('watermark-upload');
    const fileInput = document.getElementById('watermark-file');
    
    if (fileUpload && fileInput) {
        fileUpload.addEventListener('click', () => fileInput.click());
        fileUpload.addEventListener('dragover', handleDragOver);
        fileUpload.addEventListener('drop', handleDrop);
        fileInput.addEventListener('change', handleFileSelect);
    }
}

// 选择功能
function selectFeature(feature) {
    // 移除所有活动状态
    document.querySelectorAll('.feature-card').forEach(card => {
        card.classList.remove('active');
    });
    document.querySelectorAll('.input-section').forEach(section => {
        section.classList.remove('active');
    });

    // 添加活动状态
    document.querySelector(`[data-feature="${feature}"]`).classList.add('active');
    document.getElementById(`${feature}-section`).classList.add('active');
    
    currentFeature = feature;
    hideResults();
    hideAlert();
}

// 处理视频
async function processVideos(type) {
    const urlsElement = document.getElementById(`${type}-urls`);
    const urls = urlsElement.value.trim();
    
    if (!urls) {
        showAlert('请输入视频URL', 'error');
        return;
    }

    // 显示加载状态
    showLoading();
    hideAlert();
    hideResults();

    try {
        let requestData = { urls: urls };
        let endpoint = '';

        // 根据类型设置不同的请求数据和端点
        switch (type) {
            case 'download':
                endpoint = '/api/download_videos';
                break;
            case 'bgm':
                endpoint = '/api/extract_bgm';
                break;
            case 'text':
                endpoint = '/api/extract_text';
                break;
            case 'watermark':
                endpoint = '/api/add_watermark';
                const watermarkText = document.getElementById('watermark-text').value.trim();
                if (watermarkText) {
                    requestData.watermark_text = watermarkText;
                }
                if (uploadedWatermarkPath) {
                    requestData.watermark_image = uploadedWatermarkPath;
                }
                if (!watermarkText && !uploadedWatermarkPath) {
                    hideLoading();
                    showAlert('请输入水印文字或上传水印图片', 'error');
                    return;
                }
                break;
            case 'thumbnail':
                endpoint = '/api/extract_thumbnail';
                const timestamp = document.getElementById('thumbnail-timestamp').value;
                requestData.timestamp = parseFloat(timestamp) || 0;
                break;
            default:
                throw new Error('未知的处理类型');
        }

        // 发送请求
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || '请求失败');
        }

        // 显示结果
        displayResults(data.results, type);
        showAlert('处理完成！', 'success');

    } catch (error) {
        console.error('处理错误:', error);
        showAlert(`处理失败: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

// 显示结果
function displayResults(results, type) {
    const resultsContent = document.getElementById('results-content');
    const resultsSection = document.getElementById('results');
    
    resultsContent.innerHTML = '';
    
    results.forEach((result, index) => {
        const resultItem = document.createElement('div');
        resultItem.className = `result-item ${result.status}`;
        
        let content = `<strong>项目 ${index + 1}:</strong> ${result.url || '本地处理'}<br>`;
        
        if (result.status === 'success') {
            content += `<span style="color: #4caf50;">✓ 处理成功</span><br>`;
            
            if (result.title) {
                content += `标题: ${result.title}<br>`;
            }
            
            if (result.filepath) {
                content += `文件路径: ${result.filepath}<br>`;
                content += `<a href="/download/${encodeURIComponent(result.filepath)}" class="btn btn-secondary" style="margin-top: 8px; text-decoration: none;"><i class="fas fa-download"></i> 下载文件</a>`;
            }
            
            if (result.filesize) {
                content += `文件大小: ${formatFileSize(result.filesize)}<br>`;
            }
            
            // 根据类型显示特定信息
            switch (type) {
                case 'text':
                    if (result.text_content) {
                        content += `<details style="margin-top: 8px;"><summary>查看文案内容</summary><pre style="white-space: pre-wrap; margin-top: 8px; padding: 8px; background: #f5f5f5; border-radius: 4px;">${result.text_content}</pre></details>`;
                    }
                    break;
                case 'watermark':
                    if (result.watermark_type) {
                        content += `水印类型: ${result.watermark_type === 'text' ? '文字水印' : '图片水印'}<br>`;
                    }
                    break;
                case 'thumbnail':
                    if (result.timestamp !== undefined) {
                        content += `提取时间点: ${result.timestamp}秒<br>`;
                    }
                    break;
            }
            
        } else {
            content += `<span style="color: #f44336;">✗ 处理失败</span><br>`;
            content += `错误信息: ${result.error}<br>`;
        }
        
        resultItem.innerHTML = content;
        resultsContent.appendChild(resultItem);
    });
    
    resultsSection.classList.add('active');
}

// 文件拖拽处理
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFileUpload(file);
    }
}

// 处理文件上传
async function handleFileUpload(file) {
    if (!file.type.startsWith('image/')) {
        showAlert('请选择图片文件', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        showLoading();
        
        const response = await fetch('/api/upload_watermark', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || '上传失败');
        }

        uploadedWatermarkPath = data.filepath;
        
        // 更新UI显示
        const uploadDiv = document.getElementById('watermark-upload');
        uploadDiv.innerHTML = `
            <i class="fas fa-check-circle" style="font-size: 24px; color: #4caf50; margin-bottom: 8px;"></i>
            <p style="color: #4caf50;">图片上传成功: ${file.name}</p>
            <button type="button" class="btn btn-secondary" onclick="resetFileUpload()" style="margin-top: 8px;">重新选择</button>
        `;
        
        showAlert('图片上传成功！', 'success');
        
    } catch (error) {
        console.error('上传错误:', error);
        showAlert(`上传失败: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

// 重置文件上传
function resetFileUpload() {
    uploadedWatermarkPath = null;
    const uploadDiv = document.getElementById('watermark-upload');
    uploadDiv.innerHTML = `
        <i class="fas fa-cloud-upload-alt" style="font-size: 24px; color: #6b6b6b; margin-bottom: 8px;"></i>
        <p>点击或拖拽上传水印图片</p>
        <input type="file" id="watermark-file" accept="image/*" style="display: none;">
    `;
    
    // 重新绑定事件
    const fileInput = document.getElementById('watermark-file');
    const fileUpload = document.getElementById('watermark-upload');
    fileUpload.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
}

// 显示加载状态
function showLoading() {
    document.getElementById('loading').classList.add('active');
    
    // 模拟进度条
    const progressFill = document.getElementById('progress-fill');
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        progressFill.style.width = progress + '%';
    }, 500);
    
    // 存储interval ID以便后续清除
    document.getElementById('loading').dataset.interval = interval;
}

// 隐藏加载状态
function hideLoading() {
    const loading = document.getElementById('loading');
    const interval = loading.dataset.interval;
    
    if (interval) {
        clearInterval(interval);
    }
    
    // 完成进度条
    document.getElementById('progress-fill').style.width = '100%';
    
    setTimeout(() => {
        loading.classList.remove('active');
        document.getElementById('progress-fill').style.width = '0%';
    }, 500);
}

// 显示提示信息
function showAlert(message, type = 'success') {
    const alert = document.getElementById('alert');
    const alertMessage = document.getElementById('alert-message');
    
    alert.className = `alert ${type} active`;
    alertMessage.textContent = message;
    
    // 自动隐藏
    setTimeout(() => {
        hideAlert();
    }, 5000);
}

// 隐藏提示信息
function hideAlert() {
    document.getElementById('alert').classList.remove('active');
}

// 显示结果
function showResults() {
    document.getElementById('results').classList.add('active');
}

// 隐藏结果
function hideResults() {
    document.getElementById('results').classList.remove('active');
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 复制到剪贴板
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('已复制到剪贴板', 'success');
    }).catch(() => {
        showAlert('复制失败', 'error');
    });
}

// 下载文件
function downloadFile(filepath) {
    window.open(`/download/${encodeURIComponent(filepath)}`, '_blank');
}