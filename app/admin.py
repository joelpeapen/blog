from django.contrib import admin

from .models import User, Blog, Post, Subscriber, Comment, Tag, Notify

admin.site.register(User)
admin.site.register(Blog)
admin.site.register(Post)
admin.site.register(Subscriber)
admin.site.register(Comment)
admin.site.register(Tag)
admin.site.register(Notify)
