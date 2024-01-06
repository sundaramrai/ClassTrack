from django.contrib import admin
from django.urls import path
import include
from . import views

urlpatterns = [
    path('',views.index,name='index'),
    path('signin',views.signin,name='signin'),
    path('register',views.register,name='register'),
    path('dashboard',views.dashboard,name='dashboard'),
    path('signout',views.signout,name='signout'),

]
