import sqlite3
from datetime import date, datetime
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.db import transaction, IntegrityError
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.conf import settings
import jdatetime
from .models import SchoolClass, Student, AttendanceSession, AttendanceRecord, MAJORS, GRADES


def today_jalali():
    return jdatetime.date.fromgregorian(date=date.today()).strftime("%Y/%m/%d")


def parse_jalali(value):
    try:
        value = value.translate(
            str.maketrans(
                "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
                "01234567890123456789"
            )
        )
        y, m, d = [int(x) for x in value.replace("-", "/").split("/")]
        return jdatetime.date(y, m, d).togregorian()
    except Exception:
        return date.today()


def jalali(d):
    return jdatetime.date.fromgregorian(date=d).strftime("%Y/%m/%d")


class LoginView(DjangoLoginView):
    template_name = "login.html"


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    today = date.today()
    sessions = AttendanceSession.objects.filter(
        date=today).select_related("school_class")
    total_classes = SchoolClass.objects.count()
    recorded = sessions.count()
    records = AttendanceRecord.objects.filter(session__date=today)
    counts = {key: records.filter(status=key).count()
              for key in ["present", "absent", "late"]}
    context = {
        "today": today_jalali(), "total_classes": total_classes, "recorded": recorded,
        "pending": max(total_classes-recorded, 0), "counts": counts,
        "classes": SchoolClass.objects.all(),
        "recent_sessions": sessions.order_by("school_class__grade", "school_class__major"),
        "students_total": Student.objects.filter(active=True).count(),
    }
    return render(request, "dashboard.html", context)


@login_required
def classes(request):
    if request.method == "POST":
        major = request.POST.get("major", "")
        grade = request.POST.get("grade", "")
        section = request.POST.get("section", "").strip()
        if major not in dict(MAJORS) or not grade.isdigit() or int(grade) not in dict(GRADES):
            messages.error(request, "رشته یا پایه معتبر نیست.")
        else:
            obj, created = SchoolClass.objects.get_or_create(
                major=major, grade=int(grade), section=section)
            messages.success(
                request, "کلاس ایجاد شد." if created else "این کلاس از قبل وجود دارد.")
        return redirect("classes")
    return render(request, "classes.html", {"classes": SchoolClass.objects.annotate(student_count=Count("students")), "majors": MAJORS, "grades": GRADES})


@login_required
def edit_class(request, class_id):
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    if request.method == "POST":
        major = request.POST.get("major", "")
        grade = request.POST.get("grade", "")
        section = request.POST.get("section", "").strip()
        if major not in dict(MAJORS) or not grade.isdigit() or int(grade) not in dict(GRADES):
            messages.error(request, "رشته یا پایه معتبر نیست.")
        else:
            school_class.major, school_class.grade, school_class.section = major, int(
                grade), section
            try:
                school_class.save()
                messages.success(
                    request, "مشخصات کلاس ویرایش شد. سوابق حضور و غیاب آن حفظ شده‌اند.")
                return redirect("classes")
            except IntegrityError:
                messages.error(
                    request, "کلاسی با همین رشته، پایه و بخش از قبل وجود دارد.")
    return render(request, "edit_class.html", {"school_class": school_class, "majors": MAJORS, "grades": GRADES})


@login_required
def delete_class(request, class_id):
    if request.method != "POST":
        return redirect("classes")
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    if request.POST.get("confirm") == "yes":
        title = str(school_class)
        # Cascades to its students and attendance history.
        school_class.delete()
        messages.success(
            request, f"کلاس «{title}» و دانش‌آموزان و سوابق وابسته حذف شدند.")
    else:
        messages.error(request, "حذف کلاس تأیید نشد.")
    return redirect("classes")


@login_required
def students(request, class_id):
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "bulk":
            lines = [line.strip() for line in request.POST.get(
                "names", "").splitlines() if line.strip()]
            added = 0
            with transaction.atomic():
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        Student.objects.create(
                            school_class=school_class, first_name=parts[0], last_name=" ".join(parts[1:]))
                        added += 1
            messages.success(
                request, f"{added} دانش‌آموز اضافه شد. هر خط باید شامل نام و نام خانوادگی باشد.")
        elif action == "add":
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            if first_name and last_name:
                Student.objects.create(school_class=school_class, first_name=first_name,
                                       last_name=last_name, file_number=request.POST.get("file_number", "").strip())
                messages.success(request, "دانش‌آموز اضافه شد.")
            else:
                messages.error(request, "نام و نام خانوادگی الزامی است.")
        elif action == "edit":
            student = get_object_or_404(Student, pk=request.POST.get(
                "student_id"), school_class=school_class)
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            target_class = get_object_or_404(
                SchoolClass, pk=request.POST.get("target_class_id"))
            if not first_name or not last_name:
                messages.error(request, "نام و نام خانوادگی الزامی است.")
            else:
                student.first_name = first_name
                student.last_name = last_name
                student.file_number = request.POST.get(
                    "file_number", "").strip()
                student.school_class = target_class
                student.save()
                messages.success(request, "اطلاعات دانش‌آموز به‌روزرسانی شد.")
                if target_class.pk != school_class.pk:
                    return redirect("students", class_id=target_class.pk)
        elif action == "delete":
            Student.objects.filter(pk=request.POST.get(
                "student_id"), school_class=school_class).delete()
            messages.success(
                request, "دانش‌آموز و سوابق حضور و غیاب وابسته به او حذف شد.")
        return redirect("students", class_id=class_id)
    return render(request, "students.html", {"school_class": school_class, "students": school_class.students.filter(active=True), "all_classes": SchoolClass.objects.all()})


@login_required
def reset_data(request):
    if not request.user.is_superuser:
        messages.error(
            request, "فقط حساب مدیر سامانه اجازه پاک‌سازی اطلاعات را دارد.")
        return redirect("dashboard")
    if request.method == "POST":
        phrase = request.POST.get("confirm_phrase", "").strip()
        password = request.POST.get("password", "")
        if phrase != "پاکسازی کامل" or not request.user.check_password(password):
            messages.error(
                request, "تأیید پاک‌سازی ناموفق بود. عبارت و رمز عبور را بررسی کن.")
            return redirect("reset_data")
        with transaction.atomic():
            AttendanceRecord.objects.all().delete()
            AttendanceSession.objects.all().delete()
            Student.objects.all().delete()
            SchoolClass.objects.all().delete()
        messages.success(
            request, "تمام اطلاعات کلاس‌ها، دانش‌آموزان و سوابق حضور و غیاب پاک شد. حساب کاربری معاون حفظ شده است.")
        return redirect("dashboard")
    counts = {
        "classes": SchoolClass.objects.count(),
        "students": Student.objects.count(),
        "sessions": AttendanceSession.objects.count(),
        "records": AttendanceRecord.objects.count(),
    }
    return render(request, "reset_data.html", {"counts": counts})


@login_required
def attendance(request):
    date_value = request.GET.get(
        "date") or request.POST.get("date") or today_jalali()
    selected_date = parse_jalali(date_value)
    selected_class_id = request.GET.get(
        "class_id") or request.POST.get("class_id")
    school_classes = SchoolClass.objects.all()
    selected_class = SchoolClass.objects.filter(
        pk=selected_class_id).first() if selected_class_id else None
    records = {}
    if selected_class:
        session = AttendanceSession.objects.filter(
            school_class=selected_class, date=selected_date).first()
        if session:
            records = {
                r.student_id: r for r in session.records.select_related("student")}
    if request.method == "POST" and selected_class:
        session, _ = AttendanceSession.objects.get_or_create(
            school_class=selected_class, date=selected_date)
        with transaction.atomic():
            for student in selected_class.students.filter(active=True):
                status = request.POST.get(f"status_{student.id}", "present")
                if status not in ["present", "absent", "late"]:
                    status = "present"
                note = request.POST.get(f"note_{student.id}", "").strip()[:250]
                AttendanceRecord.objects.update_or_create(
                    session=session, student=student, defaults={"status": status, "note": note})
        messages.success(request, "حضور و غیاب این کلاس ذخیره شد.")
        return redirect(f"/attendance/?date={date_value}&class_id={selected_class.id}")
    return render(request, "attendance.html", {"classes": school_classes, "selected_class": selected_class, "students": selected_class.students.filter(active=True) if selected_class else [], "records": records, "date_value": date_value, "today": today_jalali()})


@login_required
def reports(request):
    date_value = request.GET.get("date", today_jalali())
    selected_date = parse_jalali(date_value)

    sessions = list(
        AttendanceSession.objects.filter(date=selected_date)
        .select_related("school_class")
        .prefetch_related("records__student")
    )

    totals = {"present": 0, "absent": 0, "late": 0}
    rows = []
    expected_students = 0

    for s in sessions:
        active_students = s.school_class.students.filter(active=True)
        expected_count = active_students.count()

        records = s.records.filter(student__active=True)

        counts = {
            k: records.filter(status=k).count()
            for k in totals
        }

        for k in totals:
            totals[k] += counts[k]

        expected_students += expected_count

        recorded_count = sum(counts.values())

        rows.append({
            "session": s,
            "counts": counts,
            "expected_count": expected_count,
            "missing_count": max(expected_count - recorded_count, 0),
            "records": records.filter(status="absent").select_related("student"),
        })

    recorded_students = sum(totals.values())

    missing_students = max(
        expected_students - recorded_students, 0
    )

    rate = round(
        (totals["present"] + totals["late"]) * 100 / expected_students,
        1
    ) if expected_students else 0

    registered_class_ids = [s.school_class_id for s in sessions]

    active_classes = SchoolClass.objects.annotate(
        active_students_count=Count(
            "students",
            filter=Q(students__active=True)
        )
    ).filter(active_students_count__gt=0)

    unrecorded_classes = active_classes.exclude(
        id__in=registered_class_ids
    )

    all_students = Student.objects.filter(active=True).count()

    grade_names = {10: "دهم", 11: "یازدهم", 12: "دوازدهم"}

    output = [
        f"غایبین  {jdatetime.date.fromgregorian(date=selected_date).strftime('%A %d/%m/%Y')}"
    ]

    for grade in [12, 11, 10]:
        output.append(grade_names[grade] + "................................")

        for major, _ in MAJORS:
            class_list = [
                s for s in sessions
                if s.school_class.grade == grade
                and s.school_class.major == major
            ]

            if class_list:
                for s in class_list:
                    names = "، ".join(
                        str(r.student)
                        for r in s.records.filter(
                            status="absent",
                            student__active=True
                        ).select_related("student")
                    )

                    section = (
                        f" ({s.school_class.section})"
                        if s.school_class.section else ""
                    )

                    output.append(f"{major}{section}: {names}")
            else:
                output.append(f"{major}:")

    return render(request, "reports.html", {
        "date_value": date_value,
        "totals": totals,
        "all_students": all_students,
        "expected_students": expected_students,
        "recorded_students": recorded_students,
        "missing_students": missing_students,
        "unrecorded_classes": unrecorded_classes,
        "unrecorded_classes_count": unrecorded_classes.count(),
        "rate": rate,
        "rows": rows,
        "output": "\n".join(output),
    })


@login_required
def excuses(request):
    if request.method == "POST":
        record = get_object_or_404(
            AttendanceRecord, pk=request.POST.get("record_id"))
        if request.POST.get("action") == "justify":
            record.justified = True
            record.justification_reason = request.POST.get(
                "reason", "").strip()[:250]
            record.justified_at = timezone.now()
        else:
            record.justified = False
            record.justification_reason = ""
            record.justified_at = None
        record.save()
        messages.success(request, "وضعیت موجه‌سازی به‌روزرسانی شد.")
        return redirect("excuses")
    q = request.GET.get("q", "").strip()
    records = AttendanceRecord.objects.filter(status="absent").select_related(
        "student", "session__school_class").order_by("-session__date")
    if q:
        records = records.filter(Q(student__first_name__icontains=q) | Q(
            student__last_name__icontains=q) | Q(student__file_number__icontains=q))
    if request.GET.get("filter") == "unjustified":
        records = records.filter(justified=False)
    return render(request, "excuses.html", {"records": records[:300], "q": q, "filter": request.GET.get("filter", "")})


@login_required
def backup(request):
    db_path = settings.DATABASES["default"]["NAME"]
    with open(db_path, "rb") as f:
        data = f.read()
    response = HttpResponse(data, content_type="application/x-sqlite3")
    response["Content-Disposition"] = f'attachment; filename="attendance-backup-{date.today().isoformat()}.sqlite3"'
    return response
