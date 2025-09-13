from django.contrib import admin
from .models import Post, Comment, PostReaction, CommentReaction


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author_nickname', 'created_at', 'view_count', 'likes_count', 'dislikes_count')
    list_filter = ('created_at', 'is_anonymous')
    search_fields = ('title', 'content', 'author_nickname')
    readonly_fields = ('id', 'created_at', 'updated_at', 'view_count')
    ordering = ('-created_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author_nickname', 'created_at', 'likes_count', 'dislikes_count')
    list_filter = ('created_at', 'is_anonymous')
    search_fields = ('content', 'author_nickname')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(PostReaction)
class PostReactionAdmin(admin.ModelAdmin):
    list_display = ('post', 'session_id', 'reaction_type', 'created_at')
    list_filter = ('reaction_type', 'created_at')
    search_fields = ('post__title', 'session_id')
    readonly_fields = ('id', 'created_at')
    ordering = ('-created_at',)


@admin.register(CommentReaction)
class CommentReactionAdmin(admin.ModelAdmin):
    list_display = ('comment', 'session_id', 'reaction_type', 'created_at')
    list_filter = ('reaction_type', 'created_at')
    search_fields = ('comment__content', 'session_id')
    readonly_fields = ('id', 'created_at')
    ordering = ('-created_at',)