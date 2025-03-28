// 全局变量
let currentVoiceId = null;
let allVoices = [];
let currentVoiceIndex = -1;

// 页面加载完成后执行
$(document).ready(function() {
    // 初始化主题
    initTheme();
    
    // 加载语音列表
    loadVoices();
    
    // 初始化回到顶部按钮
    initBackToTop();
    
    // 确保始终有一个空白音频卡
    ensureEmptyVoiceCard();
    
    // 侧边栏控制
    $('#createNewVoice').on('click', function() {
        $('#sidebar').addClass('active');
        $('#mainContent').addClass('sidebar-active');
    });
    
    $('#closeSidebar').on('click', function() {
        $('#sidebar').removeClass('active');
        $('#mainContent').removeClass('sidebar-active');
    });
    
    // 语速滑块值显示
    $('#tts_speed').on('input', function() {
        $('#tts_speed_value').text($(this).val());
    });
    
    // 文本转语音表单提交
    $('#ttsForm').on('submit', function(e) {
        e.preventDefault();
        
        const text = $('#tts_text').val().trim();
        if (!text) {
            alert('请输入文本内容');
            return;
        }
        
        // 显示加载中
        $('.loading').show();
        $('button[type="submit"]').prop('disabled', true);
        
        // 收集表单数据
        const formData = {
            text: text,
            voice_id: $('#tts_voice_id').val(),
            model: $('#tts_model').val(),
            speed: parseFloat($('#tts_speed').val())
        };
        
        // 发送请求
        $.ajax({
            url: '/api/voice/tts',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                if (response.success) {
                    // 创建成功，关闭侧边栏并刷新列表
                    $('#sidebar').removeClass('active');
                    $('#mainContent').removeClass('sidebar-active');
                    
                    // 创建一个加载中的卡片
                    const taskId = response.data.task_id;
                    const loadingCard = createLoadingCard(taskId, text);
                    
                    // 添加到网格中
                    const createBtn = $('#createNewVoice');
                    if (createBtn.length > 0) {
                        createBtn.after(loadingCard);
                    } else {
                        $('#voiceGrid').prepend(loadingCard);
                    }
                    
                    // 开始轮询任务状态
                    pollTaskStatus(taskId);
                    
                    // 重置表单
                    $('#ttsForm')[0].reset();
                    $('#tts_speed_value').text('1.0');
                } else {
                    alert('创建失败：' + (response.message || '未知错误'));
                }
            },
            error: function(xhr) {
                alert('请求失败：' + (xhr.responseJSON?.message || '服务器错误'));
            },
            complete: function() {
                $('.loading').hide();
                $('button[type="submit"]').prop('disabled', false);
            }
        });
    });
    
    // 语音转文本表单提交
    $('#asrForm').on('submit', function(e) {
        e.preventDefault();
        
        const audioFile = $('#asr_audio')[0].files[0];
        if (!audioFile) {
            alert('请选择音频文件');
            return;
        }
        
        // 检查文件格式和大小
        const validTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/x-m4a'];
        if (!validTypes.includes(audioFile.type) && 
            !audioFile.name.endsWith('.mp3') && 
            !audioFile.name.endsWith('.wav') && 
            !audioFile.name.endsWith('.m4a')) {
            alert('只支持 MP3/WAV/M4A 格式的音频');
            return;
        }
        
        if (audioFile.size > 10 * 1024 * 1024) {
            alert('音频文件大小不能超过10MB');
            return;
        }
        
        // 显示加载中
        $('.loading').show();
        $('button[type="submit"]').prop('disabled', true);
        
        // 创建FormData对象
        const formData = new FormData();
        formData.append('file', audioFile);
        
        // 发送请求
        $.ajax({
            url: '/api/voice/asr',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    // 显示识别结果
                    $('#asrResultText').text(response.data.text);
                    $('#asrResult').show();
                } else {
                    alert('识别失败：' + (response.message || '未知错误'));
                }
            },
            error: function(xhr) {
                alert('请求失败：' + (xhr.responseJSON?.message || '服务器错误'));
            },
            complete: function() {
                $('.loading').hide();
                $('button[type="submit"]').prop('disabled', false);
            }
        });
    });
    
    // 使用识别结果生成语音
    $('#useAsrResult').on('click', function() {
        const text = $('#asrResultText').text();
        if (text) {
            // 切换到TTS标签
            $('#tts-tab').tab('show');
            
            // 填充文本
            $('#tts_text').val(text);
            
            // 隐藏识别结果
            $('#asrResult').hide();
            
            // 重置ASR表单
            $('#asrForm')[0].reset();
            $('#asr_preview').hide();
        }
    });
    
    // 音频文件预览
    $('#asr_audio').on('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const url = URL.createObjectURL(file);
            $('#asr_preview').attr('src', url).show();
        } else {
            $('#asr_preview').hide();
        }
    });
    
    // 删除音频按钮点击事件
    $('#deleteVoice').on('click', function() {
        if (confirm('确定要删除这个音频吗？')) {
            const voiceId = currentVoiceId;
            
            $.ajax({
                url: '/api/voice/delete',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ task_id: voiceId }),
                success: function(response) {
                    if (response.success) {
                        // 关闭模态框并刷新页面
                        const modal = bootstrap.Modal.getInstance(document.getElementById('voicePreviewModal'));
                        modal.hide();
                        
                        // 从DOM中移除卡片
                        $(`.voice-card[data-task-id="${voiceId}"]`).remove();
                    } else {
                        alert('删除失败：' + (response.message || '未知错误'));
                    }
                },
                error: function(xhr) {
                    alert('请求失败：' + (xhr.responseJSON?.message || '服务器错误'));
                }
            });
        }
    });
    
    // 编辑重新生成按钮点击事件
    $('#editVoice').on('click', function() {
        const text = $('#modalText').text();
        const voice = $('#modalVoice').text();
        const model = $('#modalModel').text();
        
        // 打开侧边栏
        $('#sidebar').addClass('active');
        $('#mainContent').addClass('sidebar-active');
        
        // 切换到TTS标签
        $('#tts-tab').tab('show');
        
        // 填充表单
        $('#tts_text').val(text);
        $('#tts_voice_id').val(voice.toLowerCase());
        $('#tts_model').val(model.toLowerCase());
        
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('voicePreviewModal'));
        modal.hide();
    });
    
    // 模态框中的音频播放器事件
    $('#voicePreviewModal').on('show.bs.modal', function() {
        // 获取所有音频
        allVoices = $('.voice-card').toArray();
        // 找到当前音频的索引
        currentVoiceIndex = allVoices.findIndex(card => $(card).data('task-id') === currentVoiceId);
    });
    
    // 键盘导航
    $(document).on('keydown', function(e) {
        if ($('#voicePreviewModal').hasClass('show')) {
            if (e.key === 'ArrowLeft') {
                // 上一个音频
                if (currentVoiceIndex > 0) {
                    navigateVoice(currentVoiceIndex - 1);
                }
            } else if (e.key === 'ArrowRight') {
                // 下一个音频
                if (currentVoiceIndex < allVoices.length - 1) {
                    navigateVoice(currentVoiceIndex + 1);
                }
            }
        }
    });
});

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
        // 切换到亮色主题
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
        $('#themeToggle i').removeClass('fa-sun').addClass('fa-moon');
        $('#themeToggle span').text('切换暗色');
    } else {
        // 切换到暗色主题
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        $('#themeToggle i').removeClass('fa-moon').addClass('fa-sun');
        $('#themeToggle span').text('切换亮色');
    }
}

// 初始化回到顶部按钮
function initBackToTop() {
    const backToTopBtn = $('#backToTop');
    
    // 滚动事件
    $(window).on('scroll', function() {
        if ($(this).scrollTop() > 300) {
            backToTopBtn.addClass('visible');
        } else {
            backToTopBtn.removeClass('visible');
        }
    });
    
    // 点击事件
    backToTopBtn.on('click', function() {
        $('html, body').animate({ scrollTop: 0 }, 500);
    });
}

// 确保始终有一个空白音频卡
function ensureEmptyVoiceCard() {
    // 检查是否已经有空白卡
    if ($('.empty-voice-card').length === 0) {
        const emptyCard = createEmptyVoiceCard();
        $('#voiceGrid').prepend(emptyCard);
        
        // 绑定点击事件
        $('.empty-voice-card').on('click', function() {
            $('#sidebar').addClass('active');
            $('#mainContent').addClass('sidebar-active');
        });
    }
}

// 创建空白音频卡
function createEmptyVoiceCard() {
    return `
        <div class="voice-card empty-voice-card">
            <div class="voice-card-header">
                <div class="voice-text">点击创建新的语音任务</div>
            </div>
            <div class="voice-player">
                <div class="empty-placeholder">
                    <i class="fas fa-plus fa-3x"></i>
                    <p>TTS / ASR</p>
                </div>
            </div>
        </div>
    `;
}

// 加载语音列表
function loadVoices() {
    $.ajax({
        url: '/api/voice/list',
        type: 'GET',
        success: function(response) {
            if (response.success) {
                const voices = response.data;
                
                // 清空网格
                $('#voiceGrid').empty();
                
                // 确保有一个空白卡
                ensureEmptyVoiceCard();
                
                // 添加语音卡片
                voices.forEach(voice => {
                    const voiceCard = createVoiceCard(voice);
                    $('#voiceGrid').append(voiceCard);
                    
                    // 绑定事件
                    const card = $(`.voice-card[data-task-id="${voice.task_id}"]`);
                    bindCardEvents(card);
                });
            } else {
                console.error('加载语音列表失败：', response.message);
            }
        },
        error: function(xhr) {
            console.error('请求失败：', xhr.responseText);
        }
    });
}

// 创建语音卡片
function createVoiceCard(voice) {
    const statusClass = getStatusClass(voice.status);
    const statusText = getStatusText(voice.status);
    
    let audioElement = '';
    if (voice.status === 'succeed' && voice.audio_url) {
        audioElement = `<audio class="audio-player" controls src="${voice.audio_url}"></audio>`;
    } else {
        audioElement = `<div class="audio-placeholder">${statusText}</div>`;
    }
    
    return `
        <div class="voice-card" data-task-id="${voice.task_id}">
            <div class="voice-card-header">
                <span class="status ${statusClass}">${statusText}</span>
                <div class="voice-text">${voice.text}</div>
                <div class="voice-info">
                    <span>音色: ${voice.voice_id}</span>
                    <span>模型: ${voice.model}</span>
                </div>
            </div>
            <div class="voice-player">
                ${audioElement}
            </div>
            <div class="voice-actions">
                <div class="voice-buttons">
                    <button class="btn-icon btn-primary preview-voice" title="预览">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="btn-icon btn-success download-voice" title="下载" ${voice.status !== 'succeed' ? 'disabled' : ''}>
                        <i class="fas fa-download"></i>
                    </button>
                    <button class="btn-icon btn-warning edit-voice" title="编辑">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon btn-danger delete-voice" title="删除">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
}

// 创建加载中的卡片
function createLoadingCard(taskId, text) {
    return `
        <div class="voice-card loading-card" data-task-id="${taskId}">
            <div class="voice-card-header">
                <span class="status status-pending">等待处理</span>
                <div class="voice-text">${text}</div>
            </div>
            <div class="voice-player">
                <div class="loading-placeholder">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p>正在生成语音...</p>
                </div>
            </div>
        </div>
    `;
}

// 轮询任务状态
function pollTaskStatus(taskId) {
    const interval = setInterval(function() {
        $.ajax({
            url: `/api/voice/status?task_id=${taskId}`,
            type: 'GET',
            success: function(response) {
                if (response.success) {
                    const status = response.data.status;
                    
                    // 更新卡片状态
                    updateCardStatus(taskId, status);
                    
                    // 如果任务完成或失败，停止轮询
                    if (status === 'succeed' || status === 'failed') {
                        clearInterval(interval);
                        
                        // 如果成功，更新音频播放器
                        if (status === 'succeed') {
                            updateCardAudio(taskId, response.data.audio_url);
                        }
                    }
                } else {
                    console.error('获取任务状态失败：', response.message);
                    clearInterval(interval);
                }
            },
            error: function(xhr) {
                console.error('请求失败：', xhr.responseText);
                clearInterval(interval);
            }
        });
    }, 2000); // 每2秒轮询一次
}

// 更新卡片状态
function updateCardStatus(taskId, status) {
    const card = $(`.voice-card[data-task-id="${taskId}"]`);
    const statusClass = getStatusClass(status);
    const statusText = getStatusText(status);
    
    card.find('.status').removeClass('status-pending status-processing status-succeed status-failed')
        .addClass(statusClass)
        .text(statusText);
}

// 更新卡片音频
function updateCardAudio(taskId, audioUrl) {
    const card = $(`.voice-card[data-task-id="${taskId}"]`);
    
    // 替换加载占位符为音频播放器
    card.find('.loading-placeholder').replaceWith(`
        <audio class="audio-player" controls src="${audioUrl}"></audio>
    `);
    
    // 启用下载按钮
    card.find('.download-voice').prop('disabled', false);
    
    // 绑定事件
    bindCardEvents(card);
}

// 绑定卡片事件
function bindCardEvents(card) {
    // 预览按钮
    card.find('.preview-voice').on('click', function() {
        const taskId = card.data('task-id');
        openVoicePreview(taskId);
    });
    
    // 下载按钮
    card.find('.download-voice').on('click', function() {
        const audioUrl = card.find('audio').attr('src');
        if (audioUrl) {
            downloadAudio(audioUrl);
        }
    });
    
    // 编辑按钮
    card.find('.edit-voice').on('click', function() {
        const taskId = card.data('task-id');
        editVoice(taskId);
    });
    
    // 删除按钮
    card.find('.delete-voice').on('click', function() {
        const taskId = card.data('task-id');
        deleteVoice(taskId);
    });
}

// 打开语音预览
function openVoicePreview(taskId) {
    $.ajax({
        url: `/api/voice/detail?task_id=${taskId}`,
        type: 'GET',
        success: function(response) {
            if (response.success) {
                const voice = response.data;
                
                // 设置当前语音ID
                currentVoiceId = taskId;
                
                // 填充模态框
                $('#modalAudio').attr('src', voice.audio_url);
                $('#modalText').text(voice.text);
                $('#modalVoice').text(voice.voice_id);
                $('#modalModel').text(voice.model);
                
                // 显示模态框
                const modal = new bootstrap.Modal(document.getElementById('voicePreviewModal'));
                modal.show();
            } else {
                alert('获取语音详情失败：' + (response.message || '未知错误'));
            }
        },
        error: function(xhr) {
            alert('请求失败：' + (xhr.responseJSON?.message || '服务器错误'));
        }
    });
}

// 导航到指定索引的语音
function navigateVoice(index) {
    const card = $(allVoices[index]);
    const taskId = card.data('task-id');
    
    // 更新当前索引
    currentVoiceIndex = index;
    
    // 打开预览
    openVoicePreview(taskId);
}

// 下载音频
function downloadAudio(url) {
    const a = document.createElement('a');
    a.href = url;
    a.download = 'voice_' + new Date().getTime() + '.mp3';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// 编辑语音
function editVoice(taskId) {
    $.ajax({
        url: `/api/voice/detail?task_id=${taskId}`,
        type: 'GET',
        success: function(response) {
            if (response.success) {
                const voice = response.data;
                
                // 打开侧边栏
                $('#sidebar').addClass('active');
                $('#mainContent').addClass('sidebar-active');
                
                // 切换到TTS标签
                $('#tts-tab').tab('show');
                
                // 填充表单
                $('#tts_text').val(voice.text);
                $('#tts_voice_id').val(voice.voice_id);
                $('#tts_model').val(voice.model);
                $('#tts_speed').val(voice.speed || 1.0);
                $('#tts_speed_value').text(voice.speed || 1.0);
            } else {
                alert('获取语音详情失败：' + (response.message || '未知错误'));
            }
        },
        error: function(xhr) {
            alert('请求失败：' + (xhr.responseJSON?.message || '服务器错误'));
        }
    });
}

// 删除语音
function deleteVoice(taskId) {
    if (confirm('确定要删除这个语音吗？')) {
        $.ajax({
            url: '/api/voice/delete',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ task_id: taskId }),
            success: function(response) {
                if (response.success) {
                    // 从DOM中移除卡片
                    $(`.voice-card[data-task-id="${taskId}"]`).remove();
                } else {
                    alert('删除失败：' + (response.message || '未知错误'));
                }
            },
            error: function(xhr) {
                alert('请求失败：' + (xhr.responseJSON?.message || '服务器错误'));
            }
        });
    }
}

// 获取状态对应的CSS类
function getStatusClass(status) {
    switch (status) {
        case 'pending': return 'status-pending';
        case 'processing': return 'status-processing';
        case 'succeed': return 'status-succeed';
        case 'failed': return 'status-failed';
        default: return 'status-pending';
    }
}

// 获取状态对应的文本
function getStatusText(status) {
    switch (status) {
        case 'pending': return '等待处理';
        case 'processing': return '处理中';
        case 'succeed': return '已完成';
        case 'failed': return '处理失败';
        default: return '未知状态';
    }
}

// 保存语音任务到本地
function saveVoiceTaskToLocal(task) {
    // 获取现有任务
    let tasks = JSON.parse(localStorage.getItem('voice_tasks') || '[]');
    
    // 添加新任务
    tasks.push(task);
    
    // 保存回本地
    localStorage.setItem('voice_tasks', JSON.stringify(tasks));
    
    // 同步到服务器
    syncVoiceTasksToServer();
}

// 同步语音任务到服务器
function syncVoiceTasksToServer() {
    const tasks = JSON.parse(localStorage.getItem('voice_tasks') || '[]');
    
    $.ajax({
        url: '/api/voice/sync',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ tasks: tasks }),
        success: function(response) {
            if (response.success) {
                console.log('同步成功');
                // 清空本地缓存
                localStorage.removeItem('voice_tasks');
            } else {
                console.error('同步失败：', response.message);
            }
        },
        error: function(xhr) {
            console.error('请求失败：', xhr.responseText);
        }
    });
}