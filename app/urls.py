from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login, name='login'),
    path('contact', views.contact, name='contact'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('dashboard/student', views.dashboard_student, name='dashboard_student'),
    path('dashboard/teacher', views.dashboard_teacher, name='dashboard_teacher'),
    path('dashboard/admin', views.dashboard_admin, name='dashboard_admin'),
    path('signout', views.signout, name='signout'),
    path('reset_password/', views.reset_password, name='reset_password'),
    path('forgot_password', views.forgot_password, name='forgot_password'),
    path('reset/<uidb64>/<token>/', views.reset_password_confirm, name='reset_password_confirm'),

]
