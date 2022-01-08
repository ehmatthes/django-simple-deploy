from django import forms

from .models import Blog, BlogPost


class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['title', 'public']


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'body', 'public' ]