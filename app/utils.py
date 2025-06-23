from django.core.mail import send_mail
from django.template.loader import get_template


def send_confirmation_email(email, token_id, change=None):
    data = {"token_id": str(token_id)}
    if change:
        data["email"] = email
        message = get_template("email/email_change.txt").render(data)
    else:
        message = get_template("email/email_confirm.txt").render(data)
    send_mail(
        subject="Please confirm your email",
        message=message,
        from_email="admin@app.com",
        recipient_list=[email],
        fail_silently=True,
    )


def send_comment_email(email, post, commenter, comment):
    data = {
        "post": post,
        "commenter": commenter,
        "comment": comment,
    }
    message = get_template("email/comment.txt").render(data)
    send_mail(
        subject="OpenTrader: Comment on post",
        message=message,
        from_email="admin@app.com",
        recipient_list=[email],
        fail_silently=True,
    )


def send_username_email(email, username):
    message = get_template("email/username.txt").render({"username": username})
    send_mail(
        subject="Your OpenTrader username",
        message=message,
        from_email="admin@app.com",
        recipient_list=[email],
        fail_silently=True,
    )


def send_password_email(email, token_id):
    data = {
        "token_id": str(token_id),
        "email": email,
    }
    message = get_template("email/password.txt").render(data)
    send_mail(
        subject="Your OpenTrader password recovery",
        message=message,
        from_email="admin@app.com",
        recipient_list=[email],
        fail_silently=True,
    )


# TODO: email subscribers after make a post
# only if the subscriber has that setting turned on for that blogger
# only accessible on blogger page by clicking notificatoin icon

# class post-notify
#    User -> User
#    Blogger -> User
#    notify = Bool
