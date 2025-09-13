from django.db import models
from django.utils import timezone
import uuid


class Post(models.Model):
    """게시글 모델"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name='제목')
    content = models.TextField(verbose_name='내용')
    author_nickname = models.CharField(max_length=50, verbose_name='닉네임', default='익명')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    view_count = models.PositiveIntegerField(default=0, verbose_name='조회수')
    is_anonymous = models.BooleanField(default=True, verbose_name='익명여부')
    
    # 좋아요/싫어요 관련
    likes_count = models.PositiveIntegerField(default=0, verbose_name='좋아요 수')
    dislikes_count = models.PositiveIntegerField(default=0, verbose_name='싫어요 수')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '게시글'
        verbose_name_plural = '게시글들'
    
    def __str__(self):
        return self.title
    
    def get_reactions_summary(self):
        """반응 요약 정보 반환"""
        return {
            'likes': self.likes_count,
            'dislikes': self.dislikes_count,
            'total': self.likes_count + self.dislikes_count
        }


class Comment(models.Model):
    """댓글 모델"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='게시글')
    content = models.TextField(verbose_name='댓글 내용')
    author_nickname = models.CharField(max_length=50, verbose_name='닉네임', default='익명')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    is_anonymous = models.BooleanField(default=True, verbose_name='익명여부')
    
    # 좋아요/싫어요 관련
    likes_count = models.PositiveIntegerField(default=0, verbose_name='좋아요 수')
    dislikes_count = models.PositiveIntegerField(default=0, verbose_name='싫어요 수')
    
    class Meta:
        ordering = ['created_at']
        verbose_name = '댓글'
        verbose_name_plural = '댓글들'
    
    def __str__(self):
        return f"{self.post.title} - {self.content[:30]}"


class PostReaction(models.Model):
    """게시글 반응 모델 (좋아요/싫어요)"""
    REACTION_CHOICES = [
        ('like', '좋아요'),
        ('dislike', '싫어요'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions', verbose_name='게시글')
    session_id = models.CharField(max_length=100, verbose_name='세션 ID')  # 익명 사용자 식별용
    reaction_type = models.CharField(max_length=10, choices=REACTION_CHOICES, verbose_name='반응 타입')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    
    class Meta:
        unique_together = ['post', 'session_id']  # 한 사용자는 게시글당 하나의 반응만 가능
        verbose_name = '게시글 반응'
        verbose_name_plural = '게시글 반응들'


class CommentReaction(models.Model):
    """댓글 반응 모델 (좋아요/싫어요)"""
    REACTION_CHOICES = [
        ('like', '좋아요'),
        ('dislike', '싫어요'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reactions', verbose_name='댓글')
    session_id = models.CharField(max_length=100, verbose_name='세션 ID')  # 익명 사용자 식별용
    reaction_type = models.CharField(max_length=10, choices=REACTION_CHOICES, verbose_name='반응 타입')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    
    class Meta:
        unique_together = ['comment', 'session_id']  # 한 사용자는 댓글당 하나의 반응만 가능
        verbose_name = '댓글 반응'
        verbose_name_plural = '댓글 반응들'