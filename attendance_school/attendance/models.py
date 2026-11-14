from django.db import models
from django.utils import timezone

MAJORS = [
    ("شبکه", "شبکه"), ("تاسیسات", "تاسیسات"), ("چوب", "چوب"),
    ("مکانیک", "مکانیک"), ("الکترونیک", "الکترونیک"),
    ("الکتروتکنیک", "الکتروتکنیک"), ("ماشین ابزار", "ماشین ابزار"),
    ("مکاترونیک", "مکاترونیک"), ("ساختمان", "ساختمان"),
]
GRADES = [(10, "دهم"), (11, "یازدهم"), (12, "دوازدهم")]

class SchoolClass(models.Model):
    major = models.CharField(max_length=40, choices=MAJORS)
    grade = models.PositiveSmallIntegerField(choices=GRADES)
    section = models.CharField(max_length=20, blank=True, default="")
    class Meta:
        ordering = ["grade", "major", "section"]
        constraints = [models.UniqueConstraint(fields=["major", "grade", "section"], name="unique_school_class")]
    def __str__(self):
        grade_name = dict(GRADES).get(self.grade, self.grade)
        return f"{self.major} - {grade_name}" + (f" ({self.section})" if self.section else "")

class Student(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="students")
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=100)
    file_number = models.CharField(max_length=40, blank=True)
    active = models.BooleanField(default=True)
    class Meta:
        ordering = ["last_name", "first_name"]
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class AttendanceSession(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="sessions")
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["school_class", "date"], name="unique_class_attendance_date")]
        ordering = ["-date"]

class AttendanceRecord(models.Model):
    STATUS = [("present", "حاضر"), ("absent", "غایب"), ("late", "تأخیر")]
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="records")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_records")
    status = models.CharField(max_length=10, choices=STATUS, default="present")
    note = models.CharField(max_length=250, blank=True)
    justified = models.BooleanField(default=False)
    justification_reason = models.CharField(max_length=250, blank=True)
    justified_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["session", "student"], name="unique_student_per_session")]
