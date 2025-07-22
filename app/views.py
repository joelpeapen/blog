from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.db.models import (
    Q,
    BooleanField,
    Case,
    Count,
    Exists,
    OuterRef,
    Subquery,
    When,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from app.models import (
    Blog,
    Comment,
    EmailConfirmationToken,
    Notify,
    Post,
    Subscriber,
    Tag,
    User,
)
from app.utils import (
    send_comment_email,
    send_confirmation_email,
    send_password_email,
    send_post_email,
    send_subscribe_email,
    send_subscriber_email,
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
        ret = request.GET.get("return")

        if username and password:
            if not User.objects.filter(username=username).exists():
                messages.error(request, "No such user")
                return redirect("/login")

            user = authenticate(username=username, password=password)
            if user:
                if user.is_email_confirmed:
                    login(request, user)
                    if ret:
                        return redirect(ret)
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


class AppUser(View):
    def get(self, request, username=None):
        subscount = (
            Subscriber.objects.filter(blog=OuterRef("pk"))
            .values("blog")
            .annotate(count=Count("id"))
            .values("count")
        )

        if username:
            profile = get_object_or_404(User, username=username)
            blogs = (
                Blog.objects.filter(author=profile)
                .annotate(
                    subscriber_count=Subquery(subscount),
                )
                .order_by("-subscriber_count")
            )

            return render(
                request,
                "user.html",
                {
                    "profile": profile,
                    "user": request.user,
                    "posts": Post.objects.filter(author=profile).order_by("-date"),
                    "blogs": blogs,
                    "count": blogs.count(),
                    "type": "posts",
                },
            )

        # /user/ -> logged-in user's page
        if request.user.is_authenticated:
            blogs = (
                Blog.objects.filter(author=request.user)
                .annotate(
                    subscriber_count=Subquery(subscount),
                    is_subscribed=Exists(
                        Subscriber.objects.filter(
                            user=request.user, blog=OuterRef("pk")
                        )
                    ),
                )
                .order_by("-subscriber_count")
            )

            return render(
                request,
                "user.html",
                {
                    "profile": request.user,
                    "user": request.user,
                    "posts": Post.objects.filter(author=request.user).order_by("-date"),
                    "blogs": blogs,
                    "count": blogs.count(),
                    "type": "posts",
                },
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

        blogs = Blog.objects.filter(author=request.user)
        return render(request, "add.html", {"user": request.user, "blogs": blogs})

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect("/login")

        author = request.user
        blogname = request.POST.get("blog")
        title = request.POST.get("title")
        subtitle = request.POST.get("subtitle")
        text = request.POST.get("text")
        date = datetime.utcnow()
        splash = request.FILES.get("splash")
        splashdesc = request.POST.get("splashdesc")
        limit = request.POST.get("limit-comments")
        nocomment = request.POST.get("no-comments")
        subonly = request.POST.get("sub-only")

        if blogname and title and text:
            blog = get_object_or_404(Blog, name=blogname)

            if author != blog.author:
                messages.error(request, "You do not own that blog")
                return redirect(request.META.get("HTTP_REFERER"))

            post = Post.objects.create(
                author=author,
                blog=blog,
                title=title,
                subtitle=subtitle,
                text=text,
                date=date,
                updated=date,
            )

            if splash:
                post.splash = splash
                post.splashdesc = splashdesc

            if nocomment:
                post.no_comments = True

            if limit:
                post.limit_comments = True

            if subonly:
                post.subonly = True

            post.save()

            for s in Subscriber.objects.filter(blog=blog):
                if s.notify:
                    send_post_email(s.user.email, blog, post)

            return redirect(f"/{post.author}/post/{post.id}")
        else:
            messages.error(request, "You must provide a Blog, Title, and Content")
            return redirect(request.META.get("HTTP_REFERER"))


class Edit(View):
    def get(self, request, id):
        post = get_object_or_404(Post, pk=id)

        if not request.user.is_authenticated or request.user != post.author:
            return redirect(f"/{post.author}/post/{id}")

        nosplash = False
        if not post.splash:
            nosplash = True
        elif "default.png" in post.splash.url:
            nosplash = True

        blogs = Blog.objects.filter(author=request.user)
        return render(
            request,
            "edit.html",
            {"user": request.user, "post": post, "nosplash": nosplash, "blogs": blogs},
        )

    def post(self, request, id):
        post = get_object_or_404(Post, pk=id)

        if not request.user.is_authenticated or request.user != post.author:
            return redirect(f"/{post.author}/post/{id}")

        blogname = request.POST.get("blog")
        title = request.POST.get("title")
        subtitle = request.POST.get("subtitle")
        text = request.POST.get("text")
        splash = request.FILES.get("splash")
        splashdesc = request.POST.get("splashdesc")
        delete = request.POST.get("delete-splash")
        limit = request.POST.get("limit-comments")
        nocomment = request.POST.get("no-comments")
        subonly = request.POST.get("sub-only")

        if not blogname:
            messages.error(request, "Must select a blog")
            return redirect(f"/edit/{id}")
        elif blogname != post.blog:
            blog = get_object_or_404(Blog, name=blogname)
            post.blog = blog

        if request.user != blog.author:
            messages.error(request, "You do not own that blog")
            return redirect(f"/edit/{id}")

        if title != post.title:
            post.title = title

        if subtitle != post.subtitle:
            post.subtitle = subtitle

        if text != post.text:
            post.text = text

        if delete:
            post.splash = None
            post.splashdesc = None
        elif splash:
            post.splash = splash

        if splashdesc != post.splashdesc:
            post.splashdesc = splashdesc

        if nocomment:
            post.no_comments = True
        else:
            post.no_comments = False

        if limit:
            post.limit_comments = True
        else:
            post.limit_comments = False

        if subonly:
            post.subonly = True
        else:
            post.subonly = False

        post.updated = datetime.utcnow()

        post.save()
        messages.success(request, "Post Updated")
        return redirect(f"/{post.author}/post/{id}")


class Delete(View):
    def get(self, request, id):
        post = get_object_or_404(Post, pk=id)

        if not request.user.is_authenticated or request.user != post.author:
            return redirect(f"/{post.author}/post/{id}")

        post.delete()
        return redirect("/user")


class Like(View):
    def post(self, request, id):
        post = get_object_or_404(Post, pk=id)

        if not request.user.is_authenticated:
            return redirect(f"/{post.author}/post/{id}")

        if request.user.likes.filter(pk=id).exists():
            post.likes -= 1
            request.user.likes.remove(post)
            post.save()
        else:
            post.likes += 1
            request.user.likes.add(post)
            post.save()

        return redirect(f"/{post.author}/post/{id}")


class Likes(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("/login")

        posts = request.user.likes.all()
        return render(
            request,
            "likes.html",
            {"user": request.user, "posts": posts, "count": posts.count()},
        )


class Posts(View):
    def get(self, request):
        posts = Post.objects.all().order_by("-date")
        count = posts.count()
        return render(
            request,
            "posts.html",
            {"user": request.user, "posts": posts, "count": count},
        )


class Blogs(View):
    def get(self, request):
        if request.user.is_authenticated:
            blogs = Blog.objects.annotate(
                subscriber_count=Count("subscriber"),
                is_subscribed=Exists(
                    Subscriber.objects.filter(user=request.user, blog=OuterRef("pk"))
                ),
            ).order_by("-subscriber_count")

            count = blogs.count()
        else:
            blogs = Blog.objects.annotate(
                subscriber_count=Count("subscriber"),
            ).order_by("-subscriber_count")

            count = blogs.count()

        return render(request, "blogs.html", {"blogs": blogs, "count": count})


class UserBlog(View):
    def get(self, request, name):
        blog = get_object_or_404(Blog, name=name)
        posts = Post.objects.filter(blog=blog)
        count = posts.count()

        nosplash = False
        if blog.splash:
            if "default.png" in blog.splash.url:
                nosplash = True
        else:
            nosplash = True

        data = {
            "user": request.user,
            "blog": blog,
            "posts": posts,
            "nosplash": nosplash,
            "count": count,
        }

        if request.user.is_authenticated:
            try:
                subscriber = Subscriber.objects.get(blog=blog, user=request.user)
                data["subscriber"] = subscriber
                data["is_subscribed"] = True
            except Subscriber.DoesNotExist:
                data["subscriber"] = None
                data["is_subscribed"] = False

        data["subscriber_count"] = Subscriber.objects.filter(blog=blog).count()
        return render(request, "blog.html", data)


class BlogAdd(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("/login")

        return render(request, "blogadd.html", {"user": request.user})

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect("/login")

        author = request.user
        name = request.POST.get("name")
        about = request.POST.get("about")
        splash = request.FILES.get("splash")
        welcome = request.POST.get("welcome")

        if Blog.objects.filter(name=name).exists():
            messages.error(request, "A blog with that name already exists")
            return redirect(request.META.get("HTTP_REFERER"))

        if name and about and welcome:
            blog = Blog.objects.create(
                author=author,
                name=name,
                about=about,
                date=datetime.utcnow(),
                welcome=welcome,
            )

            if splash:
                blog.splash = splash
                blog.save()

            return redirect(f"/blog/{blog.name}")
        else:
            messages.error(
                request, "You must provide a Name and About, and welcome message"
            )
            return redirect(request.META.get("HTTP_REFERER"))


class BlogEdit(View):
    def get(self, request, name):
        blog = get_object_or_404(Blog, name=name)

        if not request.user.is_authenticated or request.user != blog.author:
            return redirect(f"/blog/{name}")

        nosplash = False
        if not blog.splash:
            nosplash = True
        elif "default.png" in blog.splash.url:
            nosplash = True

        return render(
            request,
            "blogedit.html",
            {"user": request.user, "blog": blog, "nosplash": nosplash},
        )

    def post(self, request, name):
        blog = get_object_or_404(Blog, name=name)

        if not request.user.is_authenticated or request.user != blog.author:
            return redirect(f"/blog/{name}")

        name = request.POST.get("name")
        about = request.POST.get("about")
        splash = request.FILES.get("splash")
        delete = request.POST.get("delete-splash")
        welcome = request.POST.get("welcome")

        if name and about and welcome:
            blog.name = name
            blog.about = about
            blog.welcome = welcome

            if delete:
                blog.splash = None
            elif splash:
                blog.splash = splash

            blog.save()
            return redirect(f"/blog/{blog.name}")
        else:
            messages.error(
                request, "You must provide a Name and About, and welcome message"
            )
            return redirect(request.META.get("HTTP_REFERER"))


class BlogDelete(View):
    def get(self, request, name):
        blog = get_object_or_404(Blog, name=name)

        if not request.user.is_authenticated and request.user != blog.author:
            return redirect("/login")

        blog.delete()
        messages.success(request, f"Blog {name} has been deleted")
        return redirect("/user")


class BlogPost(View):
    def get(self, request, username, id):
        author = get_object_or_404(User, username=username)
        post = get_object_or_404(Post, pk=id, author=author)
        comments = Comment.objects.filter(post=id)
        tags = post.tags.all()

        nosplash = False
        if post.splash:
            if "default.png" in post.splash.url:
                nosplash = True
        else:
            nosplash = True

        viewable = True
        if post.subonly:
            if request.user.is_authenticated:
                if not Subscriber.objects.filter(
                    blog=post.blog, user=request.user
                ).exists():
                    viewable = False
            else:
                viewable = False

        post.views += 1
        post.save()

        return render(
            request,
            "post.html",
            {
                "user": request.user,
                "post": post,
                "nosplash": nosplash,
                "comments": comments,
                "count": comments.count(),
                "tags": tags,
                "viewable": viewable,
            },
        )


class Subscribe(View):
    def get(self, request, name):
        if not request.user.is_authenticated:
            return redirect(request, "/login")

        blog = Blog.objects.get(name=name)
        sub, new = Subscriber.objects.get_or_create(blog=blog, user=request.user)

        if not new:
            sub.delete()
        else:
            send_subscriber_email(request.user.email, blog)
            notify = Notify.objects.get(user=blog.author)
            if notify.on_sub:
                send_subscribe_email(blog.author.email, request.user, blog)

        return redirect(request.META.get("HTTP_REFERER"))


class Subnotify(View):
    def get(self, request, name):
        if not request.user.is_authenticated:
            return redirect(request, "/login")

        blog = get_object_or_404(Blog, name=name)
        sub, new = Subscriber.objects.get_or_create(blog=blog, user=request.user)

        if not new:
            sub.notify = not sub.notify
            sub.save()

        return redirect(f"/blog/{blog.name}")


class Subscriptions(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("/login")

        subscount = (
            Subscriber.objects.filter(blog=OuterRef("pk"))
            .values("blog")
            .annotate(count=Count("id"))
            .values("count")
        )

        blogs = (
            Blog.objects.filter(subscriber__user=request.user)
            .annotate(
                subscriber_count=Subquery(subscount),
                is_subscribed=Exists(
                    Subscriber.objects.filter(user=request.user, blog=OuterRef("pk"))
                ),
            )
            .order_by("-subscriber_count")
        )
        count = blogs.count()

        return render(request, "subscriptions.html", {"blogs": blogs, "count": count})


class Comments(View):
    def get(self, request, username):
        if not request.user.is_authenticated:
            return redirect("/login")

        user = get_object_or_404(User, username=username)

        subquery = Subscriber.objects.filter(
            user=request.user, blog=OuterRef("post__blog")
        )

        comments = Comment.objects.filter(user=user).annotate(
            viewable=Case(
                When(post__subonly=True, then=Exists(subquery)),
                When(post__subonly=False, then=True),
                output_field=BooleanField(),
            )
        )

        return render(
            request,
            "comments.html",
            {
                "user": request.user,
                "profile": user,
                "comments": comments,
                "count": comments.count(),
            },
        )


class CommentAdd(View):
    def post(self, request, id):
        if not request.user.is_authenticated:
            return redirect(request, "/login")

        comment = request.POST.get("comment")
        post = get_object_or_404(Post, pk=id)

        if comment:
            if post.no_comments:
                messages.error(request, "Comments are turned off")
                return redirect(f"/{post.author}/post/{post.id}")

            if post.limit_comments:
                if not Subscriber.objects.filter(
                    blog=post.blog, user=request.user
                ).exists():
                    messages.error(request, "Only subscribers can comment")
                    return redirect(f"/{post.author}/post/{post.id}")

            Comment.objects.create(
                text=comment, post=post, user=request.user, date=datetime.utcnow()
            )

            if request.user != post.author:
                notify = Notify.objects.get(user=post.author)
                if notify.on_comment:
                    send_comment_email(post.author.email, post, request.user, comment)

            return redirect(f"/{post.author}/post/{id}")
        else:
            messages.error(request, "Must add a comment and rating")
            return redirect(f"/{post.author}/post/{id}")

        return redirect(f"/{post.author}/post/{id}#cm{comment.id}")


class CommentEdit(View):
    def post(self, request, id):
        text = request.POST.get("comment")
        comment = get_object_or_404(Comment, pk=id)
        post = comment.post

        if not request.user.is_authenticated:
            return redirect(f"/{post.author}/post/{post.id}#cm{comment.id}")

        if text:
            if post.no_comments:
                messages.error(request, "Comments are turned off")
                return redirect(f"/{post.author}/post/{post.id}")

            if post.limit_comments:
                if not Subscriber.objects.filter(
                    blog=post.blog, user=request.user
                ).exists():
                    messages.error(request, "Only subscribers can comment")
                    return redirect(f"/{post.author}/post/{post.id}")

            comment.text = text
            comment.save()
            return redirect(f"/{post.author}/post/{post.id}#cm{comment.id}")
        else:
            messages.error(request, "Must add a comment and rating")
            return redirect(f"/{post.author}/post/{post.id}#cm{comment.id}")

            return redirect(f"/{post.author}/post/{post.id}#cm{comment.id}")


class CommentDelete(View):
    def post(self, request, id):
        comment = get_object_or_404(Comment, pk=id)

        if not request.user.is_authenticated:
            return redirect(f"/{comment.post.author}/post/{comment.post.id}")

        if comment.user == request.user:
            comment.delete()
        return redirect(f"/{comment.post.author}/post/{comment.post.id}")


class CommentLike(View):
    def post(self, request, id):
        comment = get_object_or_404(Comment, pk=id)

        if not request.user.is_authenticated:
            return redirect(
                f"/{comment.post.author}/post/{comment.post.id}#cm{comment.id}"
            )

        if request.user.comment_likes.filter(pk=id).exists():
            comment.likes -= 1
            request.user.comment_likes.remove(comment)
            comment.save()
        else:
            comment.likes += 1
            request.user.comment_likes.add(comment)
            comment.save()

        return redirect(request.META.get("HTTP_REFERER"))


class Tags(View):
    def get(self, request, name):
        tags = Tag.objects.filter(name=name)
        posts = set()

        for tag in tags:
            posts.update(tag.post_tags.all())

        data = {
            "user": request.user,
            "posts": list(posts),
            "count": len(posts),
        }

        try:
            tag = tags[0]
            data["tag"] = tag
        except IndexError:
            return redirect("/404")

        return render(request, "tags.html", data)


class TagAdd(View):
    def post(self, request, id):
        post = get_object_or_404(Post, pk=id)

        if not request.user.is_authenticated or request.user != post.author:
            messages.error(request, "only the post author can add tags")
            return redirect(f"/{post.author}/post/{id}")

        tag_name = request.POST.get("tag")

        if tag_name:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            post.tags.add(tag)
        else:
            messages.error(request, "Tag cannot be empty")

        return redirect(f"/{post.author}/post/{id}")


class TagDelete(View):
    def post(self, request, pid, tid):
        post = get_object_or_404(Post, pk=pid)

        if not request.user.is_authenticated or request.user != post.author:
            messages.error(request, "only post author can delete tags")
            return redirect(f"/{post.author}/post/{pid}")

        tag = get_object_or_404(Tag, pk=tid)
        post.tags.remove(tag)

        return redirect(f"/{post.author}/post/{pid}")


class Search(View):
    def get(self, request):
        query = request.GET.get("query", None)
        username = request.GET.get("user", None)
        taip = request.GET.get("type", None)
        filter = request.GET.get("filter", None)
        blog = request.GET.get("blog", None)
        data = {}
        qf = Q()

        if taip == "blogs":
            qf |= Q(name__icontains=query) | Q(about__icontains=query)

            if username:
                try:
                    u = User.objects.get(username=username)
                    qf &= Q(author=u)
                except User.DoesNotExist:
                    pass

            if filter == "subs":
                qf &= Q(subscriber__user=request.user)
            elif filter == "likes":
                qf &= Q(id__in=request.user.likes.values_list("id", flat=True))

            if request.user.is_authenticated:
                blogs = (
                    Blog.objects.filter(qf)
                    .annotate(
                        subscriber_count=Count("subscriber"),
                        is_subscribed=Exists(
                            Subscriber.objects.filter(
                                user=request.user, blog=OuterRef("pk")
                            )
                        ),
                    )
                    .order_by("-subscriber_count")
                    .distinct()
                )
            else:
                blogs = (
                    Blog.objects.filter(qf)
                    .annotate(subscriber_count=Count("subscriber"))
                    .order_by("-subscriber_count")
                    .distinct()
                )

            data["blogs"] = blogs
            data["count"] = len(blogs)
        elif taip == "posts":
            qf |= (
                Q(title__icontains=query)
                | Q(subtitle__icontains=query)
                | Q(text__icontains=query)
            )

            if username:
                try:
                    u = User.objects.get(username=username)
                    qf &= Q(author=u)
                except User.DoesNotExist:
                    pass

            if blog:
                qf &= Q(blog__name=blog)

            if filter == "subs":
                qf &= Q(subscriber__user=request.user)
            elif filter == "likes":
                qf &= Q(id__in=request.user.likes.values_list("id", flat=True))

            posts = Post.objects.filter(qf).order_by("-views")
            data["posts"] = posts
            data["count"] = len(posts)

        data.update(
            {
                "query": query,
                "username": username,
                "type": taip,
            }
        )

        return render(request, "search.html", data)
