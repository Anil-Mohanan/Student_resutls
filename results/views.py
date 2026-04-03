from results.models import InstituteSettings
from results.models import generate_registration_number
from django.contrib.admin.utils import model_format_dict
from contextlib import redirect_stderr
from django.http import request
from django.contrib.messages import error
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import Student, Subject, Result
from django.db import models

def student_list(request):
       students = Student.objects.filter( status = 'approved')
       classes = Student.objects.values_list('class_name',flat = True).distinct().order_by('class_name')

       selected_class = request.GET.get('class','')
       search = request.GET.get('search','')

       if selected_class:
              students = students.filter(class_name = selected_class)
       
       if search:
              students = students.filter(
                     models.Q(name__icontains = search) | models.Q(roll_number__icontains=search)
              )
       
       return render(request, 'results/student_list.html',{
              'students': students,
              'classes': classes,
              'selected_class' : selected_class,
              'search': search,
       })

def student_result(request, registration_number):
       student = get_object_or_404(Student, registration_number=registration_number)
       results = student.results.all()

       return render(request,'results/student_result.html',{
              'student': student,
              'results': results,
       }) 

def student_register(request):
    error = None
    if request.method == 'POST':
        name = request.POST['name'].strip()
        if not name:
            error = 'Name is required'
        else:
            reg_number = generate_registration_number()
            Student.objects.create(
                name=name,
                registration_number=reg_number,
                status='pending'
            )
            return redirect('register_success')
    return render(request, 'results/register.html', {'error': error})

def register_success(request):
       return render(request,'results/register_success.html')


# ------------ LOGIN / LOGOUT --------------- #

def login_view(request):
       error = None
       if request.method == "POST":
              username = request.POST['username']
              password = request.POST['password']
              user = authenticate(request,username = username, password = password)

              if user is not None:
                     login(request,user)
                     return redirect('dashboard')
              else:
                     error = "Invalid username or password"
       return render(request,'results/login.html',{'error':error})

def logout_view(request):
       logout(request)
       return redirect('login')

# ---------------- DASHBOARD ---------------- #

@login_required(login_url = 'login')
def dashboard(request):
       total_students = Student.objects.count()
       total_subjects = Subject.objects.count()
       total_results = Result.objects.count()
       pending_count = Student.objects.filter(status = 'pending').count()


       return render(request,'results/dashboard.html',{
              'total_students': total_students,
              'total_subjects': total_subjects,
              'total_results': total_results,
              'pending_count': pending_count,
       })

# ------------ STUDENTS ---------- #

@login_required(login_url = 'login')
def manage_students(request):
       students = Student.objects.all()
       return render(request,'results/manage_students.html',{'students':students})

@login_required(login_url = 'login')
def add_student(request):
       error = None
       if request.method == 'POST':
              name = request.POST['name']
              roll_number = request.POST['roll_number']
              class_name = request.POST['class_name']
              reg_number = generate_registration_number()
              Student.objects.create(
                     name=name,
                     roll_number=roll_number,
                     class_name=class_name,
                     registration_number=reg_number,
                     status='approved',
              )
              return redirect('manage_students')
       return render(request,'results/add_student.html', {'error': error})

# --------- PENDING -------------

@login_required(login_url = 'login')
def pending_students(request):
       students = Student.objects.filter(status='pending').order_by('id')
       return render(request,'results/pending_students.html', {'students': students})

@login_required(login_url='login')
def approve_student(request,student_id):
       student = get_object_or_404(Student,id = student_id)
       if request.method == 'POST':
              roll_number = request.POST['roll_number']
              class_name = request.POST['class_name']
              student.roll_number = roll_number
              student.class_name = class_name
              student.status = 'approved'
              student.save()
              return redirect('pending_students')
       return render(request, 'results/approve_student.html',{'student':student})

@login_required(login_url='login')
def reject_student(request,student_id):
       student = get_object_or_404(Student,id = student_id)
       student.delete()
       return redirect('pending_students')


# ----------- SUBJECTS ------------

@login_required(login_url='login')
def manage_subjects(request):
       subjects = Subject.objects.all()
       return render(request,'results/manage_subjects.html',{'subjects': subjects})

@login_required(login_url = 'login')
def add_subject(request):
       if request.method == 'POST':
              name = request.POST['name']
              Subject.objects.create(name=name)
              return redirect('manage_subjects')
       return render(request,'results/add_subject.html')


# ------------ RESULTS ----------- #

@login_required(login_url='login')
def add_result(request):
       students = Student.objects.all()
       subjects = Subject.objects.all()
       error = None
       if request.method == 'POST':
              student_id = request.POST['student']
              subject_id = request.POST['subject']
              marks = request.POST['marks']
              total_marks = request.POST['total_marks']
              student = get_object_or_404(Student,id = student_id)
              subject = get_object_or_404(Subject, id = subject_id)
              if Result.objects.filter(student = student, subject = subject).exists():
                     error = 'Result for this subject already exists'
              else: 
                     Result.objects.create(student = student, subject = subject , marks = marks, total_marks= total_marks)
                     return redirect('dashboard')
       return render(request,'results/add_result.html',{
              'students': students,
              'subjects': subjects,
              'error': error
       })


@login_required(login_url = 'login')
def delete_result(request,result_id):
       result = get_object_or_404(Result,id = result_id)
       result.delete()
       return redirect('dashboard')


# ---------- SETTINGS ---------- #

@login_required(login_url = 'login')
def institute_settings(request):
       settings = InstituteSettings.objects.first()
       error = None
       success = None
       if request.method == "POST":
              institute_name = request.POST['institute_name']
              institute_initials = request.POST['institute_initials'].upper().strip()
              if settings:
                     settings.institute_name =  institute_name
                     settings.institute_initials = institute_initials
                     settings.save()
              else:
                     InstituteSettings.objects.create(
                            institute_name=institute_name,
                            institute_initials=institute_initials
                     )
              success = 'Settings saved successfully'
              settings = InstituteSettings.objects.first()
       return render(request, 'results/institute_settings.html',{
              'settings': settings,
              'error': error,
              'success': success,
       })
