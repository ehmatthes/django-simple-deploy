"""Defines URL patterns for blogs."""

from django.urls import path

from . import views


app_name = 'blogs'
urlpatterns = [
    # Home page.
    path('', views.index, name='index'),

    # Viewing pages.
    path('all_blogs/', views.all_blogs, name='all_blogs'),
    path('latest_posts/', views.latest_posts, name='latest_posts'),
    path('my_blogs/', views.my_blogs, name='my_blogs'),
    path('blogs/<int:blog_id>/', views.blog, name='blog'),
    path('posts/<int:post_id>/', views.post, name='post'),

    # Creation pages.
    path('new_blog/', views.new_blog, name='new_blog'),
    path('new_post/<int:blog_id>/', views.new_post, name='new_post'),
]