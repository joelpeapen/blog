from django.contrib import admin
from django.urls import path

from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.Index.as_view(), name="home"),
    path('register/', views.Register.as_view(), name="register"),
    path('login/', views.Login.as_view(), name="login"),
    path('logout/', views.Logout.as_view(), name="logout"),
    path('user/', views.appUser.as_view(), name="user"),
    path("user/settings/", views.Settings.as_view(), name="settings"),
    path("user/settings/account/", views.SettingsAccount.as_view(), name="settings-account"),
    path("user/settings/notifications/", views.SettingsNotify.as_view(), name="settings-notify"),
    path("user/delete/", views.UserDelete.as_view(), name="delete-user"),
    path("user/<str:username>/", views.appUser.as_view(), name="user"),
    path("send-email-confirm/", views.send_email_confirm, name="send-email-confirm"),
    path("email-confirm/", views.set_email_confirm, name="set-email-confirm"),
    path("email-change/", views.email_change, name="email-change"),
    path("email-change-confirm/", views.set_email_change_confirm, name="email-change-confirm"),
    path("pass-mail/", views.Passmail.as_view(), name="pass-mail"),
    path("passreset", views.Passreset.as_view(), name="pass-reset"),
    path("send-pass-mail-confirm/", views.send_pass_mail_confirm, name="send-pass-mail-confirm"),
    path("set-password-confirm/", views.set_password_confirm, name="set-password-confirm"),
    path("<str:username>/post/<int:id>", views.BlogPost.as_view(), name="post"),
    path("posts/", views.Posts.as_view(), name="posts"),
    path("add/", views.Add.as_view(), name="add"),
    path("edit/<int:id>", views.Edit.as_view(), name="edit"),
    path("delete/<int:id>", views.Delete.as_view(), name="delete"),
    path("like/<int:id>", views.Like.as_view(), name="like"),
    path("comment/<int:id>", views.CommentAdd.as_view(), name="comment-add"),
    path("comment/edit/<int:id>", views.CommentEdit.as_view(), name="comment-edit"),
    path("comment/delete/<int:id>", views.CommentDelete.as_view(), name="comment-del"),
    path("comment/like/<int:id>", views.CommentLike.as_view(), name="comment-like"),
]
