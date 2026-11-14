from django.urls import path
from . import views
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("classes/", views.classes, name="classes"),
    path("classes/<int:class_id>/edit/", views.edit_class, name="edit_class"),
    path("classes/<int:class_id>/delete/", views.delete_class, name="delete_class"),
    path("classes/<int:class_id>/students/", views.students, name="students"),
    path("attendance/", views.attendance, name="attendance"),
    path("reports/", views.reports, name="reports"),
    path("excuses/", views.excuses, name="excuses"),
    path("backup/", views.backup, name="backup"),
    path("settings/reset-data/", views.reset_data, name="reset_data"),
]
