// 存储Base64字符串
let imageBase64 = '';
let imageTailBase64 = '';
let currentVideoId = null;
let currentTaskId = null;

// 初始化懒加载功能
function initLazyLoading() {
    // 获取所有带有data-src属性的视频元素
    const videos = document.querySelectorAll('video source[data-src]');
    console.log(`找到 ${videos.length} 个需要懒加载的视频元素`);
    
    if (videos.length > 0) {
        // 创建交叉观察器
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // 获取视频元素
                    const video = entry.target;
                    // 获取所有带有data-src属性的source元素
                    const sources = video.querySelectorAll('source[data-src]');
                    sources.forEach(source => {
                        // 将data-src的值赋给src
                        source.src = source.dataset.src;
                        // 移除data-src属性
                        source.removeAttribute('data-src');
                    });
                    // 重新加载视频
                    video.load();
                    // 设置自动播放
                    video.setAttribute('autoplay', '');
                    // 停止观察该元素
                    observer.unobserve(video);
                }
            });
        }, { rootMargin: '100px', threshold: 0.1 });
        
        // 对每个视频元素进行观察
        videos.forEach(source => {
            // 观察视频元素的父元素（即<video>标签）
            observer.observe(source.parentElement);
        });
    }
}

// 初始化页面
$(document).ready(function() {
    // 获取URL参数
    function getUrlParameter(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    }

    // 处理URL参数
    const imageUrl = getUrlParameter('image');
    const prompt = getUrlParameter('prompt');

    if (imageUrl) {
        // 从URL获取图片并设置到表单
        fetch(imageUrl)
            .then(response => response.blob())
            .then(blob => {
                const file = new File([blob], 'image.png', { type: 'image/png' });
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                
                // 设置文件输入框的文件
                const fileInput = $('#image')[0];
                fileInput.files = dataTransfer.files;
                
                // 触发change事件以显示预览
                $(fileInput).trigger('change');
            });
    }

    if (prompt) {
        // 设置提示词
        $('#prompt').val(prompt);
    }

    // 初始化主题 - 默认使用黑色主题
    initDarkTheme();
    
    // 初始化回到顶部按钮
    initBackToTop();
    
    // 加载视频列表
    loadVideos();
    
    // 绑定创建按钮事件
    $('#createNewVideo').on('click', function() {
        $('#sidebar').addClass('active');
        $('#mainContent').addClass('sidebar-active');
    });
    
    // 绑定关闭侧边栏事件
    $('#closeSidebar').on('click', function() {
        $('#sidebar').removeClass('active');
        $('#mainContent').removeClass('sidebar-active');
    });

    // 图片预览功能
    $('#image').change(function() {
        if (this.files && this.files[0]) {
            processImage(this.files[0], '#imagePreview', function(base64) {
                imageBase64 = base64;
            });
        }
    });

    $('#image_tail').change(function() {
        if (this.files && this.files[0]) {
            processImage(this.files[0], '#imageTailPreview', function(base64) {
                imageTailBase64 = base64;
            });
        }
    });

    // 表单提交
    $('#videoGenerateForm').on('submit', function(e) {
        e.preventDefault();
        
        if (!imageBase64) {
            alert('请选择首帧图片');
            return;
        }

        $('.loading').show();
        $('button[type="submit"]').prop('disabled', true);
        
        // 构建请求数据
        const formData = {
            image: imageBase64,
            prompt: $('#prompt').val(),
            negative_prompt: $('#negative_prompt').val(),
            model_name: $('#model_name').val(),
            mode: $('#mode').val(),
            duration: $('#duration').val(),
            cfg_scale: $('#cfg_scale').val()
        };
        
        // 如果有尾帧图片，添加到请求数据
        if (imageTailBase64) {
            formData.image_tail = imageTailBase64;
        }
        
        // 发送请求
        $.ajax({
            url: '/generate',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                if (response.success) {
                    // 创建加载中的卡片
                    const loadingCard = createLoadingCard(response.task_id);
                    
                    // 确保创建按钮在最前面
                    const createBtn = $('#createNewVideo');
                    if (createBtn.length > 0) {
                        createBtn.detach();
                        $('#videoGrid').prepend(createBtn);
                    }
                    
                    // 将加载中的卡片添加到视频墙的开头（紧跟在创建按钮后面）
                    createBtn.after(loadingCard);
                    
                    // 关闭侧边栏
                    $('#sidebar').removeClass('active');
                    $('#mainContent').removeClass('sidebar-active');
                    
                    // 重置表单
                    $('#videoGenerateForm')[0].reset();
                    $('#imagePreview, #imageTailPreview').hide();
                    imageBase64 = '';
                    imageTailBase64 = '';
                    
                    // 定时检查任务状态
                    setTimeout(function() {
                        checkTaskStatus(response.task_id);
                    }, 5000);
                } else {
                    alert('提交失败：' + response.message);
                }
            },
            error: function(xhr, status, error) {
                console.error('请求失败:', xhr.responseText);
                alert('提交失败：' + (xhr.responseJSON ? xhr.responseJSON.message : error));
            },
            complete: function() {
                $('.loading').hide();
                $('button[type="submit"]').prop('disabled', false);
            }
        });
    });

    // 绑定视频卡片点击事件（使用事件委托）
    $('#videoGrid').on('click', '.video-card video', function(e) {
        e.stopPropagation();
        const videoCard = $(this).closest('.video-card');
        const taskId = videoCard.data('task-id');
        const videoId = videoCard.data('video-id');
        openVideoModal(taskId, videoId);
    });

    // 绑定删除视频按钮事件
    $('#deleteVideo').on('click', function() {
        if (currentTaskId && confirm('确定要删除这个视频任务吗？此操作不可恢复。')) {
            deleteTask(currentTaskId);
        }
    });

    // 绑定延长视频按钮事件
    $('#extendVideo').on('click', function() {
        if (currentVideoId) {
            extendVideo(currentVideoId);
        }
    });
});

// 图片处理函数
function processImage(file, previewId, callback) {
    // 检查文件格式
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!validTypes.includes(file.type)) {
        alert('只支持 JPG/JPEG/PNG 格式的图片');
        return false;
    }
    
    // 检查文件大小（10MB）
    if (file.size > 10 * 1024 * 1024) {
        alert('图片大小不能超过10MB');
        return false;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const img = new Image();
        img.onload = function() {
            // 检查分辨率和宽高比
            const width = img.width;
            const height = img.height;
            
            if (width < 300 || height < 300) {
                alert('图片分辨率不能小于300*300px');
                return false;
            }
            
            const ratio = width / height;
            if (ratio < 0.4 || ratio > 2.5) {
                alert('图片宽高比必须在1:2.5到2.5:1之间');
                return false;
            }
            
            // 显示预览
            $(previewId).attr('src', e.target.result).show();
            
            // 提取Base64字符串（移除前缀）
            const base64String = e.target.result.split(',')[1];
            if (callback) callback(base64String);
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

// 加载视频列表
function loadVideos() {
    $.ajax({
        url: '/api/videos',
        type: 'GET',
        success: function(response) {
            if (response.success) {
                const videos = response.data;
                // 清空视频网格，保留创建按钮
                $('#videoGrid').empty().append('<div class="floating-create-btn" id="createNewVideo"><i class="fas fa-plus fa-lg"></i></div>');
                
                // 按创建时间从新到旧排序，处理created_at为null的情况
                videos.sort((a, b) => {
                    if (!a.created_at) return 1;
                    if (!b.created_at) return -1;
                    return new Date(b.created_at) - new Date(a.created_at);
                });
                
                // 先创建所有视频卡片，以固定占位
                videos.forEach(function(video) {
                    const videoCard = createVideoCard(video);
                    $('#videoGrid').append(videoCard); // 使用append，因为已经按时间排序
                });
                
                // 初始化懒加载
                initLazyLoading();
                
                // 重新绑定创建按钮事件
                $('#createNewVideo').on('click', function() {
                    $('#sidebar').addClass('active');
                    $('#mainContent').addClass('sidebar-active');
                });
            } else {
                console.error('加载视频失败:', response.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('请求失败:', xhr.responseText);
        }
    });
}

// 创建视频卡片
function createVideoCard(video) {
    const card = $('<div>').addClass('video-card').attr('data-task-id', video.task_id).attr('data-video-id', video.video_id);
    
    // 视频元素 - 使用懒加载
    const videoElement = $('<video loop muted playsinline>');
    // 使用data-src代替src实现懒加载
    videoElement.append($('<source>').attr('data-src', video.url).attr('type', 'video/mp4'));
    
    // 设置视频卡片的预设尺寸，避免加载时的布局跳动
    // 不再使用固定的16:9比例，而是让视频根据其实际比例显示
    videoElement.css({
        'width': '100%',
        'height': 'auto',
        'background-color': 'var(--card-background, #f0f0f0)'
    });
    
    // 视频加载后根据实际比例调整尺寸
    videoElement.on('loadedmetadata', function() {
        const actualRatio = this.videoWidth / this.videoHeight;
        $(this).css('aspect-ratio', `${actualRatio}`);
    });
    
    card.append(videoElement);
    
    // 添加提示词信息图标
    if (video.prompt) {
        const promptInfo = $('<div>').addClass('prompt-info');
        const infoIcon = $('<div>').addClass('info-icon').html('i');
        const tooltip = $('<div>').addClass('prompt-tooltip').text(video.prompt);
        
        // 添加点击复制功能
        infoIcon.on('click', function(e) {
            e.stopPropagation();
            // 创建临时文本区域
            const tempTextArea = $('<textarea>');
            tempTextArea.val(video.prompt);
            $('body').append(tempTextArea);
            tempTextArea.select();
            document.execCommand('copy');
            tempTextArea.remove();
            
            // 显示复制成功提示
            Swal.fire({
                title: '已复制到剪贴板',
                text: video.prompt,
                icon: 'success',
                timer: 1500,
                showConfirmButton: false
            });
        });
        
        promptInfo.append(infoIcon, tooltip);
        card.append(promptInfo);
    }
    
    // 卡片覆盖层（操作按钮）
    const overlay = $('<div>').addClass('card-overlay');
    overlay.append(
        $('<button>').addClass('btn-icon').html('<i class="fas fa-expand"></i>').attr('title', '查看详情').on('click', function(e) {
            e.stopPropagation();
            const videoId = video.video_id || `local_${Math.floor(Math.random() * 10000)}`;
            openVideoModal(video.task_id, videoId);
        }),
        $('<button>').addClass('btn-icon').html('<i class="fas fa-clock"></i>').attr('title', '延长视频').on('click', function(e) {
            e.stopPropagation();
            extendVideo(video.video_id);
        }),
        $('<a>').addClass('btn-icon').html('<i class="fas fa-download"></i>').attr('title', '下载视频').attr('href', video.url).attr('download', ''),
        $('<button>').addClass('btn-icon').html('<i class="fas fa-trash"></i>').attr('title', '删除任务').on('click', function(e) {
            e.stopPropagation();
            if (confirm('确定要删除这个视频任务吗？此操作不可恢复。')) {
                deleteTask(video.task_id);
            }
        })
    );
    card.append(overlay);
    
    return card;
}

// 创建加载中的卡片
function createLoadingCard(taskId) {
    const card = $('<div>').addClass('video-card loading-card').attr('data-task-id', taskId);
    
    const loadingPlaceholder = $('<div>').addClass('loading-placeholder');
    loadingPlaceholder.append($('<div>').addClass('spinner-border text-secondary').append($('<span>').addClass('visually-hidden').text('Loading...')));
    loadingPlaceholder.append($('<p>').text('视频生成中...'));
    
    // 设置加载中卡片的预设尺寸，与视频卡片保持一致
    loadingPlaceholder.css({
        'width': '100%',
        'aspect-ratio': '16/9',
        'background-color': 'var(--card-background, #f0f0f0)',
        'display': 'flex',
        'flex-direction': 'column',
        'align-items': 'center',
        'justify-content': 'center'
    });
    
    card.append(loadingPlaceholder);
    return card;
}

// 检查任务状态
function checkTaskStatus(taskId) {
    console.log(`[DEBUG] 开始检查任务状态: ${taskId}`);
    
    $.ajax({
        url: `/api/task_status/${taskId}`,
        type: 'GET',
        success: function(response) {
            console.log(`[DEBUG] 任务状态响应:`, response);
            
            if (response.success) {
                const task = response.data;
                console.log(`[DEBUG] 任务状态: ${task.status}, 视频数量: ${task.videos ? task.videos.length : 0}`);
                
                // 检查是否已存在加载中的卡片
                const loadingCard = $(`.video-card[data-task-id="${taskId}"]`);
                
                // 如果没有加载中的卡片，且任务状态为submitted或processing，创建一个
                if (loadingCard.length === 0 && (task.status === 'submitted' || task.status === 'processing')) {
                    const newLoadingCard = createLoadingCard(taskId);
                    // 确保创建按钮在最前面
                    const createBtn = $('#createNewVideo');
                    if (createBtn.length > 0) {
                        createBtn.after(newLoadingCard);
                    } else {
                        $('#videoGrid').prepend(newLoadingCard);
                    }
                }
                
                // 如果任务成功且有视频
                if (task.status === 'succeed' && task.videos && task.videos.length > 0) {
                    // 查找对应的加载中占位卡片
                    const currentCard = $(`.video-card[data-task-id="${taskId}"]`);
                    
                    if (currentCard.length > 0) {
                        // 检查是否是延长视频任务
                        const isExtendTask = task.parameters && task.parameters.operation === 'extend';
                        
                        // 如果是延长视频任务，确保视频已下载到本地
                        if (isExtendTask && task.videos[0].url && !task.videos[0].downloaded) {
                            console.log(`[INFO] 检测到延长视频任务完成，但视频未下载，正在触发下载: ${taskId}`);
                            // 触发视频下载
                            $.ajax({
                                url: `/api/download_video/${taskId}/${task.videos[0].id}`,
                                type: 'GET',
                                success: function(downloadResponse) {
                                    console.log(`[INFO] 延长视频下载请求成功: ${JSON.stringify(downloadResponse)}`);
                                    // 下载请求成功后，重新检查任务状态
                                    setTimeout(function() {
                                        checkTaskStatus(taskId);
                                    }, 3000);
                                },
                                error: function(xhr) {
                                    console.error(`[ERROR] 延长视频下载请求失败: ${xhr.responseText}`);
                                    // 即使下载失败，也继续处理
                                    updateVideoCard();
                                }
                            });
                            return;
                        }
                        
                        // 更新视频卡片
                        function updateVideoCard() {
                            console.log(`[DEBUG] 更新视频卡片: ${taskId}`);
                            const videoCard = createVideoCard({
                                task_id: task.task_id,
                                video_id: task.videos[0].id,
                                url: task.videos[0].local_url || task.videos[0].url,
                                prompt: task.prompt,
                                created_at: task.created_at
                            });
                            
                            console.log(`[DEBUG] 替换加载中卡片为视频卡片`);
                            currentCard.replaceWith(videoCard);
                            
                            // 对新添加的视频应用懒加载
                            const newVideo = $(`.video-card[data-task-id="${taskId}"] video`)[0];
                            if (newVideo) {
                                const observer = new IntersectionObserver((entries) => {
                                    entries.forEach(entry => {
                                        if (entry.isIntersecting) {
                                            const video = entry.target;
                                            const sources = video.querySelectorAll('source[data-src]');
                                            sources.forEach(source => {
                                                source.src = source.dataset.src;
                                                source.removeAttribute('data-src');
                                            });
                                            video.load();
                                            video.setAttribute('autoplay', '');
                                            observer.unobserve(video);
                                        }
                                    });
                                }, { rootMargin: '100px', threshold: 0.1 });
                                observer.observe(newVideo);
                            }
                            
                            // 显示成功消息
                            Swal.fire({
                                title: '视频生成成功',
                                text: '视频已成功生成',
                                icon: 'success',
                                timer: 2000,
                                showConfirmButton: false
                            });
                        }
                        
                        // 执行更新视频卡片
                        updateVideoCard();
                    }
                } else if (task.status === 'failed') {
                    // 任务失败，显示错误信息
                    $(`.video-card[data-task-id="${taskId}"]`).remove();
                    Swal.fire({
                        title: '视频生成失败',
                        text: task.status_msg || '未知错误',
                        icon: 'error',
                        confirmButtonText: '确定'
                    });
                } else if (task.status === 'submitted' || task.status === 'processing') {
                    // 任务仍在处理中，继续检查
                    console.log(`[DEBUG] 任务仍在处理中，30秒后再次检查`);
                    setTimeout(function() {
                        checkTaskStatus(taskId);
                    }, 30000);
                }
            } else {
                console.error('[ERROR] 检查任务状态失败:', response.message);
                
                // 尝试再次检查
                setTimeout(function() {
                    checkTaskStatus(taskId);
                }, 10000);
            }
        },
        error: function(xhr, status, error) {
            console.error('[ERROR] 请求失败:', xhr.responseText);
            
            // 尝试再次检查
            setTimeout(function() {
                checkTaskStatus(taskId);
            }, 10000);
        }
    });
}

// 打开视频模态框
function openVideoModal(taskId, videoId) {
    currentTaskId = taskId;
    currentVideoId = videoId;
    
    // 显示加载状态
    $('.loading-overlay').show();
    
    $.ajax({
        url: `/api/video_detail/${taskId}/${videoId}`,
        type: 'GET',
        success: function(response) {
            if (response.success) {
                const video = response.data;
                
                // 构建视频详情内容
                const videoDetail = `
                    <div class="video-container">
                        <video id="modalVideo" controls autoplay loop>
                            <source src="${video.url}" type="video/mp4">
                        </video>
                        <div class="video-loading">加载中...</div>
                    </div>
                    <div class="video-controls">
                        <div class="control-group">
                            <button id="playPauseBtn"><i class="fas fa-play"></i></button>
                            <button id="muteBtn"><i class="fas fa-volume-up"></i></button>
                            <select id="playbackSpeed">
                                <option value="0.5">0.5x</option>
                                <option value="1" selected>1x</option>
                                <option value="1.5">1.5x</option>
                                <option value="2">2x</option>
                            </select>
                        </div>
                        <div class="control-group">
                            <button id="loopBtn" class="active"><i class="fas fa-redo"></i></button>
                        </div>
                    </div>
                    <div class="video-info-container mt-4">
                        <div class="info-section">
                            <div class="section-title">视频信息</div>
                            <div class="task-info"><span>任务ID:</span> ${video.task_id}</div>
                            <div class="task-info"><span>视频ID:</span> ${video.video_id || '本地视频'}</div>
                            <div class="task-info"><span>创建时间:</span> ${video.created_at ? new Date(video.created_at).toLocaleString() : '未知'}</div>
                            <div class="task-info"><span>状态:</span> <span class="status status-${video.status || 'succeed'}">${getStatusText(video.status || 'succeed')}</span></div>
                        </div>
                        
                        <div class="info-section">
                            <div class="section-title">生成参数</div>
                            <div class="task-info"><span>模型:</span> ${video.model_name || '未知'}</div>
                            <div class="task-info"><span>模式:</span> ${video.mode || '标准模式'}</div>
                            <div class="task-info"><span>时长:</span> ${video.duration || '未知'} 秒</div>
                            <div class="task-info"><span>自由度:</span> ${video.cfg_scale || '0.5'}</div>
                        </div>
                    </div>
                    
                    <div class="video-prompt-container">
                        <div class="prompt-section">
                            <div class="prompt-title">提示词</div>
                            <div class="prompt-text">${video.prompt || '无提示词'}</div>
                        </div>
                        ${video.negative_prompt ? `
                        <div class="prompt-section">
                            <div class="prompt-title">负向提示词</div>
                            <div class="prompt-text">${video.negative_prompt}</div>
                        </div>` : ''}
                    </div>
                `;
                
                // 更新模态框内容
                $('#videoDetailContainer').html(videoDetail);
                
                // 初始化视频控制
                initVideoControls();
                
                // 显示模态框
                const videoModal = new bootstrap.Modal(document.getElementById('videoPreviewModal'));
                videoModal.show();
                
                // 更新下载按钮链接
                $('#downloadVideo').attr('href', video.url);
                
                // 根据视频类型显示/隐藏延长按钮
                if (video.video_id && video.video_id.startsWith('local_')) {
                    $('#extendVideo').hide();
                } else {
                    $('#extendVideo').show();
                }
                
                // 根据视频来源显示/隐藏云端拉取按钮
                if (video.cloud_url && !video.local_url) {
                    $('#pullFromCloud').show();
                } else {
                    $('#pullFromCloud').hide();
                }
            } else {
                alert('获取视频详情失败：' + response.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('请求失败:', xhr.responseText);
            alert('获取视频详情失败：' + (xhr.responseJSON ? xhr.responseJSON.message : error));
        },
        complete: function() {
            // 隐藏加载状态
            $('.loading-overlay').hide();
        }
    });
}

// 初始化视频控制
function initVideoControls() {
    const video = document.getElementById('modalVideo');
    const playPauseBtn = document.getElementById('playPauseBtn');
    const muteBtn = document.getElementById('muteBtn');
    const playbackSpeed = document.getElementById('playbackSpeed');
    const loopBtn = document.getElementById('loopBtn');
    
    if (!video || !playPauseBtn || !muteBtn || !playbackSpeed || !loopBtn) return;
    
    // 视频加载事件
    video.addEventListener('loadeddata', function() {
        $('.video-loading').hide();
    });
    
    // 视频错误事件
    video.addEventListener('error', function() {
        $('.video-loading').text('视频加载失败').show();
    });
    
    // 播放/暂停按钮
    playPauseBtn.addEventListener('click', function() {
        if (video.paused) {
            video.play();
            playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        } else {
            video.pause();
            playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        }
    });
    
    // 静音按钮
    muteBtn.addEventListener('click', function() {
        video.muted = !video.muted;
        muteBtn.innerHTML = video.muted ? '<i class="fas fa-volume-mute"></i>' : '<i class="fas fa-volume-up"></i>';
    });
    
    // 播放速度
    playbackSpeed.addEventListener('change', function() {
        video.playbackRate = parseFloat(this.value);
    });
    
    // 循环播放
    loopBtn.addEventListener('click', function() {
        video.loop = !video.loop;
        loopBtn.classList.toggle('active');
    });
    
    // 视频播放/暂停事件
    video.addEventListener('play', function() {
        playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
    });
    
    video.addEventListener('pause', function() {
        playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
    });
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'submitted': '已提交',
        'processing': '处理中',
        'succeed': '已完成',
        'failed': '失败'
    };
    return statusMap[status] || status;
}

// 删除任务
function deleteTask(taskId) {
    $.ajax({
        url: `/api/task/${taskId}`,
        type: 'DELETE',
        success: function(response) {
            if (response.success) {
                // 关闭模态框
                const videoModal = bootstrap.Modal.getInstance(document.getElementById('videoPreviewModal'));
                if (videoModal) videoModal.hide();
                
                // 从视频墙中移除对应的卡片
                $(`.video-card[data-task-id="${taskId}"]`).fadeOut(300, function() {
                    $(this).remove();
                });
                
                // 显示成功消息
                Swal.fire({
                    title: '删除成功',
                    text: '视频任务已成功删除',
                    icon: 'success',
                    timer: 1500,
                    showConfirmButton: false
                });
            } else {
                alert('删除失败：' + response.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('请求失败:', xhr.responseText);
            alert('删除失败：' + (xhr.responseJSON ? xhr.responseJSON.message : error));
        }
    });
}

// 延长视频
// 延长视频函数
function extendVideo(videoId) {
    // 弹出提示词输入对话框
    Swal.fire({
        title: '延长视频',
        html: `
            <div class="form-group">
                <label for="extendPrompt">请输入延长视频的提示词</label>
                <textarea id="extendPrompt" class="form-control" rows="3" placeholder="描述您希望延长的视频内容...">继续延长视频</textarea>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: '提交',
        cancelButtonText: '取消',
        preConfirm: () => {
            const prompt = document.getElementById('extendPrompt').value;
            if (!prompt) {
                Swal.showValidationMessage('请输入提示词');
                return false;
            }
            return prompt;
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const prompt = result.value;
            // 显示加载状态
            $('.loading-overlay').show();
            
            // 发送延长视频请求
            $.ajax({
                url: `/api/extend/${videoId}`,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    prompt: prompt
                }),
                success: function(response) {
                    // 原有的成功处理逻辑...
                    if (response.success) {
                        // 关闭模态框
                        const videoModal = bootstrap.Modal.getInstance(document.getElementById('videoPreviewModal'));
                        if (videoModal) videoModal.hide();
                        
                        // 显示成功消息
                        Swal.fire({
                            title: '请求已提交',
                            text: '视频延长任务已提交，请稍后查看结果',
                            icon: 'success',
                            timer: 2000,
                            showConfirmButton: false
                        });
                        
                        // 创建加载中的卡片
                        const loadingCard = createLoadingCard(response.task_id);
                        
                        // 确保创建按钮在最前面
                        const createBtn = $('#createNewVideo');
                        if (createBtn.length > 0) {
                            createBtn.detach();
                            $('#videoGrid').prepend(createBtn);
                        }
                        
                        // 将加载中的卡片添加到视频墙的开头
                        createBtn.after(loadingCard);
                        
                        // 定时检查任务状态
                        setTimeout(function() {
                            checkTaskStatus(response.task_id);
                        }, 5000);
                    } else {
                        alert('延长视频失败：' + response.message);
                    }
                },
                error: function(xhr, status, error) {
                    console.error('请求失败:', xhr.responseText);
                    alert('延长视频失败：' + (xhr.responseJSON ? xhr.responseJSON.message : error));
                },
                complete: function() {
                    // 隐藏加载状态
                    $('.loading-overlay').hide();
                }
            });
        }
    });
}

// 初始化主题
function initTheme() {
    // 检查本地存储中的主题设置
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        $('#themeToggle i').removeClass('fa-moon').addClass('fa-sun');
        $('#themeToggle span').text('切换亮色');
    }
}

// 切换主题
function toggleTheme() {
    if (document.documentElement.getAttribute('data-theme') === 'dark') {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
        $('#themeToggle i').removeClass('fa-sun').addClass('fa-moon');
        $('#themeToggle span').text('切换暗色');
    } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        $('#themeToggle i').removeClass('fa-moon').addClass('fa-sun');
        $('#themeToggle span').text('切换亮色');
    }
}

// 初始化黑色主题
function initDarkTheme() {
    // 直接设置为黑色主题，无需检查本地存储
    document.documentElement.setAttribute('data-theme', 'dark');
    $('#themeToggle i').removeClass('fa-moon').addClass('fa-sun');
    $('#themeToggle span').text('切换亮色');
    
    // 保存到本地存储
    localStorage.setItem('theme', 'dark');
}

// 切换主题函数保持不变
function toggleTheme() {
    if (document.documentElement.getAttribute('data-theme') === 'dark') {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
        $('#themeToggle i').removeClass('fa-sun').addClass('fa-moon');
        $('#themeToggle span').text('切换暗色');
    } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        $('#themeToggle i').removeClass('fa-moon').addClass('fa-sun');
        $('#themeToggle span').text('切换亮色');
    }
}

// 初始化回到顶部按钮
function initBackToTop() {
    const backToTopBtn = document.getElementById('backToTop');
    
    // 监听滚动事件
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopBtn.classList.add('visible');
        } else {
            backToTopBtn.classList.remove('visible');
        }
    });
    
    // 点击回到顶部
    backToTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// 文生视频表单提交
$('#text2videoForm').on('submit', function(e) {
    e.preventDefault();
    
    $('.loading').show();
    $('button[type="submit"]').prop('disabled', true);
    
    // 构建请求数据
    const formData = {
        prompt: $('#t2v_prompt').val(),
        negative_prompt: $('#t2v_negative_prompt').val(),
        model_name: $('#t2v_model').val(),
        mode: $('#t2v_mode').val(),
        duration: $('#t2v_duration').val(),
        cfg_scale: $('#t2v_cfg_scale').val()
    };

    // 添加摄像机参数
    const cameraType = $('#t2v_camera_type').val();
    if (cameraType === 'simple') {
        formData.camera_control = {
            horizontal: $('#t2v_camera_horizontal').val(),
            vertical: $('#t2v_camera_vertical').val(),
            pan: $('#t2v_camera_pan').val(),
            tilt: $('#t2v_camera_tilt').val(),
            roll: $('#t2v_camera_roll').val(),
            zoom: $('#t2v_camera_zoom').val()
        };
    } else if (cameraType) {
        formData.camera_type = cameraType;
    }
    
    // 发送请求 - 修改为新的API路径
    $.ajax({
        url: '/api/text2video',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            if (response.success) {
                // 创建加载中的卡片
                const loadingCard = createLoadingCard(response.task_id);
                
                // 确保创建按钮在最前面
                const createBtn = $('#createNewVideo');
                if (createBtn.length > 0) {
                    createBtn.detach();
                    $('#videoGrid').prepend(createBtn);
                }
                
                // 将加载中的卡片添加到视频墙的开头（紧跟在创建按钮后面）
                createBtn.after(loadingCard);
                
                // 关闭侧边栏
                $('#sidebar').removeClass('active');
                $('#mainContent').removeClass('sidebar-active');
                
                // 重置表单
                $('#text2videoForm')[0].reset();
                
                // 定时检查任务状态 - 使用新的API路径
                setTimeout(function() {
                    checkTaskStatus(response.task_id);
                }, 5000);
            } else {
                alert('提交失败：' + response.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('请求失败:', xhr.responseText);
            alert('提交失败：' + (xhr.responseJSON ? xhr.responseJSON.message : error));
        },
        complete: function() {
            $('.loading').hide();
            $('button[type="submit"]').prop('disabled', false);
        }
    });
});