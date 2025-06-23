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


class EmailConfirmationToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)


class Notify(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    on_comment = models.BooleanField(default=True)
    on_sub = models.BooleanField(default=True)
