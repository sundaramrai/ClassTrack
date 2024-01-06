from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login,logout
# from user import settings
# from django.core.mail import send_mail

# Create your views here.
def index(request):
    return render(request,"app/index.html")

def signin(request):
    if request.method=="POST":
        username=request.POST['username']
        password=request.POST['password']

        user=authenticate(username=username,password=password)

        if user is not None:
            django_login(request,user)
            fname=user.first_name
            if username != username:
                messages.error(request,"Username doesn't exist")
                return redirect('signin')
            elif password != password:
                messages.error(request,"Password doesn't exist")
                return redirect('signin')
            else:
                return render(request, "app/index.html",{'fname':fname})
        else:
            messages.error(request,"Error Credentials")
            return redirect('index')

    return render(request,"app/login.html")

def register(request):
    if request.method=="POST":
        email=request.POST['email']
        username=request.POST['username']
        fname=request.POST['fname']
        lname=request.POST['lname']
        # mob=request.POST['mob']
        password=request.POST['password']
        c_password=request.POST['c_password']

        if User.objects.filter(username=username):
            messages.error(request,"Username already exist")
            return redirect('index')
        
        if User.objects.filter(email=email):
            messages.error(request,"Email already exist")
            return redirect('index')
        
        if len(username)>10:
            messages.error(request,"Username must be under 10 characters")

        if password != c_password:
            messages.error(request,"Password didn't match")

        myuser=User.objects.create_user(username,email,password)
        myuser.first_name=fname
        myuser.last_name=lname
        # myuser.email=email
        myuser.save()

        messages.success(request,'You have registered successfully')

        return redirect('signin')

    return render(request,"app/register.html")

def dashboard(request):
    return render(request,"app/dashboard.html")

def signout(request):
    # pass
    logout(request)
    messages.success(request,"Logged out successfully")
    return redirect('index')
