# paradox/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from functools import wraps
import random
import os
import json
from pdf2image import convert_from_path
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse

from .models import User, Post, Document, Comment
from .helpers import is_email_verified, is_valid_mobile_number, is_valid_password, generate_username_suggestions


# ============================
# CUSTOM LOGIN DECORATOR
# ============================
def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            return redirect('sign_in')
        return view_func(request, *args, **kwargs)
    return wrapper


# ============================
# AUTHENTICATION VIEWS
# ============================

def sign_in(request):
    if request.method == 'POST':
        email_ = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email_)
            print("✅ User found:", user.email)
        except User.DoesNotExist:
            print("❌ User not found")
            return render(request, 'dashboard/sign_in.html', {'error': "User Does Not exist"})

        if not user.is_active:
            print("❌ User not verified")
            return render(request, 'dashboard/sign_in.html', {'error': "Your Account is not verified"})

        if check_password(password, user.password):
            print("✅ Password matched")
            request.session['user_id'] = user.id
            return redirect('index')
        else:
            print("❌ Wrong password")
            return render(request, 'dashboard/sign_in.html', {'error': "Wrong Password Please Try Again"})

    return render(request, 'dashboard/sign_in.html')


def sign_up(request):
    if request.method == 'POST':
        name_ = request.POST['name']
        email_ = request.POST['email']
        mobile_ = request.POST['mobile']
        password_ = request.POST['password']
        confirm_password_ = request.POST['confirm_password']

        if User.objects.filter(name=name_).exists():
            suggestions = generate_username_suggestions(name_)
            return render(request, 'dashboard/sign_up.html', {
                'error': "Name already taken. Try one of these:",
                'name_suggestions': suggestions
            })

        if not is_email_verified(email_):
            return render(request, 'dashboard/sign_up.html', {'error': "Invalid email address"})

        if User.objects.filter(email=email_).exists():
            return render(request, 'dashboard/sign_up.html', {'error': "Email already exists"})

        if not is_valid_mobile_number(mobile_):
            return render(request, 'dashboard/sign_up.html', {'error': "Enter valid +91 number"})

        if User.objects.filter(mobile=mobile_).exists():
            return render(request, 'dashboard/sign_up.html', {'error': "Mobile already registered"})

        if password_ != confirm_password_:
            return render(request, 'dashboard/sign_up.html', {'error': "Passwords do not match"})

        valid, error = is_valid_password(password_)
        if not valid:
            return render(request, 'dashboard/sign_up.html', {'error': error})

        user = User.objects.create(
            name=name_,
            email=email_,
            mobile=mobile_,
            password=make_password(password_),
        )

        otp_ = random.randint(111111, 999999)
        user.otp = otp_
        user.save()

        subject = "Email Confirmation | ParaDox"
        message = f"Hi {name_}, your OTP is {otp_}. Welcome to ParaDox!"
        send_mail(subject, message, settings.EMAIL_HOST_USER, [email_])

        return render(request, 'dashboard/email_verify.html', {'email': email_})

    return render(request, 'dashboard/sign_up.html')


def email_verify(request):
    if request.method == 'POST':
        email_ = request.POST['email']
        otp_ = request.POST['otp']

        try:
            user = User.objects.get(email=email_)
        except User.DoesNotExist:
            return render(request, 'dashboard/email_verify.html', {'email': email_, 'error': 'Email not found'})

        if str(user.otp) == str(otp_):
            user.is_active = True
            user.save()
            return redirect('sign_in')

        messages.error(request, "Invalid OTP")
        return render(request, 'dashboard/email_verify.html', {'email': email_})

    return render(request, 'dashboard/email_verify.html')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']

        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = request.build_absolute_uri(f'/reset_password/{uid}/{token}/')

            subject = 'Reset Your Password - ParaDox'
            message = f'Reset your password here:\n{reset_link}'
            send_mail(subject, message, settings.EMAIL_HOST_USER, [email])

            return render(request, 'dashboard/forgot_password.html', {
                'message': 'We sent a reset link to your email!'
            })

        except User.DoesNotExist:
            messages.error(request, 'Email not found!')

    return render(request, 'dashboard/forgot_password.html')


def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('new_password')
            password2 = request.POST.get('confirm_password')
            if password1 == password2:
                user.password = make_password(password1)
                user.save()
                messages.success(request, 'Password reset successful!')
                return redirect('sign_in')
            messages.error(request, 'Passwords do not match')
        return render(request, 'dashboard/reset_password.html')

    return render(request, 'dashboard/reset_invalid.html')


def logout(request):
    user = User.objects.get(id=request.session['user_id'])
    del request.session['user_id']
    messages.success(request, f"{user.name}, you have logged out successfully.", extra_tags='logout')
    return redirect('sign_in')

# ============================
# DASHBOARD VIEWS
# ============================

@login_required
def index(request):
    user_id = request.session.get('user_id')
    current_user = User.objects.get(id=user_id)

    query = request.GET.get('query', '')
    users = list(User.objects.filter(name__icontains=query).exclude(id=user_id)) if query else list(User.objects.exclude(id=user_id))
    documents = list(Document.objects.all())

    random.shuffle(users)
    random.shuffle(documents)

    for doc in documents:
        doc.comment_data = json.dumps([
            {
                "user": c.user.name,
                "text": c.text,
                "created_at": c.created_at.strftime("%b %d %H:%M")
            }
            for c in doc.comments.all()
        ], cls=DjangoJSONEncoder)

    return render(request, 'dashboard/index.html', {
        'users': users[:10],
        'documents': documents[:10],
        'query': query,
        'current_user': current_user
    })


@login_required
def profile(request):
    user = User.objects.get(id=request.session['user_id'])

    if request.method == 'POST' and request.FILES.get('document'):
        uploaded_file = request.FILES['document']
        title = request.POST.get('title')
        description = request.POST.get('description')

        doc = Document.objects.create(user=user, title=title, description=description, file=uploaded_file)

        if uploaded_file.name.endswith('.pdf'):
            try:
                pdf_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
                images = convert_from_path(pdf_path, first_page=1, last_page=1, poppler_path=settings.POPPLER_PATH)
                thumbnail_path = f"thumbnails/{doc.id}_thumb.jpg"
                full_path = os.path.join(settings.MEDIA_ROOT, thumbnail_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                images[0].save(full_path, 'JPEG')
                doc.thumbnail = thumbnail_path
                doc.save()
            except Exception as e:
                print("Thumbnail generation failed:", e)

    uploaded_docs = Document.objects.filter(user=user).order_by('-uploaded_at')
    return render(request, 'dashboard/profile.html', {
        'user': user,
        'uploaded_docs': uploaded_docs,
        'followers_count': user.followers.count(),
        'following_count': user.following.count(),
        'followers': user.followers.all(),
        'following': user.following.all()
    })


@login_required
def explore_docs(request):
    user_id = request.session.get('user_id')
    current_user = User.objects.get(id=user_id)

    users = list(User.objects.exclude(id=user_id))
    documents = list(Document.objects.all())

    random.shuffle(users)
    random.shuffle(documents)

    return render(request, 'dashboard/explore_docs.html', {
        'users': users,
        'documents': documents,
        'current_user': current_user
    })


@login_required
def explore_profile(request):
    user_id = request.session.get('user_id')
    current_user = User.objects.get(id=user_id)

    users = list(User.objects.exclude(id=user_id))
    documents = list(Document.objects.all())

    random.shuffle(users)
    random.shuffle(documents)

    return render(request, 'dashboard/explore_profile.html', {
        'users': users,
        'documents': documents,
        'current_user': current_user
    })


@login_required
def public_profile(request, user_id):
    user_profile = User.objects.get(id=user_id)
    current_user = User.objects.get(id=request.session['user_id'])
    documents = Document.objects.filter(user=user_profile).order_by('-uploaded_at')
    return render(request, 'dashboard/public_profile.html', {
        'user_profile': user_profile,
        'current_user': current_user,
        'documents': documents,
        'followers_count': user_profile.followers.count(),
        'following_count': user_profile.following.count(),
        'followers': user_profile.followers.all(),
        'following': user_profile.following.all()
    })


@login_required
def toggle_follow(request, user_id):
    if request.method == 'POST':
        current_user = get_object_or_404(User, id=request.session.get('user_id'))
        target_user = get_object_or_404(User, id=user_id)

        if current_user != target_user:
            if target_user in current_user.following.all():
                current_user.following.remove(target_user)
            else:
                current_user.following.add(target_user)

        return redirect('public_profile', user_id=user_id)


@login_required
def edit_profile(request):
    user = User.objects.get(id=request.session['user_id'])

    if request.method == 'POST':
        user.name = request.POST.get('name')
        user.bio = request.POST.get('bio')
        image = request.FILES.get('profile_image')

        if image:
            user.profile_image = image

        user.save()
        return redirect('profile')

    return render(request, 'dashboard/edit_profile.html', {'user': user})


@login_required
def update_document(request, doc_id):
    document = Document.objects.get(id=doc_id)

    if request.method == 'POST':
        document.title = request.POST.get('title')
        document.description = request.POST.get('description')
        if request.FILES.get('document'):
            document.file = request.FILES['document']
        document.save()
        return redirect('profile')

    return render(request, 'dashboard/update_document.html', {'document': document})


@login_required
def delete_document(request, doc_id):
    user_id = request.session.get('user_id')
    try:
        document = Document.objects.get(id=doc_id, user_id=user_id)
        document.file.delete()
        document.delete()
        messages.success(request, "Document deleted successfully.")
    except Document.DoesNotExist:
        messages.error(request, "Document not found or not authorized.")

    return redirect('profile')


@login_required
def add_comment(request, doc_id):
    if request.method == 'POST':
        user = User.objects.get(id=request.session['user_id'])
        document = get_object_or_404(Document, id=doc_id)
        text = request.POST.get('comment', '').strip()
        if text:
            comment = Comment.objects.create(user=user, document=document, text=text)
            return JsonResponse({
                'user': comment.user.name,
                'text': comment.text,
                'created_at': comment.created_at.strftime('%b %d %H:%M')
            })
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ============================
# POST MANAGEMENT
# ============================

@login_required
def show(request):
    posts = Post.objects.all()
    return render(request, 'dashboard/show.html', {'posts': posts})


@login_required
def insert(request):
    if request.method == 'POST':
        Post.objects.create(
            image=request.FILES['post_image'],
            title=request.POST['title'],
            content=request.POST['content']
        )
        return redirect('show')
    return render(request, 'dashboard/insert.html')


@login_required
def delete_post(request, post_id):
    post = Post.objects.get(id=post_id)
    post.delete()
    return redirect('show')


# ============================
# SEARCH & ANALYTICS
# ============================

@login_required
def search(request):
    user_id = request.session.get('user_id')
    current_user = User.objects.get(id=user_id)
    query = request.GET.get('query', '')

    users = User.objects.filter(name__icontains=query).exclude(id=user_id)
    documents = Document.objects.filter(title__icontains=query)

    return render(request, 'dashboard/search_results.html', {
        'users': users,
        'documents': documents,
        'query': query,
        'current_user': current_user,
    })


@login_required
def analytics(request):
    return render(request, 'dashboard/analytics.html')


# ============================
# STATIC PAGES
# ============================

def terms(request):
    return render(request, 'dashboard/terms.html')


def about_us(request):
    return render(request, 'dashboard/about_us.html')


def contact_us(request):
    return render(request, 'dashboard/contact_us.html')

