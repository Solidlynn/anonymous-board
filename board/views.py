from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
import json
import uuid
from .models import Post, Comment, PostReaction, CommentReaction


def index(request):
    """메인 게시판 페이지"""
    # 검색 기능
    search_query = request.GET.get('search', '')
    posts = Post.objects.all()
    
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
    post = get_object_or_404(Post, id=post_id)
    
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