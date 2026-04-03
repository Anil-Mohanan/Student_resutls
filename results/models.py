from django.template.defaultfilters import default
from enum import unique
from django.db import models
from django.utils import timezone

def generate_registration_number():
       current_year = timezone.now().year

       settings = InstituteSettings.objects.first()
       initials = settings.institute_initials if settings else 'IN'

       last_student = Student.objects.order_by('-id').first()

       if last_student and last_student.registration_number:
              try:
                     last_number = int(last_student.registration_number.split('/')[-2])
                     next_number = last_number + 1
              except:
                     next_number = 1
       else:
              next_number = 1

       return f"{initials}/{current_year}/{str(next_number).zfill(3)}"




class InstituteSettings(models.Model):
       institute_name = models.CharField(max_length = 100)
       institute_initials = models.CharField(max_length = 10)

       class Meta:
              verbose_name = 'Institute Settings'
       
       def __str__(self):
              return self.institute_name


class Student(models.Model):
       STATUS_CHOICES = [   
              ('pending','Pending'),
              ('approved','Approved')
       ]
       name = models.CharField(max_length = 100)
       registration_number = models.CharField(max_length = 30 , unique = True, blank = True,)
       roll_number = models.CharField(max_length = 20, unique=True)
       class_name = models.CharField(max_length = 20)
       status = models.CharField(max_length = 10, choices = STATUS_CHOICES, default = 'pending')
       joined_year = models.IntegerField(default= timezone.now().year)
       
       def __str__(self):
              return f"{self.registration_number} - {self.name}"

class Subject(models.Model):
       name = models.CharField(max_length = 100)

       def __str__(self):
              return self.name


class Result(models.Model):

       student = models.ForeignKey(Student, on_delete=models.CASCADE,related_name='results')
       subject = models.ForeignKey(Subject,on_delete=models.CASCADE)
       marks = models.IntegerField()
       total_marks = models.IntegerField(default=100)

       @property
       def is_pass(self):
              return self.marks >= (self.total_marks * 0.35)
       
       def __str__(self):
              return f"{self.student.name} - {self.subject.name} - {self.marks}"
