// 全局变量
let currentFeature = null;

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

    // 全局URL输入框事件
    const globalUrlsInput = document.getElementById('global-urls');
    globalUrlsInput.addEventListener('input', updateProcessButton);

    // 文件上传相关功能已移除
}

// 选择功能
function selectFeature(feature) {
    // 移除所有活动状态
    document.querySelectorAll('.feature-card').forEach(card => {
        card.classList.remove('active');
    });

    // 添加活动状态
    document.querySelector(`[data-feature="${feature}"]`).classList.add('active');

    // 封面提取特殊处理：显示时间输入
    if (feature === 'thumbnail') {
        document.getElementById('thumbnail-section').classList.add('active');
    } else {
        document.querySelectorAll('.input-section').forEach(section => {
            section.classList.remove('active');
        });
    }

    currentFeature = feature;
    updateProcessButton();
    hideResults();
    hideAlert();
}

// 更新处理按钮状态
function updateProcessButton() {
    const urlsInput = document.getElementById('global-urls');
    const processBtn = document.getElementById('process-btn');
    const processBtnText = document.getElementById('process-btn-text');

    const hasUrls = urlsInput.value.trim() !== '';
    const hasFeature = currentFeature !== null;

    if (hasUrls && hasFeature) {
        processBtn.disabled = false;
        // 根据功能设置不同的按钮文本
        switch (currentFeature) {
            case 'download':
                processBtnText.textContent = '开始下载';
                break;
            case 'bgm':
                processBtnText.textContent = '提取BGM';
                break;
            case 'thumbnail':
                processBtnText.textContent = '提取封面';
                break;
            default:
                processBtnText.textContent = '开始处理';
        }
    } else {
        processBtn.disabled = true;
        if (!hasFeature && !hasUrls) {
            processBtnText.textContent = '请选择功能并输入URL';
        } else if (!hasFeature) {
            processBtnText.textContent = '请选择功能';
        } else {
            processBtnText.textContent = '请输入URL';
        }
    }
}

// 处理选中的功能
async function processSelectedFeature() {
    if (!currentFeature) {
        showAlert('请先选择一个功能', 'error');
        return;
    }

    const urlsInput = document.getElementById('global-urls');
    const urls = urlsInput.value.trim();

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
        switch (currentFeature) {
            case 'download':
                endpoint = '/api/download_videos';
                break;
            case 'bgm':
                endpoint = '/api/extract_bgm';
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
        displayResults(data.results, currentFeature);
        showAlert('处理完成！', 'success');

    } catch (error) {
        console.error('处理错误:', error);
        showAlert(`处理失败: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
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
        
        // 创建结果卡片的HTML结构
        const resultCard = document.createElement('div');
        resultCard.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 16px;
            padding: 20px;
            background: ${result.status === 'success' ? '#f0f9ff' : '#fef2f2'};
            border: 1px solid ${result.status === 'success' ? '#a7f3d0' : '#fca5a5'};
            border-radius: 8px;
            margin-bottom: 16px;
        `;
        
        // 左侧信息区域
        const infoSection = document.createElement('div');
        infoSection.style.cssText = 'flex: 1; min-width: 0;';
        
        // 状态和序号
        const header = document.createElement('div');
        header.style.cssText = 'display: flex; align-items: center; gap: 8px; margin-bottom: 12px;';
        
        const statusIcon = document.createElement('span');
        statusIcon.style.cssText = `
            font-size: 18px;
            font-weight: bold;
            color: ${result.status === 'success' ? '#059669' : '#dc2626'};
        `;
        statusIcon.textContent = result.status === 'success' ? '✓' : '✗';
        
        const itemNumber = document.createElement('span');
        itemNumber.style.cssText = 'font-weight: 600; color: #2d2d2d; font-size: 16px;';
        itemNumber.textContent = `项目 ${index + 1}`;
        
        const statusText = document.createElement('span');
        statusText.style.cssText = `
            color: ${result.status === 'success' ? '#059669' : '#dc2626'};
            font-weight: 500;
            font-size: 14px;
        `;
        statusText.textContent = result.status === 'success' ? '处理成功' : '处理失败';
        
        header.appendChild(statusIcon);
        header.appendChild(itemNumber);
        header.appendChild(statusText);
        
        // URL信息
        const urlInfo = document.createElement('div');
        urlInfo.style.cssText = 'margin-bottom: 12px;';
        
        const urlLabel = document.createElement('div');
        urlLabel.style.cssText = 'font-size: 12px; color: #6b7280; margin-bottom: 4px;';
        urlLabel.textContent = '视频链接:';
        
        const urlText = document.createElement('div');
        urlText.style.cssText = `
            font-size: 14px;
            color: #2383e2;
            word-break: break-all;
            line-height: 1.4;
        `;
        urlText.textContent = result.url || '本地处理';
        
        urlInfo.appendChild(urlLabel);
        urlInfo.appendChild(urlText);
        
        // 详细信息
        const detailsSection = document.createElement('div');
        detailsSection.style.cssText = 'display: grid; gap: 8px;';
        
        if (result.status === 'success') {
            // 标题
            if (result.title) {
                const titleRow = createInfoRow('标题', result.title);
                detailsSection.appendChild(titleRow);
            }
            
            // 平台信息
            if (result.platform) {
                const platformRow = createInfoRow('平台', result.platform);
                detailsSection.appendChild(platformRow);
            }
            
            // 文件大小
            if (result.filesize) {
                const sizeRow = createInfoRow('文件大小', formatFileSize(result.filesize));
                detailsSection.appendChild(sizeRow);
            }
            
            // 文件路径
            if (result.filepath) {
                const pathRow = createInfoRow('文件路径', getFileName(result.filepath));
                detailsSection.appendChild(pathRow);
            }
            
            // 根据类型显示特定信息
            if (type === 'thumbnail' && result.timestamp !== undefined) {
                const timestampRow = createInfoRow('提取时间点', `${result.timestamp}秒`);
                detailsSection.appendChild(timestampRow);
            }
            
        } else {
            // 错误信息
            const errorRow = document.createElement('div');
            errorRow.style.cssText = 'margin-top: 8px;';
            
            const errorLabel = document.createElement('div');
            errorLabel.style.cssText = 'font-size: 12px; color: #6b7280; margin-bottom: 4px;';
            errorLabel.textContent = '错误信息:';
            
            const errorText = document.createElement('div');
            errorText.style.cssText = 'font-size: 14px; color: #dc2626; line-height: 1.4;';
            errorText.textContent = result.error || '未知错误';
            
            errorRow.appendChild(errorLabel);
            errorRow.appendChild(errorText);
            detailsSection.appendChild(errorRow);
        }
        
        // 组装左侧信息
        infoSection.appendChild(header);
        infoSection.appendChild(urlInfo);
        infoSection.appendChild(detailsSection);
        
        // 右侧操作区域
        const actionSection = document.createElement('div');
        actionSection.style.cssText = 'display: flex; flex-direction: column; gap: 8px; align-items: flex-end;';
        
        if (result.status === 'success' && (result.temp_filepath || result.filepath)) {
            // 下载按钮
            const downloadBtn = document.createElement('button');
            downloadBtn.className = 'btn';
            downloadBtn.style.cssText = `
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 8px 16px;
                background: #2383e2;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.15s ease;
                white-space: nowrap;
                margin-bottom: 4px;
                border: none;
                cursor: pointer;
            `;
            downloadBtn.innerHTML = '<i class="fas fa-download"></i> 下载文件';

            // 添加点击事件
            downloadBtn.addEventListener('click', () => {
                const fileType = type === 'bgm' ? 'bgm' : (type === 'thumbnail' ? 'thumbnail' : 'video');
                downloadTempFile(result, fileType);
            });

            // 添加悬停效果
            downloadBtn.addEventListener('mouseenter', function() {
                this.style.background = '#1a6bc7';
                this.style.transform = 'translateY(-1px)';
            });
            downloadBtn.addEventListener('mouseleave', function() {
                this.style.background = '#2383e2';
                this.style.transform = 'translateY(0)';
            });

            actionSection.appendChild(downloadBtn);

            // 如果是临时文件，添加清理按钮
            if (result.temp_filepath) {
                const cleanupBtn = document.createElement('button');
                cleanupBtn.className = 'btn btn-secondary';
                cleanupBtn.style.cssText = `
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    padding: 6px 12px;
                    background: #f1f1f0;
                    color: #2d2d2d;
                    border: 1px solid #e9e9e7;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 500;
                    transition: all 0.15s ease;
                    white-space: nowrap;
                    cursor: pointer;
                `;
                cleanupBtn.innerHTML = '<i class="fas fa-trash"></i> 清理临时文件';

                // 添加点击事件
                cleanupBtn.addEventListener('click', () => {
                    cleanupTempFile(result, type === 'bgm' ? 'bgm' : (type === 'thumbnail' ? 'thumbnail' : 'video'));
                });

                actionSection.appendChild(cleanupBtn);
            }
        }
        
        // 组装完整卡片
        resultCard.appendChild(infoSection);
        resultCard.appendChild(actionSection);
        
        resultsContent.appendChild(resultCard);
    });
    
    // 添加批量下载按钮
    const successResults = results.filter(result => result.status === 'success' && (result.temp_filepath || result.filepath));
    if (successResults.length > 1) {
        const batchDownloadContainer = document.createElement('div');
        batchDownloadContainer.style.cssText = `
            margin-top: 20px;
            padding: 16px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            text-align: center;
        `;
        
        const batchDownloadBtn = document.createElement('button');
        batchDownloadBtn.className = 'btn';
        batchDownloadBtn.style.cssText = `
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 24px;
            background: #059669;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s ease;
        `;
        batchDownloadBtn.innerHTML = '<i class="fas fa-download"></i> 批量下载 (' + successResults.length + ' 个文件)';
        
        // 添加悬停效果
        batchDownloadBtn.addEventListener('mouseenter', function() {
            this.style.background = '#047857';
            this.style.transform = 'translateY(-1px)';
        });
        batchDownloadBtn.addEventListener('mouseleave', function() {
            this.style.background = '#059669';
            this.style.transform = 'translateY(0)';
        });
        
        // 添加点击事件
        batchDownloadBtn.addEventListener('click', function() {
            showBatchSaveDialog(successResults);
        });
        
        batchDownloadContainer.appendChild(batchDownloadBtn);
        resultsContent.appendChild(batchDownloadContainer);
    }
    
    resultsSection.classList.add('active');
}

// 创建信息行的辅助函数
function createInfoRow(label, value) {
    const row = document.createElement('div');
    row.style.cssText = 'display: flex; gap: 8px;';
    
    const labelEl = document.createElement('span');
    labelEl.style.cssText = 'font-size: 12px; color: #6b7280; min-width: 60px; flex-shrink: 0;';
    labelEl.textContent = label + ':';
    
    const valueEl = document.createElement('span');
    valueEl.style.cssText = 'font-size: 14px; color: #2d2d2d; word-break: break-all; line-height: 1.4;';
    valueEl.textContent = value;
    
    row.appendChild(labelEl);
    row.appendChild(valueEl);
    
    return row;
}

// 从文件路径中提取文件名
function getFileName(filepath) {
    return filepath.split(/[\\/]/).pop() || filepath;
}

// 文件上传相关功能已移除

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

// 下载临时文件
async function downloadTempFile(result, fileType = 'video') {
    try {
        const response = await fetch('/api/download_temp_file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                temp_filepath: result.temp_filepath || result.filepath,
                download_filename: result.download_filename || getFileName(result.temp_filepath || result.filepath),
                file_type: fileType
            })
        });

        if (!response.ok) {
            throw new Error(result.error || '下载失败');
        }

        // 创建下载链接
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = result.download_filename || getFileName(result.temp_filepath || result.filepath);
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        showAlert('文件下载已开始', 'success');

    } catch (error) {
        console.error('下载错误:', error);
        showAlert(`下载失败: ${error.message}`, 'error');
    }
}

// 清理临时文件
async function cleanupTempFile(result, fileType = 'video') {
    try {
        const response = await fetch('/api/cleanup_temp_file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                temp_filepath: result.temp_filepath,
                file_type: fileType
            })
        });

        if (!response.ok) {
            throw new Error('清理失败');
        }

        const data = await response.json();
        showAlert(data.message || '临时文件已清理', 'success');

        // 更新UI，移除清理按钮
        const resultCard = document.querySelector(`[data-result-url="${result.url}"]`);
        if (resultCard) {
            const cleanupBtn = resultCard.querySelector('.cleanup-btn');
            if (cleanupBtn) {
                cleanupBtn.remove();
            }
        }

    } catch (error) {
        console.error('清理错误:', error);
        showAlert(`清理失败: ${error.message}`, 'error');
    }
}

// 下载文件（保留原有功能）
function downloadFile(filepath) {
    window.open(`/download/${encodeURIComponent(filepath)}`, '_blank');
}

// 显示批量另存为对话框
function showBatchSaveDialog(successResults) {
    // 创建模态对话框
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    `;
    
    const dialog = document.createElement('div');
    dialog.style.cssText = `
        background: white;
        border-radius: 12px;
        padding: 24px;
        max-width: 500px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    `;
    
    // 标题
    const title = document.createElement('h3');
    title.style.cssText = `
        margin: 0 0 16px 0;
        font-size: 18px;
        font-weight: 600;
        color: #1f2937;
    `;
    title.textContent = '批量另存为文件';
    
    // 说明文字
    const description = document.createElement('p');
    description.style.cssText = `
        margin: 0 0 20px 0;
        font-size: 14px;
        color: #6b7280;
        line-height: 1.5;
    `;
    description.textContent = `即将下载 ${successResults.length} 个文件。由于浏览器安全限制，系统将逐个打开下载链接，请在浏览器中选择保存位置。`;
    
    // 文件列表
    const fileList = document.createElement('div');
    fileList.style.cssText = `
        margin: 0 0 20px 0;
        max-height: 200px;
        overflow-y: auto;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 12px;
        background: #f9fafb;
    `;
    
    const listTitle = document.createElement('div');
    listTitle.style.cssText = `
        font-size: 12px;
        font-weight: 600;
        color: #374151;
        margin-bottom: 8px;
    `;
    listTitle.textContent = '文件列表:';
    fileList.appendChild(listTitle);
    
    successResults.forEach((result, index) => {
        const fileItem = document.createElement('div');
        fileItem.style.cssText = `
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 4px;
            padding: 4px 0;
            border-bottom: 1px solid #e5e7eb;
        `;
        const filename = result.download_filename || getFileName(result.temp_filepath || result.filepath);
        fileItem.textContent = `${index + 1}. ${filename}`;
        fileList.appendChild(fileItem);
    });
    
    // 按钮区域
    const buttonArea = document.createElement('div');
    buttonArea.style.cssText = `
        display: flex;
        gap: 12px;
        justify-content: flex-end;
    `;
    
    // 取消按钮
    const cancelBtn = document.createElement('button');
    cancelBtn.style.cssText = `
        padding: 8px 16px;
        border: 1px solid #d1d5db;
        background: white;
        color: #374151;
        border-radius: 6px;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.15s ease;
    `;
    cancelBtn.textContent = '取消';
    cancelBtn.addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    // 确认按钮
    const confirmBtn = document.createElement('button');
    confirmBtn.style.cssText = `
        padding: 8px 16px;
        border: none;
        background: #059669;
        color: white;
        border-radius: 6px;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.15s ease;
    `;
    confirmBtn.textContent = '开始下载';
    confirmBtn.addEventListener('click', () => {
        document.body.removeChild(modal);
        startBatchDownload(successResults);
    });
    
    buttonArea.appendChild(cancelBtn);
    buttonArea.appendChild(confirmBtn);
    
    // 组装对话框
    dialog.appendChild(title);
    dialog.appendChild(description);
    dialog.appendChild(fileList);
    dialog.appendChild(buttonArea);
    modal.appendChild(dialog);
    
    // 点击背景关闭
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
    
    document.body.appendChild(modal);
}

// 开始批量下载
async function startBatchDownload(successResults) {
    showAlert('开始批量下载，文件将逐个下载到您选择的位置', 'success');

    // 逐个下载临时文件，间隔500ms避免浏览器阻止
    for (let index = 0; index < successResults.length; index++) {
        const result = successResults[index];

        try {
            await new Promise(resolve => setTimeout(resolve, 500)); // 延迟
            await downloadTempFile(result);
        } catch (error) {
            console.error(`下载文件 ${index + 1} 失败:`, error);
        }

        // 显示进度
        if (index === successResults.length - 1) {
            setTimeout(() => {
                showAlert('批量下载完成，请检查浏览器下载', 'success');
            }, 500);
        }
    }
}