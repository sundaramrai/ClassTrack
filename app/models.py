from django.db import models
from django.contrib.auth.models import User

class Class(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Class {self.name}>"

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=20, unique=True, db_index=True)
    qualification = models.CharField(max_length=255)
    specialization = models.CharField(max_length=255)
    experience_years = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    must_reset_password = models.BooleanField(default=True)

    class Meta:
        ordering = ['employee_id']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"

    def __repr__(self):
        return f"<TeacherProfile {self.employee_id}>"

class Division(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    class_field = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='divisions')
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, related_name='divisions')
    max_students = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'class_field')
        ordering = ['class_field', 'name']

    def __str__(self):
        return f"{self.class_field.name} {self.name}"

    def __repr__(self):
        return f"<Division {self.class_field.name} {self.name}>"

class StudentProfile(models.Model):
    class Category(models.TextChoices):
        SCIENCE_BOARD = 'Science-Board'
        SCIENCE_JEE = 'Science-JEE'
        SCIENCE_NEET = 'Science-NEET'
        COMMERCE_BOARD = 'Commerce-Board'
        COMMERCE_CA = 'Commerce-CA'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=30, unique=True, db_index=True)
    date_of_birth = models.DateField()
    guardian_name = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=20)
    address = models.TextField()
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, related_name='students')
    category = models.CharField(max_length=50, choices=Category.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    must_reset_password = models.BooleanField(default=True)

    class Meta:
        ordering = ['student_id']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"

    def __repr__(self):
        return f"<StudentProfile {self.student_id}>"

class Subject(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    code = models.CharField(max_length=30, unique=True, db_index=True)
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='subjects')
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, related_name='subjects')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.name} ({self.code})"

    def __repr__(self):
        return f"<Subject {self.code}>"
