from django.db import models
from django.contrib.auth.models import User


class Blog(models.Model):
    """A blog belonging to one user."""
    title = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    # Most blogs are public, but some may be private for development
    #   or as a private journal.
    public = models.BooleanField(default=True)

    def __str__(self):
        """Return a string representation of the model."""
        return self.title


class BlogPost(models.Model):
    """A single post belonging to a blog."""
    title = models.CharField(max_length=500)
    body = models.TextField()
    blog = models.ForeignKey(Blog, on_delete= models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    # A post is private by default, for drafting purposes.
    public = models.BooleanField(default=False)

    def __str__(self):
        """Return a string representation of the model."""
        return self.title[:50]