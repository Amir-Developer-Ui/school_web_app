from django.urls import path
from . import views
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("classes/", views.classes, name="classes"),
    path("classes/<int:class_id>/edit/", views.edit_class, name="edit_class"),
    path("classes/<int:class_id>/delete/",
         views.delete_class, name="delete_class"),
    path("classes/<int:class_id>/students/", views.students, name="students"),
    path("attendance/", views.attendance, name="attendance"),
    path("reports/", views.reports, name="reports"),
    path("excuses/", views.excuses, name="excuses"),
    path("backup/", views.backup, name="backup"),
    path("settings/reset-data/", views.reset_data, name="reset_data"),
    # ثبت وقایع
    path("incidents/", views.incident_sheets, name="incident_sheets"),
    path("incidents/create/", views.create_incident_sheet, name="create_incident_sheet"),
    path("incidents/<int:sheet_id>/", views.incident_detail, name="incident_detail"),
    path("incidents/<int:sheet_id>/delete/", views.delete_incident_sheet, name="delete_incident_sheet"),
    path( "incidents/<int:sheet_id>/edit/<int:entry_id>/", views.edit_incident_entry, name="edit_incident_entry" ), 
    path( "incidents/<int:sheet_id>/delete/<int:entry_id>/", views.delete_incident_entry, name="delete_incident_entry" ),
]
