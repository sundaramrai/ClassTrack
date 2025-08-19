from django.contrib import admin
from .models import Class, TeacherProfile, Division, StudentProfile, Subject
# Register your models here.

admin.site.register(Class)
admin.site.register(TeacherProfile)
admin.site.register(Division)
admin.site.register(StudentProfile)
admin.site.register(Subject)