from django.contrib import admin
from .models import SchoolClass, Student, AttendanceSession, AttendanceRecord
admin.site.register(SchoolClass)
admin.site.register(Student)
admin.site.register(AttendanceSession)
admin.site.register(AttendanceRecord)
