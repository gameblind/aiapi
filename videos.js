// 视频相关的JavaScript功能

// 全局变量
let imageBase64 = '';
let imageTailBase64 = '';
let videoModal = null;

// 处理图片上传
function processImage(file, previewSelector, callback) {
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            $(previewSelector).attr('src', e.target.result).show();
            if (callback) callback(e.target.result.split(',')[1]);
        };
        reader.readAsDataURL(file);
    }
}

// 加载视频列表
function loadVideos() {
    $.get('/api/videos/list')
        .then(data => {
            const videoGrid = $('#videoGrid');
            videoGrid.empty();
            
            data.forEach(video => {
                if (video.status === 'submitted' || video.status === 'processing') {
                    videoGrid.prepend(createLoadingCard(video.task_id));
                } else if (video.status === 'succeed' && video.url) {
                    videoGrid.prepend(createVideoCard(video));
                }
            });
            
            // 初始化延迟加载
            initLazyLoading();
        })
        .catch(error => {
            console.error('加载视频列表失败:', error);
        });
}

// 创建视频卡片
function createVideoCard(video) {
    const card = $('<div>').addClass('video-card').attr('data-task-id', video.task_id);
    
    const videoElement = $('<video>').attr('preload', 'none').prop('muted', true).prop('loop', true);
    videoElement.append($('<source>').attr('data-src', video.url).attr('type', 'video/mp4'));
    
    videoElement.css({
        'width': '100%',
        'height': 'auto',
        'background-color': 'var(--card-background, #f0f0f0)'
    });
    
    videoElement.on('loadedmetadata', function() {
        const actualRatio = this.videoWidth / this.videoHeight;
        $(this).css('aspect-ratio', `${actualRatio}`);
    });
    
    card.append(videoElement);
    
    if (video.prompt) {
        const promptInfo = $('<div>').addClass('prompt-info');
        const infoIcon = $('<div>').addClass('info-icon').html('i');
        const tooltip = $('<div>').addClass('prompt-tooltip').text(video.prompt);
        
        infoIcon.on('click', function(e) {
            e.stopPropagation();
            const tempTextArea = $('<textarea>');
            tempTextArea.val(video.prompt);
            $('body').append(tempTextArea);
            tempTextArea.select();
            document.execCommand('copy');
            tempTextArea.remove();
            
            const originalText = infoIcon.html();
            infoIcon.html('✓');
            setTimeout(() => infoIcon.html(originalText), 1000);
        });
        
        promptInfo.append(infoIcon, tooltip);
        card.append(promptInfo);
    }
    
    const overlay = $('<div>').addClass('card-overlay').append(
        $('<button>').addClass('btn-icon').html('<i class="fas fa-play"></i>').attr('title', '播放视频').on('click', function(e) {
            e.stopPropagation();
            showVideoDetail(video);
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

// 初始化延迟加载
function initLazyLoading() {
    const videos = document.querySelectorAll('.video-container video source[data-src]');
    
    if (videos.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const source = entry.target;
                    const video = source.parentElement;
                    
                    source.src = source.getAttribute('data-src');
                    video.load();
                    
                    observer.unobserve(video);
                    
                    video.addEventListener('mouseover', function() {
                        this.play().catch(() => {});
                    });
                    
                    video.addEventListener('mouseout', function() {
                        this.pause();
                        this.currentTime = 0;
                    });
                }
            });
        }, { rootMargin: '100px', threshold: 0.1 });
        
        videos.forEach(source => {
            observer.observe(source.parentElement);
        });
    }
}

// 显示视频详情
function showVideoDetail(video) {
    const modalContent = `
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-body">
                    <div id="videoDetailContainer" class="video-container">
                        <video controls>
                            <source src="${video.url}" type="video/mp4">
                        </video>
                        <div class="video-loading">
                            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                            加载中...
                        </div>
                        <div class="video-controls">
                            <div class="control-group">
                                <button id="toggleMute" title="静音切换"><i class="fas fa-volume-up"></i></button>
                                <select id="playbackSpeed" title="播放速度">
                                    <option value="0.5">0.5x</option>
                                    <option value="1" selected>1x</option>
                                    <option value="1.5">1.5x</option>
                                    <option value="2">2x</option>
                                </select>
                            </div>
                            <div class="control-group">
                                <button id="toggleFullscreen" title="全屏"><i class="fas fa-expand"></i></button>
                            </div>
                        </div>
                    </div>
                    ${video.prompt ? `<p id="modalPrompt">${video.prompt}</p>` : ''}
                </div>
            </div>
        </div>
    `;

    if (!videoModal) {
        videoModal = new bootstrap.Modal(document.createElement('div'));
        videoModal._element.classList.add('modal', 'fade');
        document.body.appendChild(videoModal._element);
    }

    videoModal._element.innerHTML = modalContent;
    videoModal.show();
    
    initVideoControls();
}

// 初始化视频控制功能
function initVideoControls() {
    const videoElement = $('#videoDetailContainer video')[0];
    if (!videoElement) return;
    
    $('#toggleFullscreen').on('click', function() {
        if (videoElement.requestFullscreen) {
            videoElement.requestFullscreen();
        } else if (videoElement.webkitRequestFullscreen) {
            videoElement.webkitRequestFullscreen();
        } else if (videoElement.msRequestFullscreen) {
            videoElement.msRequestFullscreen();
        }
        $(this).html('<i class="fas fa-compress"></i>');
    });
    
    $(document).on('fullscreenchange webkitfullscreenchange mozfullscreenchange MSFullscreenChange', function() {
        if (!document.fullscreenElement && !document.webkitFullscreenElement && 
            !document.mozFullScreenElement && !document.msFullscreenElement) {
            $('#toggleFullscreen').html('<i class="fas fa-expand"></i>');
        }
    });
}

// 删除任务
function deleteTask(taskId) {
    $.ajax({
        url: `/api/videos/${taskId}`,
        method: 'DELETE'
    })
    .then(data => {
        if (data.success) {
            $(`.video-card[data-task-id="${taskId}"]`).remove();
            if (videoModal) {
                videoModal.hide();
            }
            alert('视频已删除');
        } else {
            alert('删除失败: ' + (data.message || '未知错误'));
        }
    })
    .catch(error => {
        console.error('删除请求失败:', error);
        alert('删除失败，请检查网络连接');
    });
}

// 事件绑定
$(document).ready(function() {
    // 获取URL参数
    const urlParams = new URLSearchParams(window.location.search);
    const imageUrl = urlParams.get('image');
    const prompt = urlParams.get('prompt');

    if (imageUrl) {
        fetch(imageUrl)
            .then(response => response.blob())
            .then(blob => {
                const file = new File([blob], 'image.png', { type: 'image/png' });
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                
                const fileInput = $('#image')[0];
                fileInput.files = dataTransfer.files;
                $(fileInput).trigger('change');
            });
    }

    if (prompt) {
        $('#prompt').val(prompt);
    }

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

    // 视频控制事件
    $(document).on('click', '#toggleMute', function() {
        const video = document.querySelector('.video-container video');
        video.muted = !video.muted;
        
        if (video.muted) {
            $(this).html('<i class="fas fa-volume-mute"></i>');
        } else {
            $(this).html('<i class="fas fa-volume-up"></i>');
        }
    });
    
    $(document).on('change', '#playbackSpeed', function() {
        const video = document.querySelector('.video-container video');
        video.playbackRate = parseFloat(this.value);
    });
    
    // 视频加载事件
    $(document).on('loadstart', '.video-container video', function() {
        $(this).siblings('.video-loading').show();
    });
    
    $(document).on('canplay', '.video-container video', function() {
        $(this).siblings('.video-loading').hide();
    });
    
    $(document).on('error', '.video-container video', function() {
        $(this).siblings('.video-loading').hide();
        const videoContainer = $(this).parent();
        
        const errorMsg = $('<div class="video-error"></div>')
            .text('视频加载失败')
            .css({
                'position': 'absolute',
                'top': '50%',
                'left': '50%',
                'transform': 'translate(-50%, -50%)',
                'background': 'rgba(0, 0, 0, 0.7)',
                'color': 'white',
                'padding': '10px 20px',
                'border-radius': '4px'
            });
        
        videoContainer.append(errorMsg);
    });
});