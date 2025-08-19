from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from app.models import StudentProfile, TeacherProfile
from django.contrib.auth.hashers import check_password

# Create your views here.
def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request,"app/index.html")

def contact(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request,"app/contact.html")

def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == "POST":
        user_input = request.POST.get('user')
        password = request.POST.get('password')
        user = None
        is_student = False
        is_teacher = False

        # Try to find user by student_id or email (student)
        try:
            student_profile = StudentProfile.objects.get(student_id=user_input)
            user = student_profile.user
            is_student = True
        except StudentProfile.DoesNotExist:
            try:
                student_profile = StudentProfile.objects.get(user__email=user_input)
                user = student_profile.user
                is_student = True
            except StudentProfile.DoesNotExist:
                pass

        # Try to find user by teacher_id or email (teacher)
        if not user:
            try:
                teacher_profile = TeacherProfile.objects.get(employee_id=user_input)
                user = teacher_profile.user
                is_teacher = True
            except TeacherProfile.DoesNotExist:
                try:
                    teacher_profile = TeacherProfile.objects.get(user__email=user_input)
                    user = teacher_profile.user
                    is_teacher = True
                except TeacherProfile.DoesNotExist:
                    pass

        # Fallback: Try username or email (for admin or others)
        if not user:
            try:
                user = User.objects.get(email=user_input)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(username=user_input)
                except User.DoesNotExist:
                    user = None

        if user and user.check_password(password):
            # Only check must_reset_password for students and teachers
            must_reset = False
            if is_student and hasattr(user, 'student_profile') and getattr(user.student_profile, 'must_reset_password', False):
                must_reset = True
            if is_teacher and hasattr(user, 'teacher_profile') and getattr(user.teacher_profile, 'must_reset_password', False):
                must_reset = True
            if must_reset:
                request.session['reset_user_id'] = user.id
                return redirect('reset_password')
            django_login(request, user)
            messages.success(request, "You have successfully logged in.")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials")
            return render(request, "app/login.html")
    return render(request, "app/login.html")

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
            return render(request, "app/reset_password.html")
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
    return render(request, "app/reset_password.html")

@login_required(login_url='login')
def dashboard(request):
    user_cards = [
        {
            "img": "https://images.unsplash.com/photo-1531891437562-4301cf35b7e4?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxzZWFyY2h8NDV8fHByb2ZpbGV8ZW58MHx8MHx8&auto=format&fit=crop&w=500&q=60g",
            "name": "Neil Wilson",
            "department": "COMP",
            "percent": 85,
        },
        {
            "img": "https://images.unsplash.com/photo-1543132220-3ec99c6094dc?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxzZWFyY2h8NDl8fHByb2ZpbGV8ZW58MHwxfDB8fA%3D%3D&auto=format&fit=crop&w=500&q=60",
            "name": "Finn Taylor",
            "department": "IT",
            "percent": 82,
        },
        {
            "img": "https://images.unsplash.com/photo-1598198414976-ddb788ec80c1?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxzZWFyY2h8NzV8fHByb2ZpbGV8ZW58MHwxfDB8fA%3D%3D&auto=format&fit=crop&w=500&q=60",
            "name": "Nick Johnson",
            "department": "EXTC",
            "percent": 94,
        },
        {
            "img": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxzZWFyY2h8MTB8fHByb2ZpbGV8ZW58MHwxfDB8fA%3D%3D&auto=format&fit=crop&w=500&q=60",
            "name": "Sarah Mayer",
            "department": "AI&DS",
            "percent": 85,
        },
        {
            "img": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxzZWFyY2h8MzN8fHByb2ZpbGV8ZW58MHwxfDB8fA%3D%3D&auto=format&fit=crop&w=500&q=60",
            "name": "Zayn Shaw",
            "department": "AI&ML",
            "percent": 82,
        },
        {
            "img": "https://images.unsplash.com/photo-1544723795-3fb6469f5b39?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxzZWFyY2h8NDR8fHByb2ZpbGV8ZW58MHwxfDB8fA%3D%3D&auto=format&fit=crop&w=500&q=60",
            "name": "Moses Kaul",
            "department": "COMP",
            "percent": 93,
        },
    ]
    attendance_list = [
        {
            "id": "102684",
            "name": "Neil Wilson",
            "department": "COMP",
            "date": "03-24-22",
            "year": "SE",
            "division": "B"
        },
        {
            "id": "102168",
            "name": "Finn Taylor",
            "department": "IT",
            "date": "03-24-22",
            "year": "SE",
            "division": "A"
        },
        {
            "id": "103428",
            "name": "Nick Johnson",
            "department": "EXTC",
            "date": "03-24-22",
            "year": "TE",
            "division": "C"
        },
        {
            "id": "101224",
            "name": "Sarah Mayer",
            "department": "AI&DS",
            "date": "03-24-22",
            "year": "FE",
            "division": "B"
        },
        {
            "id": "102554",
            "name": "Zayn Shaw",
            "department": "AI&ML",
            "date": "03-24-22",
            "year": "SE",
            "division": "C"
        },
        {
            "id": "104763",
            "name": "Moses Kaul",
            "department": "COMP",
            "date": "03-24-22",
            "year": "BE",
            "division": "A"
        },
    ]
    return render(request, "app/dashboard.html", {
        "user_cards": user_cards,
        "attendance_list": attendance_list,
    })

def signout(request):
    django_logout(request)
    messages.success(request, "You are successfully logged out.")
    return redirect('index')

# def register(request):
#     if request.user.is_authenticated:
#         return redirect('dashboard')
#     if request.method == "POST":
#         email = request.POST['email']
#         fname = request.POST['fname']
#         lname = request.POST['lname']
#         password = request.POST['password']
#         c_password = request.POST['c_password']

#         has_error = False
#         if User.objects.filter(email=email).exists():
#             messages.error(request, "Email already exists")
#             has_error = True
#         if len(email) > 10:
#             messages.error(request, "Email must be under 10 characters")
#             has_error = True
#         if password != c_password:
#             messages.error(request, "Passwords do not match")
#             has_error = True

#         if has_error:
#             return render(request, "app/register.html")

#         myuser = User.objects.create_user(email=email, password=password)
#         myuser.first_name = fname
#         myuser.last_name = lname
#         myuser.save()

#         messages.success(request, 'You have registered successfully. Please login.')

#         return redirect('login')

#     return render(request, "app/register.html")
