from uuid import uuid4
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(max_length=254)
    is_email_confirmed = models.BooleanField(default=False)
    is_password_confirmed = models.BooleanField(default=False)
    pic = models.ImageField(
        upload_to="images/profiles/", default="images/profiles/default.png"
    )
    bio = models.TextField()
    likes = models.ManyToManyField("Post", related_name="liked_posts")
    comment_likes = models.ManyToManyField("Comment", related_name="liked_comments")

    def __str__(self):
        return self.username


class Blog(models.Model):
    name = models.CharField(max_length=75, unique=True)
    author = models.ForeignKey("User", on_delete=models.CASCADE)
    splash = models.ImageField(
        upload_to="images/blogs/", default="images/blogs/default.png"
    )
    about = models.TextField()
    date = models.DateTimeField()
    welcome = models.TextField()

    def __str__(self):
        return self.name


class Post(models.Model):
    blog = models.ForeignKey("Blog", on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    subtitle = models.CharField(max_length=250)
    text = models.TextField()
    author = models.ForeignKey("User", on_delete=models.CASCADE)
    likes = models.IntegerField(default=0)
    views = models.IntegerField(default=1)
    date = models.DateTimeField()
    updated = models.DateTimeField()
    splash = models.ImageField(
        upload_to="images/splashes/", default="images/splashes/default.png"
    )
    splashdesc = models.CharField(max_length=150)
    tags = models.ManyToManyField("Tag", related_name="post_tags")
    limit_comments = models.BooleanField(default=False)
    no_comments = models.BooleanField(default=False)
    subonly = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Subscriber(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    blog = models.ForeignKey("Blog", on_delete=models.CASCADE)
    notify = models.BooleanField(default=True)


class Comment(models.Model):
    text = models.CharField(max_length=250)
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    post = models.ForeignKey("Post", on_delete=models.CASCADE)
    date = models.DateTimeField()
    likes = models.IntegerField(default=0)


class Tag(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


class EmailConfirmationToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)


class Notify(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    on_comment = models.BooleanField(default=True)
    on_sub = models.BooleanField(default=True)
