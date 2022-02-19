from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from .models import Blog, BlogPost
from .forms import BlogForm, BlogPostForm


def index(request):
    """The home page for the blog."""
    return render(request, 'blogs/index.html')


def all_blogs(request):
    """Show all public blogs, and user's blogs."""

    # Get all public blogs, then user's blogs.
    public_blogs = Blog.objects.filter(public=True)
    if request.user.is_authenticated:
        user_blogs = Blog.objects.filter(owner=request.user)
    else:
        user_blogs = []

    context = {
        'public_blogs': public_blogs,
        'user_blogs': user_blogs,
    }
    return render(request, 'blogs/all_blogs.html', context=context)


def latest_posts(request):
    """Show latest posts from all public blogs."""

    # Get the latest 10 posts.
    public_posts = BlogPost.objects.filter(public=True).order_by('-date_added')[:10]

    context = {'public_posts': public_posts}
    return render(request, 'blogs/latest_posts.html', context=context)


@login_required
def my_blogs(request):
    """Show user's blogs."""
    user_blogs = Blog.objects.filter(owner=request.user)

    context = {'user_blogs': user_blogs}
    return render(request, 'blogs/my_blogs.html', context=context)


def blog(request, blog_id):
    """Main page for a single blog.
    Show public posts, and private posts for the current user.
    """

    blog = Blog.objects.get(id=blog_id)

    if request.user == blog.owner:
        posts = blog.blogpost_set.all().order_by('-date_added')
    else:
        posts = blog.blogpost_set.filter(public=True).order_by('-date_added')

    context = {
        'blog': blog,
        'posts': posts,
    }
    return render(request, 'blogs/blog.html', context=context)


def post(request, post_id):
    """Main page for a single post."""

    post = BlogPost.objects.get(id=post_id)

    if (not post.public) and (request.user != post.blog.owner):
        # This is someone else's private post; redirect to home page.
        return redirect('blogs:index')

    context = {
        'blog': post.blog,
        'post': post,
    }
    return render(request, 'blogs/post.html', context=context)


# --- Creation pages. ---

@login_required
def new_blog(request):
    """Create a new blog."""

    if request.method != 'POST':
        # No data submitted; create a blank form.
        form = BlogForm()
    else:
        # POST data submitted; process data.
        form = BlogForm(data=request.POST)
        if form.is_valid():
            new_blog = form.save(commit=False)
            new_blog.owner = request.user
            new_blog.save()
            return redirect('blogs:my_blogs')

    # Display blank or invalid form.
    context = {'form': form}
    return render(request, 'blogs/new_blog.html', context)


@login_required
def new_post(request, blog_id):
    """Create a new post."""

    # Every post is associated with a specific blog.
    blog = Blog.objects.get(id=blog_id)

    # Make sure user owns this blog.
    if blog.owner != request.user:
        return redirect('blogs:index')

    if request.method != 'POST':
        # No data submitted; create a blank form.
        form = BlogPostForm()
    else:
        # POST data submitted; process data.
        form = BlogPostForm(data=request.POST)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.blog = blog

            # If the blog is private, ensure the post is private.
            if not blog.public:
                new_post.public = False

            new_post.save()

            return redirect('blogs:post', post_id=new_post.id)

    # Display blank or invalid form.
    context = {'form': form, 'blog': blog}
    return render(request, 'blogs/new_post.html', context)


# --- Editing pages ---

# DEV: These pages aren't needed for the purpose of testing deployment, so no
#  rush on building these out.


# --- Deletion pages ---

# DEV: These pages aren't needed for the purpose of testing deployment, so no
#  rush on building these out.
