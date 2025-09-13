// 사내 익명 게시판 메인 JavaScript

// 전역 변수
let sessionId = null;
let pollingInterval = null;
let lastUpdateTime = Date.now();

// DOM이 로드되면 실행
document.addEventListener('DOMContentLoaded', function() {
    initializeSession();
    initializePolling();
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

// CSRF 토큰 가져오기
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 폴링 초기화
function initializePolling() {
    updateConnectionStatus(true);
    startPolling();
}

// 폴링 시작
function startPolling() {
    stopPolling();
    pollingInterval = setInterval(checkForUpdates, 5000); // 5초마다 확인
}

// 폴링 중지
function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

// 업데이트 확인
async function checkForUpdates() {
    try {
        const response = await fetch('/api/check-updates/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.has_updates) {
                handleUpdates(data.updates);
            }
            updateConnectionStatus(true);
        } else {
            updateConnectionStatus(false);
        }
    } catch (error) {
        console.error('업데이트 확인 실패:', error);
        updateConnectionStatus(false);
    }
}

// 업데이트 처리
function handleUpdates(updates) {
    updates.forEach(update => {
        switch (update.type) {
            case 'new_post':
                handleNewPostNotification(update);
                break;
            case 'new_comment':
                handleNewCommentNotification(update);
                break;
            case 'reaction_update':
                handleReactionUpdate(update);
                break;
            default:
                console.log('알 수 없는 업데이트 타입:', update.type);
        }
    });
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
            icon.className = 'fas fa-sync-alt text-success me-2';
            text.textContent = '실시간 업데이트 활성화';
            statusElement.className = 'card mt-3 border-success';
        } else {
            icon.className = 'fas fa-exclamation-triangle text-warning me-2';
            text.textContent = '업데이트 확인 중...';
            statusElement.className = 'card mt-3 border-warning';
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
    
    // 삭제 버튼 이벤트
    const deleteButtons = document.querySelectorAll('.delete-post-btn');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', handleDeleteClick);
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
        
        const csrfToken = getCookie('csrftoken');
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
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

// 삭제 버튼 클릭 처리
async function handleDeleteClick(event) {
    event.preventDefault();
    const button = event.target.closest('.delete-post-btn');
    const postId = button.dataset.postId;
    await utils.deletePost(postId);
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
    },
    
    // 게시글 삭제 기능
    deletePost: async function(postId) {
        try {
            if (!confirm('정말로 이 게시글을 삭제하시겠습니까?')) {
                return;
            }

            const csrfToken = getCookie('csrftoken');
            const response = await fetch(`/api/post/${postId}/delete/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                }
            });

            const result = await response.json();

            if (result.success) {
                alert('게시글이 삭제되었습니다.');
                window.location.href = '/';
            } else {
                alert(result.error || '게시글 삭제에 실패했습니다.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('네트워크 오류가 발생했습니다.');
        }
    },

    // 이모지 반응 토글 기능
    toggleEmojiReaction: async function(targetType, targetId, reactionType) {
        try {
            const csrfToken = getCookie('csrftoken');
            const url = targetType === 'post' 
                ? `/api/post/${targetId}/reaction/` 
                : `/api/comment/${targetId}/reaction/`;
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({
                    reaction_type: reactionType
                })
            });

            const result = await response.json();
            
            if (result.success) {
                // 해당 버튼의 카운트 업데이트
                const selector = targetType === 'post' 
                    ? `[data-post-id="${targetId}"][data-reaction-type="${reactionType}"] .reaction-count`
                    : `[data-comment-id="${targetId}"][data-reaction-type="${reactionType}"] .reaction-count`;
                
                const countElement = document.querySelector(selector);
                if (countElement) {
                    countElement.textContent = result.count;
                }
                
                // 버튼 스타일 업데이트 (활성/비활성)
                const button = document.querySelector(
                    targetType === 'post' 
                        ? `[data-post-id="${targetId}"][data-reaction-type="${reactionType}"]`
                        : `[data-comment-id="${targetId}"][data-reaction-type="${reactionType}"]`
                );
                
                if (button) {
                    if (result.is_active) {
                        button.classList.remove('btn-outline-primary');
                        button.classList.add('btn-primary');
                    } else {
                        button.classList.remove('btn-primary');
                        button.classList.add('btn-outline-primary');
                    }
                }
            }
        } catch (error) {
            console.error('Reaction error:', error);
        }
    }
};

// 전역으로 유틸리티 함수 노출
window.showNotification = showNotification;
window.utils = utils;
