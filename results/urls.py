from django.urls import path
from . import views

urlpatterns = [
    # public
    path('', views.student_list, name='student_list'),
    path('result/<path:registration_number>/', views.student_result, name='student_result'),
    path('register/', views.student_register, name='student_register'),
    path('register/success/', views.register_success, name='register_success'),

    # dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/students/', views.manage_students, name='manage_students'),
    path('dashboard/students/add/', views.add_student, name='add_student'),
    path('dashboard/pending/', views.pending_students, name='pending_students'),
    path('dashboard/approve/<int:student_id>/', views.approve_student, name='approve_student'),
    path('dashboard/reject/<int:student_id>/', views.reject_student, name='reject_student'),
    path('dashboard/subjects/', views.manage_subjects, name='manage_subjects'),
    path('dashboard/subjects/add/', views.add_subject, name='add_subject'),
    path('dashboard/results/add/', views.add_result, name='add_result'),
    path('dashboard/results/delete/<int:result_id>/', views.delete_result, name='delete_result'),
    path('dashboard/settings/', views.institute_settings, name='institute_settings'),
    path('dashboard/student/<path:registration_number>/', views.student_result_admin, name='student_result_admin'),

    # login logout
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]