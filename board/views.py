from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import json
import uuid
from .models import Post, Comment, PostReaction, CommentReaction


def index(request):
    """메인 게시판 페이지"""
    # 검색 기능
    search_query = request.GET.get('search', '')
    posts = Post.objects.filter(is_deleted=False)
    
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query) |
            Q(author_nickname__icontains=search_query)
        )
    
    # 페이지네이션
    paginator = Paginator(posts, 10)  # 한 페이지에 10개 게시글
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'board/index.html', context)


def post_detail(request, post_id):
    """게시글 상세 페이지"""
    post = get_object_or_404(Post, id=post_id, is_deleted=False)
    
    # 조회수 증가
    post.view_count += 1
    post.save()
    
    # 댓글 가져오기
    comments = post.comments.all()
    
    context = {
        'post': post,
        'comments': comments,
    }
    return render(request, 'board/post_detail.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def create_post(request):
    """새 게시글 작성"""
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        author_nickname = data.get('author_nickname', '익명').strip()
        
        if not title or not content:
            return JsonResponse({'success': False, 'error': '제목과 내용을 입력해주세요.'})
        
        if len(title) > 200:
            return JsonResponse({'success': False, 'error': '제목이 너무 깁니다.'})
        
        if len(author_nickname) > 50:
            author_nickname = author_nickname[:50]
        
        post = Post.objects.create(
            title=title,
            content=content,
            author_nickname=author_nickname or '익명'
        )
        
        # 새 게시글 작성 시간 기록 (폴링용)
        request.session['last_check_time'] = timezone.now().isoformat()
        
        return JsonResponse({
            'success': True, 
            'post_id': str(post.id),
            'message': '게시글이 작성되었습니다.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '잘못된 데이터 형식입니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': '게시글 작성 중 오류가 발생했습니다.'})


@csrf_exempt
@require_http_methods(["POST"])
def create_comment(request, post_id):
    """댓글 작성"""
    try:
        post = get_object_or_404(Post, id=post_id)
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        author_nickname = data.get('author_nickname', '익명').strip()
        
        if not content:
            return JsonResponse({'success': False, 'error': '댓글 내용을 입력해주세요.'})
        
        if len(author_nickname) > 50:
            author_nickname = author_nickname[:50]
        
        comment = Comment.objects.create(
            post=post,
            content=content,
            author_nickname=author_nickname or '익명'
        )
        
        # 새 댓글 작성 시간 기록 (폴링용)
        request.session['last_check_time'] = timezone.now().isoformat()
        
        return JsonResponse({
            'success': True,
            'comment_id': str(comment.id),
            'message': '댓글이 작성되었습니다.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '잘못된 데이터 형식입니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': '댓글 작성 중 오류가 발생했습니다.'})


@csrf_exempt
@require_http_methods(["POST"])
def toggle_post_reaction(request, post_id):
    """게시글 반응 토글 (좋아요/싫어요)"""
    try:
        post = get_object_or_404(Post, id=post_id)
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type')  # 'like' or 'dislike'
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if reaction_type not in ['like', 'dislike']:
            return JsonResponse({'success': False, 'error': '잘못된 반응 타입입니다.'})
        
        # 기존 반응 확인
        existing_reaction = PostReaction.objects.filter(
            post=post, session_id=session_id
        ).first()
        
        if existing_reaction:
            # 기존 반응과 같으면 제거
            if existing_reaction.reaction_type == reaction_type:
                existing_reaction.delete()
                # 카운트 감소
                if reaction_type == 'like':
                    post.likes_count = max(0, post.likes_count - 1)
                else:
                    post.dislikes_count = max(0, post.dislikes_count - 1)
                post.save()
                
                return JsonResponse({
                    'success': True,
                    'action': 'removed',
                    'likes_count': post.likes_count,
                    'dislikes_count': post.dislikes_count
                })
            else:
                # 다른 반응으로 변경
                old_type = existing_reaction.reaction_type
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                
                # 카운트 조정
                if old_type == 'like':
                    post.likes_count = max(0, post.likes_count - 1)
                else:
                    post.dislikes_count = max(0, post.dislikes_count - 1)
                
                if reaction_type == 'like':
                    post.likes_count += 1
                else:
                    post.dislikes_count += 1
                
                post.save()
                
                return JsonResponse({
                    'success': True,
                    'action': 'changed',
                    'likes_count': post.likes_count,
                    'dislikes_count': post.dislikes_count
                })
        else:
            # 새 반응 추가
            PostReaction.objects.create(
                post=post,
                session_id=session_id,
                reaction_type=reaction_type
            )
            
            # 카운트 증가
            if reaction_type == 'like':
                post.likes_count += 1
            else:
                post.dislikes_count += 1
            post.save()
            
            return JsonResponse({
                'success': True,
                'action': 'added',
                'likes_count': post.likes_count,
                'dislikes_count': post.dislikes_count
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '잘못된 데이터 형식입니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': '반응 처리 중 오류가 발생했습니다.'})


@csrf_exempt
@require_http_methods(["POST"])
def toggle_comment_reaction(request, comment_id):
    """댓글 반응 토글 (좋아요/싫어요)"""
    try:
        comment = get_object_or_404(Comment, id=comment_id)
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type')  # 'like' or 'dislike'
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if reaction_type not in ['like', 'dislike']:
            return JsonResponse({'success': False, 'error': '잘못된 반응 타입입니다.'})
        
        # 기존 반응 확인
        existing_reaction = CommentReaction.objects.filter(
            comment=comment, session_id=session_id
        ).first()
        
        if existing_reaction:
            # 기존 반응과 같으면 제거
            if existing_reaction.reaction_type == reaction_type:
                existing_reaction.delete()
                # 카운트 감소
                if reaction_type == 'like':
                    comment.likes_count = max(0, comment.likes_count - 1)
                else:
                    comment.dislikes_count = max(0, comment.dislikes_count - 1)
                comment.save()
                
                return JsonResponse({
                    'success': True,
                    'action': 'removed',
                    'likes_count': comment.likes_count,
                    'dislikes_count': comment.dislikes_count
                })
            else:
                # 다른 반응으로 변경
                old_type = existing_reaction.reaction_type
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                
                # 카운트 조정
                if old_type == 'like':
                    comment.likes_count = max(0, comment.likes_count - 1)
                else:
                    comment.dislikes_count = max(0, comment.dislikes_count - 1)
                
                if reaction_type == 'like':
                    comment.likes_count += 1
                else:
                    comment.dislikes_count += 1
                
                comment.save()
                
                return JsonResponse({
                    'success': True,
                    'action': 'changed',
                    'likes_count': comment.likes_count,
                    'dislikes_count': comment.dislikes_count
                })
        else:
            # 새 반응 추가
            CommentReaction.objects.create(
                comment=comment,
                session_id=session_id,
                reaction_type=reaction_type
            )
            
            # 카운트 증가
            if reaction_type == 'like':
                comment.likes_count += 1
            else:
                comment.dislikes_count += 1
            comment.save()
            
            return JsonResponse({
                'success': True,
                'action': 'added',
                'likes_count': comment.likes_count,
                'dislikes_count': comment.dislikes_count
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '잘못된 데이터 형식입니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': '반응 처리 중 오류가 발생했습니다.'})


@require_http_methods(["GET"])
def check_updates(request):
    """업데이트 확인 API (폴링용)"""
    try:
        # 마지막 확인 시간 가져오기
        last_check_str = request.session.get('last_check_time')
        if not last_check_str:
            request.session['last_check_time'] = timezone.now().isoformat()
            return JsonResponse({'has_updates': False, 'updates': []})
        
        last_check_time = datetime.fromisoformat(last_check_str.replace('Z', '+00:00'))
        current_time = timezone.now()
        
        # 최근 5분 내의 업데이트 확인
        recent_posts = Post.objects.filter(
            created_at__gte=last_check_time,
            created_at__lt=current_time
        ).values('id', 'title', 'author_nickname', 'created_at')
        
        recent_comments = Comment.objects.filter(
            created_at__gte=last_check_time,
            created_at__lt=current_time
        ).values('id', 'post__title', 'author_nickname', 'created_at')
        
        updates = []
        
        # 새 게시글 알림
        for post in recent_posts:
            updates.append({
                'type': 'new_post',
                'data': {
                    'post_id': str(post['id']),
                    'title': post['title'],
                    'author': post['author_nickname'],
                    'created_at': post['created_at'].isoformat()
                }
            })
        
        # 새 댓글 알림
        for comment in recent_comments:
            updates.append({
                'type': 'new_comment',
                'data': {
                    'comment_id': str(comment['id']),
                    'post_title': comment['post__title'],
                    'author': comment['author_nickname'],
                    'created_at': comment['created_at'].isoformat()
                }
            })
        
        # 마지막 확인 시간 업데이트
        request.session['last_check_time'] = current_time.isoformat()
        
        return JsonResponse({
            'has_updates': len(updates) > 0,
            'updates': updates
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': '업데이트 확인 중 오류가 발생했습니다.'})


@csrf_exempt
@require_http_methods(["POST"])
def delete_post(request, post_id):
    """게시글 삭제"""
    try:
        post = get_object_or_404(Post, id=post_id)
        
        # 게시글 삭제 처리 (비밀번호 없이 바로 삭제)
        post.is_deleted = True
        post.deleted_at = timezone.now()
        post.save()
        
        # 마지막 확인 시간 업데이트 (다른 사용자들에게 알림)
        request.session['last_check_time'] = timezone.now().isoformat()
        
        return JsonResponse({
            'success': True,
            'message': '게시글이 삭제되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': '게시글 삭제 중 오류가 발생했습니다.'
        })


def health_check(request):
    """Railway healthcheck 엔드포인트"""
    return HttpResponse("OK", status=200)


@csrf_exempt
@require_http_methods(["POST"])
def toggle_post_reaction(request, post_id):
    """게시글 이모지 반응 토글"""
    try:
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type')
        
        if reaction_type not in ['like', 'heart', 'laugh', 'wow', 'sad']:
            return JsonResponse({'success': False, 'error': '유효하지 않은 반응 타입입니다.'})
        
        post = get_object_or_404(Post, id=post_id)
        session_id = request.session.session_key
        
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        # 기존 반응 확인
        existing_reaction = PostReaction.objects.filter(
            post=post, 
            session_id=session_id
        ).first()
        
        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                # 같은 반응이면 제거
                existing_reaction.delete()
                is_active = False
            else:
                # 다른 반응이면 변경
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                is_active = True
        else:
            # 새 반응 생성
            PostReaction.objects.create(
                post=post,
                session_id=session_id,
                reaction_type=reaction_type
            )
            is_active = True
        
        # 카운트 업데이트
        update_post_reaction_counts(post)
        
        # 현재 카운트 반환
        count = getattr(post, f'{reaction_type}s_count', 0)
        
        return JsonResponse({
            'success': True,
            'count': count,
            'is_active': is_active
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def toggle_comment_reaction(request, comment_id):
    """댓글 이모지 반응 토글"""
    try:
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type')
        
        if reaction_type not in ['like', 'heart', 'laugh', 'wow', 'sad']:
            return JsonResponse({'success': False, 'error': '유효하지 않은 반응 타입입니다.'})
        
        comment = get_object_or_404(Comment, id=comment_id)
        session_id = request.session.session_key
        
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        # 기존 반응 확인
        existing_reaction = CommentReaction.objects.filter(
            comment=comment, 
            session_id=session_id
        ).first()
        
        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                # 같은 반응이면 제거
                existing_reaction.delete()
                is_active = False
            else:
                # 다른 반응이면 변경
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                is_active = True
        else:
            # 새 반응 생성
            CommentReaction.objects.create(
                comment=comment,
                session_id=session_id,
                reaction_type=reaction_type
            )
            is_active = True
        
        # 카운트 업데이트
        update_comment_reaction_counts(comment)
        
        # 현재 카운트 반환
        count = getattr(comment, f'{reaction_type}s_count', 0)
        
        return JsonResponse({
            'success': True,
            'count': count,
            'is_active': is_active
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def update_post_reaction_counts(post):
    """게시글 반응 카운트 업데이트"""
    reactions = PostReaction.objects.filter(post=post)
    
    post.likes_count = reactions.filter(reaction_type='like').count()
    post.hearts_count = reactions.filter(reaction_type='heart').count()
    post.laughs_count = reactions.filter(reaction_type='laugh').count()
    post.wows_count = reactions.filter(reaction_type='wow').count()
    post.sads_count = reactions.filter(reaction_type='sad').count()
    
    post.save()


def update_comment_reaction_counts(comment):
    """댓글 반응 카운트 업데이트"""
    reactions = CommentReaction.objects.filter(comment=comment)
    
    comment.likes_count = reactions.filter(reaction_type='like').count()
    comment.hearts_count = reactions.filter(reaction_type='heart').count()
    comment.laughs_count = reactions.filter(reaction_type='laugh').count()
    comment.wows_count = reactions.filter(reaction_type='wow').count()
    comment.sads_count = reactions.filter(reaction_type='sad').count()
    
    comment.save()