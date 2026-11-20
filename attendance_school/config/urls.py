from django.contrib import admin
from django.urls import path, include
from attendance import views
urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("sw.js", views.service_worker, name="service_worker"),
    path("", include("attendance.urls")),
]
