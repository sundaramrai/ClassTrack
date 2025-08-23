from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from app.models import StudentProfile, TeacherProfile, Class, Division
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

# Create your views here.
def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, "app/index.html")

def contact(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, "app/contact/contact.html")

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

def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == "POST":
        user_input = request.POST.get('user')
        password = request.POST.get('password')
        user, is_student, is_teacher = _find_user_by_student(user_input)
        if not user:
            user, is_student, is_teacher = _find_user_by_teacher(user_input)
        if not user:
            user, is_student, is_teacher = _find_user_by_admin(user_input)

        if user and user.check_password(password):
            if _must_reset_password(user, is_student, is_teacher):
                request.session['reset_user_id'] = user.id
                return redirect('reset_password')
            django_login(request, user)
            messages.success(request, "You have successfully logged in.")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials")
            return render(request, "app/auth/login.html")
    return render(request, "app/auth/login.html")

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def reset_password(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    if request.method == "POST":
        password = request.POST.get('password')
        c_password = request.POST.get('c_password')
        if password != c_password:
            messages.error(request, "Passwords do not match")
            return render(request, "app/auth/reset_password.html")
        user.set_password(password)
        user.save()
        # Set must_reset_password = False
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
    if not hasattr(user, 'student_profile'):
        return redirect('dashboard')
    student_profile = user.student_profile
    # Example: Calculate attendance percent (replace with your real logic)
    attendance_percent = getattr(student_profile, 'attendance_percent', 0)
    # Example: Get announcements for student's division (replace with your real logic)
    announcements = []
    if student_profile.division:
        # Suppose you have an Announcement model related to Division
        # announcements = Announcement.objects.filter(division=student_profile.division).values_list('text', flat=True)
        announcements = [a.text for a in getattr(student_profile.division, 'announcements', [])]
    return render(request, "app/dashboard/dashboard_student.html", {
        "attendance_percent": attendance_percent,
        "announcements": announcements,
    })

@login_required(login_url='login')
def dashboard_teacher(request):
    user = request.user
    if not hasattr(user, 'teacher_profile'):
        return redirect('dashboard')
    teacher_profile = user.teacher_profile
    teacher_divisions = Division.objects.filter(teacher=teacher_profile)
    # Example: Get pending attendance (replace with your real logic)
    pending_attendance = []
    # If you have an Attendance model, you can filter for pending records
    # pending_attendance = Attendance.objects.filter(division__in=teacher_divisions, status='pending')
    return render(request, "app/dashboard/dashboard_teacher.html", {
        "teacher_divisions": teacher_divisions,
        "pending_attendance": pending_attendance,
    })

@login_required(login_url='login')
def dashboard_admin(request):
    user = request.user
    if not (user.is_superuser or user.is_staff):
        return redirect('dashboard')
    total_students = StudentProfile.objects.count()
    total_teachers = TeacherProfile.objects.count()
    total_classes = Class.objects.count()
    # Example: Get recent activity (replace with your real logic)
    recent_activity = []
    # If you have an ActivityLog model, you can fetch recent logs
    # recent_activity = ActivityLog.objects.order_by('-timestamp')[:10]
    return render(request, "app/dashboard/dashboard_admin.html", {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_classes": total_classes,
        "recent_activity": recent_activity,
    })

def signout(request):
    django_logout(request)
    messages.success(request, "You are successfully logged out.")
    return redirect('index')

def forgot_password(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == "POST":
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
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
                    from_email=None,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                messages.success(request, "A password reset link has been sent to your email.")
                return redirect('login')
            except Exception as e:
                messages.error(request, f"Error sending password reset email: {e}")
        else:
            messages.error(request, "No user found with that email address.")
    return render(request, "app/auth/forgot_password.html")

def reset_password_confirm(request, uidb64, token):
    from django.utils.http import urlsafe_base64_decode
    from django.contrib.auth.tokens import default_token_generator
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password = request.POST.get('password')
            c_password = request.POST.get('c_password')
            if password != c_password:
                messages.error(request, "Passwords do not match")
                return render(request, "app/auth/reset_password_confirm.html")
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
        return render(request, "app/auth/reset_password_confirm.html")
    else:
        messages.error(request, "The password reset link is invalid or has expired.")
        return redirect('forgot_password')