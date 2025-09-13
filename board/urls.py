from django.urls import path
from . import views

app_name = 'board'

urlpatterns = [
    path('', views.index, name='index'),
    path('post/<uuid:post_id>/', views.post_detail, name='post_detail'),
    path('api/post/create/', views.create_post, name='create_post'),
    path('api/post/<uuid:post_id>/comment/', views.create_comment, name='create_comment'),
    path('api/post/<uuid:post_id>/reaction/', views.toggle_post_reaction, name='toggle_post_reaction'),
    path('api/comment/<uuid:comment_id>/reaction/', views.toggle_comment_reaction, name='toggle_comment_reaction'),
    path('api/check-updates/', views.check_updates, name='check_updates'),
]
