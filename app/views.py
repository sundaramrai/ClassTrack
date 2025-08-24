from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from app.models import StudentProfile, TeacherProfile, Class, Division
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

# Brute-force protection settings
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_WINDOW = 900  # 15 minutes
LOGIN_TEMPLATE = "app/auth/login.html"
CONTACT_TEMPLATE = "app/contact/contact.html"
RESET_PASSWORD_TEMPLATE = "app/auth/reset_password.html"
RESET_PASSWORD_CONFIRM_TEMPLATE = "app/auth/reset_password_confirm.html"


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_rate_limited(identifier: str) -> bool:
    cache_key = f"login_attempts_{identifier}"
    attempts = cache.get(cache_key, 0)
    return attempts >= MAX_LOGIN_ATTEMPTS

def increment_login_attempts(identifier: str):
    cache_key = f"login_attempts_{identifier}"
    attempts = cache.get(cache_key, 0)
    cache.set(cache_key, attempts + 1, LOGIN_ATTEMPT_WINDOW)

def clear_login_attempts(identifier: str):
    cache_key = f"login_attempts_{identifier}"
    cache.delete(cache_key)

# Create your views here.
def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, "app/index.html")

@csrf_protect
def contact(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        message = request.POST.get("message", "").strip()
        # Input validation
        if not name or not email or not message:
            messages.error(request, "All fields are required.")
            return render(request, CONTACT_TEMPLATE)
        if len(name) > 100 or len(message) > 1000:
            messages.error(request, "Name or message too long.")
            return render(request, CONTACT_TEMPLATE)
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return render(request, CONTACT_TEMPLATE)
        subject = f"New Contact Form Submission from {name}"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #2c3e50;">New Contact Form Submission</h2>
            <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Name:</td>
                    <td style="padding: 8px;">{name}</td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 8px; font-weight: bold;">Email:</td>
                    <td style="padding: 8px;">{email}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold; vertical-align: top;">Message:</td>
                    <td style="padding: 8px; white-space: pre-line;">{message}</td>
                </tr>
            </table>
            <p style="margin-top: 24px; font-size: 12px; color: #888;">This message was sent from the contact form on your website.</p>
        </body>
        </html>
        """
        body = f"New Contact Form Submission\n\nName: {name}\nEmail: {email}\nMessage:\n{message}"
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[settings.EMAIL_HOST_USER],
                fail_silently=False,
                html_message=html_body,
            )
            messages.success(request, "Your message has been sent successfully!")
            return redirect("contact")
        except Exception:
            messages.error(request, "Error sending message. Please try again later.")
    return render(request, CONTACT_TEMPLATE)

def _find_user_by_student(user_input):
    try:
        student_profile = StudentProfile.objects.get(student_id=user_input)
        return student_profile.user, True, False
    except StudentProfile.DoesNotExist:
        try:
            student_profile = StudentProfile.objects.get(user__email=user_input)
            return student_profile.user, True, False
        except StudentProfile.DoesNotExist:
            return None, False, False

def _find_user_by_teacher(user_input):
    try:
        teacher_profile = TeacherProfile.objects.get(employee_id=user_input)
        return teacher_profile.user, False, True
    except TeacherProfile.DoesNotExist:
        try:
            teacher_profile = TeacherProfile.objects.get(user__email=user_input)
            return teacher_profile.user, False, True
        except TeacherProfile.DoesNotExist:
            return None, False, False

def _find_user_by_admin(user_input):
    try:
        user = User.objects.get(email=user_input)
        return user, False, False
    except User.DoesNotExist:
        try:
            user = User.objects.get(username=user_input)
            return user, False, False
        except User.DoesNotExist:
            return None, False, False

def _must_reset_password(user, is_student, is_teacher):
    if is_student and hasattr(user, 'student_profile'):
        return getattr(user.student_profile, 'must_reset_password', False)
    if is_teacher and hasattr(user, 'teacher_profile'):
        return getattr(user.teacher_profile, 'must_reset_password', False)
    return False

@csrf_protect
@require_http_methods(["GET", "POST"])
def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == "POST":
        user_input = request.POST.get('user', '').strip()
        password = request.POST.get('password', '')
        client_ip = get_client_ip(request)
        rate_limit_key = f"{client_ip}_{user_input}"
        if is_rate_limited(rate_limit_key):
            messages.error(request, "Too many failed login attempts. Please try again later.")
            return render(request, LOGIN_TEMPLATE)
        user, is_student, is_teacher = _find_user_by_student(user_input)
        if not user:
            user, is_student, is_teacher = _find_user_by_teacher(user_input)
        if not user:
            user, is_student, is_teacher = _find_user_by_admin(user_input)
        if user and user.check_password(password):
            if _must_reset_password(user, is_student, is_teacher):
                request.session['reset_user_id'] = user.id
                clear_login_attempts(rate_limit_key)
                return redirect('reset_password')
            django_login(request, user)
            clear_login_attempts(rate_limit_key)
            messages.success(request, "You have successfully logged in.")
            return redirect('dashboard')
        else:
            increment_login_attempts(rate_limit_key)
            # Do not reveal if user exists
            messages.error(request, "Invalid credentials")
            return render(request, LOGIN_TEMPLATE)
    return render(request, LOGIN_TEMPLATE)

@csrf_protect
@require_http_methods(["GET", "POST"])
def reset_password(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('login')
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        password = request.POST.get('password', '')
        c_password = request.POST.get('c_password', '')
        if password != c_password:
            messages.error(request, "Passwords do not match")
            return render(request, RESET_PASSWORD_TEMPLATE)
        try:
            validate_password(password, user)
        except ValidationError as e:
            messages.error(request, " ".join(e.messages))
            return render(request, RESET_PASSWORD_TEMPLATE)
        user.set_password(password)
        user.save()
        if hasattr(user, 'student_profile'):
            user.student_profile.must_reset_password = False
            user.student_profile.save()
        if hasattr(user, 'teacher_profile'):
            user.teacher_profile.must_reset_password = False
            user.teacher_profile.save()
        messages.success(request, "Password reset successful. Please login.")
        del request.session['reset_user_id']
        return redirect('login')
    return render(request, "app/auth/reset_password.html")

@login_required(login_url='login')
def dashboard(request):
    user = request.user
    if user.is_superuser or user.is_staff:
        return redirect('dashboard_admin')
    elif hasattr(user, 'teacher_profile'):
        return redirect('dashboard_teacher')
    elif hasattr(user, 'student_profile'):
        return redirect('dashboard_student')
    else:
        return render(request, "app/dashboard/dashboard.html")

@login_required(login_url='login')
def dashboard_student(request):
    user = request.user
    # Only allow students
    if not hasattr(user, 'student_profile'):
        if user.is_superuser or user.is_staff:
            return redirect('dashboard_admin')
        elif hasattr(user, 'teacher_profile'):
            return redirect('dashboard_teacher')
        else:
            return redirect('dashboard')
    student_profile = user.student_profile
    attendance_percent = getattr(student_profile, 'attendance_percent', 0)
    announcements = []
    if student_profile.division:
        announcements = [a.text for a in getattr(student_profile.division, 'announcements', [])]
    return render(request, "app/dashboard/dashboard_student.html", {
        "attendance_percent": attendance_percent,
        "announcements": announcements,
    })

@login_required(login_url='login')
def dashboard_teacher(request):
    user = request.user
    # Only allow teachers
    if not hasattr(user, 'teacher_profile'):
        if user.is_superuser or user.is_staff:
            return redirect('dashboard_admin')
        elif hasattr(user, 'student_profile'):
            return redirect('dashboard_student')
        else:
            return redirect('dashboard')
    teacher_profile = user.teacher_profile
    teacher_divisions = Division.objects.filter(teacher=teacher_profile)
    pending_attendance = []
    return render(request, "app/dashboard/dashboard_teacher.html", {
        "teacher_divisions": teacher_divisions,
        "pending_attendance": pending_attendance,
    })

@login_required(login_url='login')
def dashboard_admin(request):
    user = request.user
    # Only allow admin/staff
    if not (user.is_superuser or user.is_staff):
        if hasattr(user, 'teacher_profile'):
            return redirect('dashboard_teacher')
        elif hasattr(user, 'student_profile'):
            return redirect('dashboard_student')
        else:
            return redirect('dashboard')
    total_students = StudentProfile.objects.count()
    total_teachers = TeacherProfile.objects.count()
    total_classes = Class.objects.count()
    recent_activity = []
    return render(request, "app/dashboard/dashboard_admin.html", {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_classes": total_classes,
        "recent_activity": recent_activity,
    })

@require_http_methods(["POST"])
@csrf_protect
@login_required(login_url='login')
def signout(request):
    django_logout(request)
    messages.success(request, "You are successfully logged out.")
    return redirect('index')

@csrf_protect
@require_http_methods(["GET", "POST"])
def forgot_password(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return render(request, "app/auth/forgot_password.html")
        user = User.objects.filter(email=email).first()
        # Always show the same message to prevent user enumeration
        messages.success(request, "If an account with that email exists, a password reset link has been sent.")
        if user:
            try:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = request.build_absolute_uri(
                    reverse('reset_password_confirm', kwargs={'uidb64': uid, 'token': token})
                )
                send_mail(
                    subject="ClassTrack Password Reset",
                    message=f"Hi {user.get_full_name()},\n\nClick the link below to reset your password:\n{reset_url}\n\nIf you did not request this, ignore this email.",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception:
                pass
        return redirect('login')
    return render(request, "app/auth/forgot_password.html")

@csrf_protect
@require_http_methods(["GET", "POST"])
def reset_password_confirm(request, uidb64, token):
    from django.utils.http import urlsafe_base64_decode
    from django.contrib.auth.tokens import default_token_generator

    def handle_password_reset(request, user):
        password = request.POST.get('password', '')
        c_password = request.POST.get('c_password', '')
        if password != c_password:
            messages.error(request, "Passwords do not match")
            return render(request, RESET_PASSWORD_CONFIRM_TEMPLATE)
        try:
            validate_password(password, user)
        except ValidationError as e:
            messages.error(request, " ".join(e.messages))
            return render(request, RESET_PASSWORD_CONFIRM_TEMPLATE)
        user.set_password(password)
        user.save()
        if hasattr(user, 'student_profile'):
            user.student_profile.must_reset_password = False
            user.student_profile.save()
        if hasattr(user, 'teacher_profile'):
            user.teacher_profile.must_reset_password = False
            user.teacher_profile.save()
        messages.success(request, "Password reset successful. Please login.")
        return redirect('login')

    user = None
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_object_or_404(User, pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        pass

    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, "The password reset link is invalid or has expired.")
        return redirect('forgot_password')

    if request.method == "POST":
        return handle_password_reset(request, user)
    return render(request, RESET_PASSWORD_CONFIRM_TEMPLATE)