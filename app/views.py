from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from app.models import (
    EmailConfirmationToken,
    Notify,
    Post,
    User,
)
from app.utils import (
    send_confirmation_email,
    send_password_email,
    # send_comment_email,
    send_username_email,
)


class Index(View):
    def get(self, request):
        return render(request, "index.html", {"user": request.user})


class Register(View):
    def get(self, request):
        return render(request, "register.html", {"user": request.user})

    def post(self, request):
        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")

        if email and username and password:
            if User.objects.filter(email=email).exists():
                messages.error(request, "A user with this email already exists")
                return redirect("/register")
            elif User.objects.filter(username=username).exists():
                messages.error(request, "A user with this username already exists")
                return redirect("/register")
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    date_joined=datetime.utcnow(),
                )
                Notify.objects.create(user=user)

                token = EmailConfirmationToken.objects.create(user=user)
                send_confirmation_email(email=user.email, token_id=token.pk)

                return render(
                    request,
                    "email_confirm.html",
                    {"user": user, "new": True, "email": email},
                )
        else:
            messages.error(request, "All fields must be filled")
            return redirect("/register")


class Login(View):
    def get(self, request):
        return render(request, "login.html", {"user": request.user})

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")

        if username and password:
            if not User.objects.filter(username=username).exists():
                messages.error(request, "No such user")
                return redirect("/login")

            user = authenticate(username=username, password=password)
            if user:
                if user.is_email_confirmed:
                    login(request, user)
                    return redirect("/user")
                else:
                    return render(request, "email_confirm.html", {"user": user})
            else:
                messages.error(request, "Username or password is incorrect")
                return redirect("/login")
        else:
            messages.error(request, "All fields must be filled")


class Logout(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("/login")

        logout(request)
        return redirect("/login")


class appUser(View):
    def get(self, request, username=None):
        if username:
            profile = get_object_or_404(User, username=username)

            data = {
                "profile": profile,
                "user": request.user,
            }

            return render(request, "user.html", data)

        # /user/ -> logged-in user's page
        if request.user.is_authenticated:
            return render(
                request,
                "user.html",
                {"profile": request.user, "user": request.user},
            )
        return redirect("/login")


class UserDelete(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect("/login")

        n = request.user.username
        request.user.delete()
        messages.success(request, f"User {n} has been deleted")
        return redirect("/register")


class Settings(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("/login")

        return render(request, "settings.html", {"user": request.user})

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect("/login")

        username = request.POST.get("username")
        fname = request.POST.get("fname")
        lname = request.POST.get("lname")
        pic = request.FILES.get("pic")
        bio = request.POST.get("bio")

        user = request.user
        if username and username != user.username:
            if User.objects.filter(username=username).exists():
                messages.error(request, "A user with this username already exists")
                return redirect("/user/settings")
            user.username = username

        if fname != user.first_name:
            user.first_name = fname

        if lname != user.last_name:
            user.last_name = lname

        if bio != user.bio:
            user.bio = bio

        if pic:
            user.pic = pic

        user.save()
        messages.success(request, "Profile Updated")
        return redirect("/user/settings")


class SettingsAccount(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("/login")
        return render(request, "settings_account.html", {"user": request.user})

    # to change password
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect("/login")

        user = request.user
        password = request.POST.get("password")
        old_password = request.POST.get("old-password")
        confirm = request.POST.get("confirm-pw")

        if not old_password:
            messages.error(request, "Must provide old password to change password")
        elif not password:
            messages.error(request, "Must provide a new password")
        elif not confirm:
            messages.error(request, "Must confirm the new password")
        elif password != confirm:
            messages.error(request, "Passwords do not match")
        elif not user.check_password(old_password):
            messages.error(request, "Old password is incorrect")
        elif password == old_password == confirm:
            messages.error(request, "Thats the same password")
        else:
            user.set_password(password)
            update_session_auth_hash(request, user)
            user.save()
            messages.success(request, "Password Changed")

        return redirect("/user/settings/account")


class SettingsNotify(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("/login")

        notify = Notify.objects.get(user=request.user)
        return render(
            request, "settings_notify.html", {"user": request.user, "notify": notify}
        )

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect("/login")

        type = request.GET.get("type", None)
        notify = Notify.objects.get(user=request.user)

        if type == "comments":
            enable = request.POST.get("notify-comment")
            if enable:
                notify.on_comment = True
                notify.save()
            else:
                notify.on_comment = False
                notify.save()

        if type == "subscribe":
            enable = request.POST.get("notify-sub")
            if enable:
                notify.on_sub = True
                notify.save()
            else:
                notify.on_sub = False
                notify.save()

        return redirect("/user/settings/notifications")


def send_email_confirm(request):
    if request.POST:
        username = request.POST.get("user")
        if username:
            user = get_object_or_404(User, username=username)

        token, _ = EmailConfirmationToken.objects.get_or_create(user=user)
        send_confirmation_email(email=user.email, token_id=token.pk)
        messages.info(request, "Check your email for the verification link")
        return render(request, "email_confirm.html", {"is_email_confirmed": False})


def set_email_confirm(request):
    if request.GET:
        token_id = request.GET.get("token_id", None)
        try:
            token = EmailConfirmationToken.objects.get(pk=token_id)
            user = token.user
            user.is_email_confirmed = True
            user.save()
            token.delete()
            data = {"is_email_confirmed": True}
            return render(request, "email_confirm.html", data)
        except EmailConfirmationToken.DoesNotExist:
            data = {"is_email_confirmed": False}
            return render(request, "email_confirm.html", data)


def email_change(request):
    if request.POST:
        if not request.user.is_authenticated:
            return redirect("/login")

        user = request.user
        new_email = request.POST.get("email")

        if User.objects.filter(email=new_email).exists():
            messages.error(request, "A user with this email already exists")
            return redirect("/user/settings/account")

        token, _ = EmailConfirmationToken.objects.get_or_create(user=user)
        send_confirmation_email(email=new_email, token_id=token.pk, change=True)
        return render(
            request, "email_confirm.html", {"change": True, "email": new_email}
        )


def set_email_change_confirm(request):
    if request.GET:
        token_id = request.GET.get("token_id", None)
        email = request.GET.get("email", None)
        try:
            token = EmailConfirmationToken.objects.get(pk=token_id)
            user = token.user
            user.email = email
            user.save()
            token.delete()
            data = {"change": True, "is_email_confirmed": True}
            return render(request, "email_confirm.html", data)
        except EmailConfirmationToken.DoesNotExist:
            data = {"change": True, "is_email_confirmed": False}
            return render(request, "email_confirm.html", data)


class Passmail(View):
    def get(self, request):
        type = request.GET.get("type", None)
        return render(
            request, "passmail.html", {"is_password_confirmed": False, "type": type}
        )


class Passreset(View):
    def get(self, request):
        token_id = request.GET.get("token_id", None)
        return render(request, "passreset.html", {"token_id": token_id})


def send_pass_mail_confirm(request):
    if request.POST:
        t = request.POST.get("type", None)
        email = request.POST.get("email", None)

        if not User.objects.filter(email=email).exists():
            if t == "username":
                messages.error(request, "No user associated with that email")
                return redirect("/pass-mail?type=username")
            if t == "password":
                messages.error(request, "No user associated with that email")
                return redirect("/pass-mail?type=password")

        user = User.objects.get(email=email)

        if t == "username":
            send_username_email(email=email, username=user.username)
            messages.info(request, "Check your mail for your username")
            return redirect("/login")

        if t == "password":
            token, _ = EmailConfirmationToken.objects.get_or_create(user=user)
            send_password_email(email=email, token_id=token.pk)

            return render(
                request,
                "pass_confirm.html",
                {"is_password_confirmed": False, "type": t},
            )


def set_password_confirm(request):
    if request.POST:
        token_id = request.POST.get("token", None)
        password = request.POST.get("password", None)
        try:
            token = EmailConfirmationToken.objects.get(pk=token_id)
            user = token.user
            hasher = PBKDF2PasswordHasher()
            user.password = hasher.encode(password, hasher.salt())
            user.save()
            token.delete()
            data = {"is_password_confirmed": True, "type": type}
            return render(request, "pass_confirm.html", data)
        except EmailConfirmationToken.DoesNotExist:
            data = {"is_password_confirmed": False, "type": type}
            return render(request, "pass_confirm.html", data)


class Add(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("/login")

        return render(request, "add.html", {"user": request.user})

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect("/login")

        author = request.user
        title = request.POST.get("title")
        subtitle = request.POST.get("subtitle")
        text = request.POST.get("text")
        date = datetime.utcnow()

        if title and text:
            post = Post.objects.create(
                author=author,
                title=title,
                subtitle=subtitle,
                text=text,
                date=date,
                updated=date,
            )
            post.save()
            return redirect(f"/post/{post.id}")
        else:
            messages.error(request, "You must provide a Title and Content")
            return redirect(request.META.get("HTTP_REFERER"))


class BlogPost(View):
    def get(self, request, username, id):
        user = get_object_or_404(User, username=username)
        post = get_object_or_404(Post, pk=id, author=user)
        post.views += 1
        post.save()

        return render(request, "post.html", {"user": request.user, "post": post})
