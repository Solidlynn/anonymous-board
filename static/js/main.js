// 사내 익명 게시판 메인 JavaScript

// 전역 변수
let websocket = null;
let sessionId = null;

// DOM이 로드되면 실행
document.addEventListener('DOMContentLoaded', function() {
    initializeSession();
    initializeWebSocket();
    initializeEventListeners();
});

// 세션 초기화
function initializeSession() {
    sessionId = localStorage.getItem('sessionId') || generateUUID();
    if (!localStorage.getItem('sessionId')) {
        localStorage.setItem('sessionId', sessionId);
    }
}

// UUID 생성
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0,
            v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// WebSocket 초기화
function initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/board/`;
    
    try {
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = function(event) {
            console.log('WebSocket 연결됨');
            updateConnectionStatus(true);
            // 연결 성공 시 하트비트 시작
            startHeartbeat();
        };
        
        websocket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        websocket.onclose = function(event) {
            console.log('WebSocket 연결 끊어짐');
            updateConnectionStatus(false);
            stopHeartbeat();
            // 3초 후 재연결 시도
            setTimeout(initializeWebSocket, 3000);
        };
        
        websocket.onerror = function(error) {
            console.error('WebSocket 오류:', error);
            updateConnectionStatus(false);
        };
    } catch (error) {
        console.error('WebSocket 연결 실패:', error);
        updateConnectionStatus(false);
        // 5초 후 재시도
        setTimeout(initializeWebSocket, 5000);
    }
}

// 하트비트 관리
let heartbeatInterval = null;

function startHeartbeat() {
    stopHeartbeat();
    heartbeatInterval = setInterval(() => {
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({type: 'ping'}));
        } else {
            // 연결이 끊어진 경우 재연결 시도
            initializeWebSocket();
        }
    }, 30000); // 30초마다 하트비트
}

function stopHeartbeat() {
    if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
        heartbeatInterval = null;
    }
}

// WebSocket 메시지 처리
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'new_post':
            handleNewPostNotification(data);
            break;
        case 'new_comment':
            handleNewCommentNotification(data);
            break;
        case 'reaction_update':
            handleReactionUpdate(data);
            break;
        default:
            console.log('알 수 없는 메시지 타입:', data.type);
    }
}

// 새 게시글 알림 처리
function handleNewPostNotification(data) {
    showNotification('새로운 게시글이 작성되었습니다!', 'info');
    
    // 현재 페이지가 메인 페이지인 경우 새로고침
    if (window.location.pathname === '/' || window.location.pathname === '') {
        setTimeout(() => location.reload(), 2000);
    }
}

// 새 댓글 알림 처리
function handleNewCommentNotification(data) {
    showNotification('새로운 댓글이 작성되었습니다!', 'info');
    
    // 현재 페이지가 해당 게시글 상세 페이지인 경우 새로고침
    if (window.location.pathname.includes('/post/')) {
        setTimeout(() => location.reload(), 2000);
    }
}

// 반응 업데이트 처리
function handleReactionUpdate(data) {
    // 실시간 반응 업데이트 로직
    console.log('반응 업데이트:', data);
}

// 연결 상태 업데이트
function updateConnectionStatus(isConnected) {
    const statusElement = document.getElementById('realtime-status');
    if (statusElement) {
        const icon = statusElement.querySelector('i');
        const text = statusElement.querySelector('span');
        
        if (isConnected) {
            icon.className = 'fas fa-wifi text-success me-2';
            text.textContent = '실시간 업데이트 연결됨';
            statusElement.className = 'card mt-3 border-success';
        } else {
            icon.className = 'fas fa-wifi text-danger me-2';
            text.textContent = '실시간 업데이트 연결 끊어짐';
            statusElement.className = 'card mt-3 border-danger';
        }
    }
}

// 이벤트 리스너 초기화
function initializeEventListeners() {
    // 폼 제출 이벤트
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });
    
    // 반응 버튼 이벤트
    const reactionButtons = document.querySelectorAll('.reaction-btn, .comment-reaction-btn');
    reactionButtons.forEach(btn => {
        btn.addEventListener('click', handleReactionClick);
    });
    
    // 키보드 단축키
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

// 폼 제출 처리
async function handleFormSubmit(event) {
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    
    if (submitBtn) {
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="loading"></span> 처리중...';
        submitBtn.disabled = true;
        
        try {
            await new Promise(resolve => setTimeout(resolve, 1000)); // 최소 로딩 시간
        } finally {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }
}

// 반응 버튼 클릭 처리
async function handleReactionClick(event) {
    const button = event.target.closest('.reaction-btn, .comment-reaction-btn');
    if (!button) return;
    
    event.preventDefault();
    
    const isPostReaction = button.classList.contains('reaction-btn') && !button.classList.contains('comment-reaction-btn');
    const targetId = isPostReaction ? button.dataset.postId : button.dataset.commentId;
    const reactionType = button.dataset.reactionType;
    
    // 버튼 애니메이션
    button.style.transform = 'scale(0.95)';
    setTimeout(() => {
        button.style.transform = '';
    }, 150);
    
    try {
        const url = isPostReaction 
            ? `/api/post/${targetId}/reaction/`
            : `/api/comment/${targetId}/reaction/`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                reaction_type: reactionType,
                session_id: sessionId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 반응 버튼 업데이트
            updateReactionButtons(targetId, result, isPostReaction);
            
            // 시각적 피드백
            showReactionFeedback(button, result.action);
        } else {
            showNotification(result.error || '반응 처리에 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('반응 처리 오류:', error);
        showNotification('네트워크 오류가 발생했습니다.', 'error');
    }
}

// 반응 버튼 업데이트
function updateReactionButtons(targetId, result, isPostReaction) {
    const selector = isPostReaction 
        ? `[data-post-id="${targetId}"]`
        : `[data-comment-id="${targetId}"]`;
    
    const container = document.querySelector(selector);
    if (!container) return;
    
    const likeBtn = container.querySelector('[data-reaction-type="like"]');
    const dislikeBtn = container.querySelector('[data-reaction-type="dislike"]');
    
    if (likeBtn) {
        likeBtn.innerHTML = `<i class="fas fa-thumbs-up"></i> ${result.likes_count}`;
    }
    if (dislikeBtn) {
        dislikeBtn.innerHTML = `<i class="fas fa-thumbs-down"></i> ${result.dislikes_count}`;
    }
}

// 반응 피드백 표시
function showReactionFeedback(button, action) {
    const originalClass = button.className;
    
    if (action === 'added') {
        button.classList.remove('btn-outline-success', 'btn-outline-danger');
        button.classList.add(button.dataset.reactionType === 'like' ? 'btn-success' : 'btn-danger');
    } else if (action === 'removed') {
        button.classList.remove('btn-success', 'btn-danger');
        button.classList.add(button.dataset.reactionType === 'like' ? 'btn-outline-success' : 'btn-outline-danger');
    }
    
    // 애니메이션 효과
    button.style.transform = 'scale(1.1)';
    setTimeout(() => {
        button.style.transform = '';
    }, 200);
}

// 키보드 단축키 처리
function handleKeyboardShortcuts(event) {
    // Ctrl/Cmd + Enter로 폼 제출
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        const activeElement = document.activeElement;
        if (activeElement.tagName === 'TEXTAREA') {
            const form = activeElement.closest('form');
            if (form) {
                event.preventDefault();
                form.dispatchEvent(new Event('submit'));
            }
        }
    }
    
    // ESC로 모달 닫기
    if (event.key === 'Escape') {
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            const modal = bootstrap.Modal.getInstance(openModal);
            if (modal) modal.hide();
        }
    }
}

// 알림 표시 함수
function showNotification(message, type = 'info') {
    const toast = document.getElementById('notificationToast');
    const messageEl = document.getElementById('notificationMessage');
    
    if (!toast || !messageEl) return;
    
    messageEl.textContent = message;
    
    // 타입에 따른 아이콘 변경
    const icon = toast.querySelector('i');
    if (icon) {
        icon.className = type === 'success' ? 'fas fa-check-circle text-success me-2' :
                        type === 'error' ? 'fas fa-exclamation-circle text-danger me-2' :
                        type === 'warning' ? 'fas fa-exclamation-triangle text-warning me-2' :
                        'fas fa-info-circle text-primary me-2';
    }
    
    const toastInstance = new bootstrap.Toast(toast);
    toastInstance.show();
}

// 유틸리티 함수들
const utils = {
    // 디바운스 함수
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // 스로틀 함수
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    // 로컬 스토리지 안전하게 사용
    storage: {
        set: function(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (e) {
                console.error('로컬 스토리지 저장 실패:', e);
                return false;
            }
        },
        
        get: function(key) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : null;
            } catch (e) {
                console.error('로컬 스토리지 읽기 실패:', e);
                return null;
            }
        }
    }
};

// 전역으로 유틸리티 함수 노출
window.showNotification = showNotification;
window.utils = utils;
