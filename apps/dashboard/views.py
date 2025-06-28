# paradox/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.http import JsonResponse
from functools import wraps
import os, random, json
from pdf2image import convert_from_path
from django.core.serializers.json import DjangoJSONEncoder

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
            if not user.is_active:
                return render(request, 'dashboard/sign_in.html', {'error': "Account not verified."})
            if check_password(password, user.password):
                request.session['user_id'] = user.id
                return redirect('index')
            return render(request, 'dashboard/sign_in.html', {'error': "Incorrect password."})
        except User.DoesNotExist:
            return render(request, 'dashboard/sign_in.html', {'error': "User not found."})
    return render(request, 'dashboard/sign_in.html')

def sign_up(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        mobile = request.POST['mobile']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if User.objects.filter(name=name).exists():
            suggestions = generate_username_suggestions(name)
            return render(request, 'dashboard/sign_up.html', {
                'error': "Name taken. Suggestions:", 'name_suggestions': suggestions
            })

        if not is_email_verified(email):
            return render(request, 'dashboard/sign_up.html', {'error': "Invalid email."})
        if User.objects.filter(email=email).exists():
            return render(request, 'dashboard/sign_up.html', {'error': "Email already registered."})
        if not is_valid_mobile_number(mobile):
            return render(request, 'dashboard/sign_up.html', {'error': "Invalid mobile number."})
        if User.objects.filter(mobile=mobile).exists():
            return render(request, 'dashboard/sign_up.html', {'error': "Mobile already used."})
        if password != confirm_password:
            return render(request, 'dashboard/sign_up.html', {'error': "Passwords do not match."})

        valid, error = is_valid_password(password)
        if not valid:
            return render(request, 'dashboard/sign_up.html', {'error': error})

        user = User.objects.create(
            name=name,
            email=email,
            mobile=mobile,
            password=make_password(password),
            is_active=False
        )
        otp = random.randint(100000, 999999)
        user.otp = otp
        user.save()

        subject = "Verify your ParaDox account"
        message = f"Hi {name}, your OTP is {otp}."
        send_mail(subject, message, settings.EMAIL_HOST_USER, [email])

        return render(request, 'dashboard/email_verify.html', {'email': email})
    return render(request, 'dashboard/sign_up.html')

def email_verify(request):
    if request.method == 'POST':
        email = request.POST['email']
        otp = request.POST['otp']
        try:
            user = User.objects.get(email=email)
            if str(user.otp) == str(otp):
                user.is_active = True
                user.save()
                return redirect('sign_in')
            messages.error(request, "Invalid OTP")
        except User.DoesNotExist:
            messages.error(request, "Email not found")
    return render(request, 'dashboard/email_verify.html', {'email': request.POST.get('email')})

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = request.build_absolute_uri(f'/reset_password/{uid}/{token}/')
            send_mail("Reset Password", f"Reset here: {reset_link}", settings.EMAIL_HOST_USER, [email])
            return render(request, 'dashboard/forgot_password.html', {'message': 'Link sent to your email'})
        except User.DoesNotExist:
            messages.error(request, 'Email not found')
    return render(request, 'dashboard/forgot_password.html')

def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (ValueError, TypeError, User.DoesNotExist):
        user = None
    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            p1 = request.POST['new_password']
            p2 = request.POST['confirm_password']
            if p1 == p2:
                user.password = make_password(p1)
                user.save()
                messages.success(request, "Password reset successful")
                return redirect('sign_in')
            messages.error(request, "Passwords do not match")
        return render(request, 'dashboard/reset_password.html')
    return render(request, 'dashboard/reset_invalid.html')

def logout(request):
    request.session.flush()
    messages.success(request, "Logged out successfully.")
    return redirect('sign_in')

# ============================
# MAIN VIEWS
# ============================
@login_required
def index(request):
    user_id = request.session.get('user_id')
    current_user = User.objects.get(id=user_id)
    query = request.GET.get('query', '')
    users = User.objects.filter(name__icontains=query).exclude(id=user_id) if query else User.objects.exclude(id=user_id)
    documents = list(Document.objects.all())

    random.shuffle(documents)
    for doc in documents:
        doc.comment_data = json.dumps([
            {"user": c.user.name, "text": c.text, "created_at": c.created_at.strftime("%b %d %H:%M")}
            for c in doc.comments.all()
        ], cls=DjangoJSONEncoder)

    return render(request, 'dashboard/index.html', {
        'users': users[:10], 'documents': documents[:10], 'current_user': current_user
    })

@login_required
def profile(request):
    user = User.objects.get(id=request.session['user_id'])
    if request.method == 'POST' and request.FILES.get('document'):
        uploaded = request.FILES['document']
        title = request.POST.get('title')
        desc = request.POST.get('description')
        doc = Document.objects.create(user=user, title=title, description=desc, file=uploaded)

        if uploaded.name.endswith('.pdf'):
            try:
                path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
                img = convert_from_path(path, first_page=1, last_page=1, poppler_path=settings.POPPLER_PATH)[0]
                thumb_path = f"thumbnails/{doc.id}_thumb.jpg"
                full_path = os.path.join(settings.MEDIA_ROOT, thumb_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                img.save(full_path, 'JPEG')
                doc.thumbnail = thumb_path
                doc.save()
            except Exception as e:
                print("Thumbnail failed:", e)

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
    user_id = request.session['user_id']
    current_user = User.objects.get(id=user_id)
    documents = list(Document.objects.all())
    random.shuffle(documents)
    return render(request, 'dashboard/explore_docs.html', {
        'users': User.objects.exclude(id=user_id),
        'documents': documents,
        'current_user': current_user
    })

@login_required
def explore_profile(request):
    return explore_docs(request)  # same logic, different template if needed

@login_required
def public_profile(request, user_id):
    user_profile = User.objects.get(id=user_id)
    current_user = User.objects.get(id=request.session['user_id'])
    docs = Document.objects.filter(user=user_profile)
    return render(request, 'dashboard/public_profile.html', {
        'user_profile': user_profile,
        'current_user': current_user,
        'documents': docs,
        'followers_count': user_profile.followers.count(),
        'following_count': user_profile.following.count()
    })

@login_required
def toggle_follow(request, user_id):
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
    doc = Document.objects.get(id=doc_id)
    if request.method == 'POST':
        doc.title = request.POST['title']
        doc.description = request.POST['description']
        if request.FILES.get('document'):
            doc.file = request.FILES['document']
        doc.save()
        return redirect('profile')
    return render(request, 'dashboard/update_document.html', {'document': doc})

@login_required
def delete_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id, user_id=request.session['user_id'])
    doc.file.delete()
    doc.delete()
    messages.success(request, "Document deleted.")
    return redirect('profile')

@login_required
def add_comment(request, doc_id):
    if request.method == 'POST':
        user = User.objects.get(id=request.session['user_id'])
        doc = get_object_or_404(Document, id=doc_id)
        text = request.POST.get('comment', '').strip()
        if text:
            c = Comment.objects.create(user=user, document=doc, text=text)
            return JsonResponse({'user': c.user.name, 'text': c.text, 'created_at': c.created_at.strftime('%b %d %H:%M')})
    return JsonResponse({'error': 'Invalid'}, status=400)

# POSTS
@login_required
def show(request):
    return render(request, 'dashboard/show.html', {'posts': Post.objects.all()})

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
    get_object_or_404(Post, id=post_id).delete()
    return redirect('show')

@login_required
def search(request):
    uid = request.session['user_id']
    query = request.GET.get('query', '')
    return render(request, 'dashboard/search_results.html', {
        'users': User.objects.filter(name__icontains=query).exclude(id=uid),
        'documents': Document.objects.filter(title__icontains=query),
        'current_user': User.objects.get(id=uid),
        'query': query
    })

@login_required
def analytics(request):
    return render(request, 'dashboard/analytics.html')

# STATIC PAGES
def terms(request): return render(request, 'dashboard/terms.html')
def about_us(request): return render(request, 'dashboard/about_us.html')
def contact_us(request): return render(request, 'dashboard/contact_us.html')
