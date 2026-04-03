from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db import models
from .models import Student, Subject, Result, InstituteSettings, Exam, generate_registration_number
import json


# ---------- PUBLIC VIEWS ----------

def student_list(request):
    students = Student.objects.filter(status='approved')
    classes = Student.objects.filter(
        status='approved'
    ).values_list('class_name', flat=True).distinct().order_by('class_name')

    selected_class = request.GET.get('class', '')
    search = request.GET.get('search', '')

    if selected_class:
        students = students.filter(class_name=selected_class)

    if search:
        students = students.filter(
            models.Q(name__icontains=search) |
            models.Q(registration_number__icontains=search)
        )

    return render(request, 'results/student_list.html', {
        'students': students,
        'classes': classes,
        'selected_class': selected_class,
        'search': search,
    })


def student_result(request, registration_number):
    student = get_object_or_404(
        Student,
        registration_number=registration_number,
        status='approved'
    )
    exams = Exam.objects.filter(class_name=student.class_name)
    selected_exam_id = request.GET.get('exam_id', '')
    selected_exam = None
    results = []

    if selected_exam_id:
        selected_exam = get_object_or_404(Exam, id=selected_exam_id)
        results = Result.objects.filter(
            student=student,
            exam=selected_exam
        ).select_related('subject')
    elif exams.exists():
        selected_exam = exams.last()
        results = Result.objects.filter(
            student=student,
            exam=selected_exam
        ).select_related('subject')

    # chart data - improvement over exams per subject
    subjects = Subject.objects.filter(class_name=student.class_name)
    chart_data = {}

    for subject in subjects:
        subject_results = Result.objects.filter(
            student=student,
            subject=subject
        ).select_related('exam').order_by('exam__date')

        if subject_results.exists():
            chart_data[subject.name] = {
                'exams': [r.exam.name for r in subject_results],
                'percentages': [r.percentage for r in subject_results]
            }

    return render(request, 'results/student_result.html', {
        'student': student,
        'exams': exams,
        'selected_exam': selected_exam,
        'results': results,
        'chart_data': json.dumps(chart_data),
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
    return render(request, 'results/register_success.html')


# ---------- LOGIN / LOGOUT ----------

def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            error = 'Invalid username or password'
    return render(request, 'results/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


# ---------- DASHBOARD ----------

@login_required(login_url='login')
def dashboard(request):
    total_students = Student.objects.filter(status='approved').count()
    total_subjects = Subject.objects.count()
    total_results = Result.objects.count()
    total_exams = Exam.objects.count()
    pending_count = Student.objects.filter(status='pending').count()
    return render(request, 'results/dashboard.html', {
        'total_students': total_students,
        'total_subjects': total_subjects,
        'total_results': total_results,
        'total_exams': total_exams,
        'pending_count': pending_count,
    })


# ---------- STUDENTS ----------

@login_required(login_url='login')
def manage_students(request):
    students = Student.objects.filter(status='approved')
    return render(request, 'results/manage_students.html', {'students': students})


@login_required(login_url='login')
def add_student(request):
    error = None
    if request.method == 'POST':
        name = request.POST['name']
        class_name = request.POST['class_name']
        roll_number = request.POST['roll_number']
        reg_number = generate_registration_number()
        Student.objects.create(
            name=name,
            registration_number=reg_number,
            roll_number=roll_number,
            class_name=class_name,
            status='approved'
        )
        return redirect('manage_students')
    return render(request, 'results/add_student.html', {'error': error})


# ---------- PENDING ----------

@login_required(login_url='login')
def pending_students(request):
    students = Student.objects.filter(status='pending').order_by('-registered_at')
    return render(request, 'results/pending_students.html', {'students': students})


@login_required(login_url='login')
def approve_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        roll_number = request.POST['roll_number']
        class_name = request.POST['class_name']
        student.roll_number = roll_number
        student.class_name = class_name
        student.status = 'approved'
        student.save()
        return redirect('pending_students')
    return render(request, 'results/approve_student.html', {'student': student})


@login_required(login_url='login')
def reject_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    student.delete()
    return redirect('pending_students')


# ---------- SUBJECTS ----------

@login_required(login_url='login')
def manage_subjects(request):
    classes = Student.objects.filter(
        status='approved'
    ).values_list('class_name', flat=True).distinct().order_by('class_name')

    subjects_by_class = {}
    for class_name in classes:
        subjects_by_class[class_name] = Subject.objects.filter(class_name=class_name)

    return render(request, 'results/manage_subjects.html', {
        'subjects_by_class': subjects_by_class,
    })


@login_required(login_url='login')
def add_subject(request):
    classes = Student.objects.filter(
        status='approved'
    ).values_list('class_name', flat=True).distinct().order_by('class_name')
    error = None

    if request.method == 'POST':
        name = request.POST['name'].strip()
        class_name = request.POST['class_name'].strip()
        if Subject.objects.filter(name=name, class_name=class_name).exists():
            error = f'"{name}" already exists for class {class_name}'
        else:
            Subject.objects.create(name=name, class_name=class_name)
            return redirect('manage_subjects')

    return render(request, 'results/add_subjects.html', {
        'classes': classes,
        'error': error
    })


# ---------- EXAMS ----------

@login_required(login_url='login')
def manage_exams(request):
    classes = Student.objects.filter(
        status='approved'
    ).values_list('class_name', flat=True).distinct().order_by('class_name')

    exams_by_class = {}
    for class_name in classes:
        exams_by_class[class_name] = Exam.objects.filter(class_name=class_name)

    return render(request, 'results/manage_exams.html', {
        'exams_by_class': exams_by_class,
    })


@login_required(login_url='login')
def add_exam(request):
    classes = Student.objects.filter(
        status='approved'
    ).values_list('class_name', flat=True).distinct().order_by('class_name')
    error = None

    if request.method == 'POST':
        name = request.POST['name'].strip()
        class_name = request.POST['class_name'].strip()
        date = request.POST['date']
        if Exam.objects.filter(name=name, class_name=class_name).exists():
            error = f'"{name}" already exists for class {class_name}'
        else:
            Exam.objects.create(name=name, class_name=class_name, date=date)
            return redirect('manage_exams')

    return render(request, 'results/add_exam.html', {
        'classes': classes,
        'error': error
    })


# ---------- RESULTS ----------

@login_required(login_url='login')
def add_result(request):
    students = Student.objects.filter(status='approved')
    error = None
    preselected_student_id = request.GET.get('student_id', '')

    subjects = []
    if preselected_student_id:
        try:
            preselected_student = Student.objects.get(id=preselected_student_id)
            subjects = Subject.objects.filter(class_name=preselected_student.class_name)
        except Student.DoesNotExist:
            subjects = Subject.objects.all()
    else:
        subjects = Subject.objects.all()

    exams = Exam.objects.all()

    if request.method == 'POST':
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        exam_id = request.POST.get('exam')
        marks = request.POST.get('marks')
        total_marks = request.POST.get('total_marks')

        if not all([student_id, subject_id, exam_id, marks, total_marks]):
            error = 'All fields are required'
        else:
            student = get_object_or_404(Student, id=student_id)
            subject = get_object_or_404(Subject, id=subject_id)
            exam = get_object_or_404(Exam, id=exam_id)
            
            if Result.objects.filter(student=student, subject=subject, exam=exam).exists():
                error = 'Result for this subject in this exam already exists'
            else:
                Result.objects.create(
                    student=student,
                    subject=subject,
                    exam=exam,
                    marks=marks,
                    total_marks=total_marks
                )
                return redirect('student_result_admin',
                              registration_number=student.registration_number)

    return render(request, 'results/add_result.html', {
        'students': students,
        'subjects': subjects,
        'exams': exams,
        'error': error,
        'preselected_student_id': preselected_student_id,
    })


@login_required(login_url='login')
def bulk_add_results(request):
    classes = Student.objects.filter(
        status='approved'
    ).values_list('class_name', flat=True).distinct().order_by('class_name')

    selected_class = request.GET.get('class_name', '')
    selected_subject_id = request.GET.get('subject_id', '')
    selected_exam_id = request.GET.get('exam_id', '')

    subjects = Subject.objects.filter(class_name=selected_class) if selected_class else []
    exams = Exam.objects.filter(class_name=selected_class) if selected_class else []

    students = []
    selected_subject = None
    selected_exam = None
    existing_results = {}

    if selected_class and selected_subject_id and selected_exam_id:
        students = Student.objects.filter(
            class_name=selected_class,
            status='approved'
        ).order_by('roll_number')
        selected_subject = get_object_or_404(Subject, id=selected_subject_id)
        selected_exam = get_object_or_404(Exam, id=selected_exam_id)

        for student in students:
            result = Result.objects.filter(
                student=student,
                subject=selected_subject,
                exam=selected_exam
            ).first()
            if result:
                existing_results[student.id] = result.marks

    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        exam_id = request.POST.get('exam_id')
        total_marks = request.POST.get('total_marks', 100)
        class_name = request.POST.get('class_name')
        subject = get_object_or_404(Subject, id=subject_id)
        exam = get_object_or_404(Exam, id=exam_id)
        student_ids = request.POST.getlist('student_ids')

        saved = 0
        for student_id in student_ids:
            marks = request.POST.get(f'marks_{student_id}', '').strip()
            if marks == '':
                continue
            student = get_object_or_404(Student, id=student_id)
            result = Result.objects.filter(
                student=student,
                subject=subject,
                exam=exam
            ).first()
            if result:
                result.marks = marks
                result.total_marks = total_marks
                result.save()
            else:
                Result.objects.create(
                    student=student,
                    subject=subject,
                    exam=exam,
                    marks=marks,
                    total_marks=total_marks
                )
            saved += 1

        return redirect(
            f'/dashboard/results/bulk/?class_name={class_name}&subject_id={subject_id}&exam_id={exam_id}&saved={saved}'
        )

    saved = request.GET.get('saved', '')

    return render(request, 'results/bulk_add_results.html', {
        'classes': classes,
        'subjects': subjects,
        'exams': exams,
        'students': students,
        'selected_class': selected_class,
        'selected_subject_id': selected_subject_id,
        'selected_exam_id': selected_exam_id,
        'selected_subject': selected_subject,
        'selected_exam': selected_exam,
        'existing_results': existing_results,
        'saved': saved,
    })


@login_required(login_url='login')
def delete_result(request, result_id):
    result = get_object_or_404(Result, id=result_id)
    student = result.student
    result.delete()
    return redirect('student_result_admin',
                   registration_number=student.registration_number)


@login_required(login_url='login')
def student_result_admin(request, registration_number):
    student = get_object_or_404(Student, registration_number=registration_number)
    exams = Exam.objects.filter(class_name=student.class_name)
    selected_exam_id = request.GET.get('exam_id', '')
    selected_exam = None
    results = []

    if selected_exam_id:
        selected_exam = get_object_or_404(Exam, id=selected_exam_id)
        results = Result.objects.filter(
            student=student,
            exam=selected_exam
        ).select_related('subject')
    elif exams.exists():
        selected_exam = exams.last()
        results = Result.objects.filter(
            student=student,
            exam=selected_exam
        ).select_related('subject')

    return render(request, 'results/student_result_admin.html', {
        'student': student,
        'exams': exams,
        'selected_exam': selected_exam,
        'results': results,
    })


# ---------- SETTINGS ----------

@login_required(login_url='login')
def institute_settings(request):
    settings = InstituteSettings.objects.first()
    success = None
    if request.method == 'POST':
        institute_name = request.POST['institute_name']
        institute_initials = request.POST['institute_initials'].upper().strip()
        if settings:
            settings.institute_name = institute_name
            settings.institute_initials = institute_initials
            settings.save()
        else:
            InstituteSettings.objects.create(
                institute_name=institute_name,
                institute_initials=institute_initials
            )
        success = 'Settings saved successfully'
        settings = InstituteSettings.objects.first()
    return render(request, 'results/institute_settings.html', {
        'settings': settings,
        'success': success,
    })