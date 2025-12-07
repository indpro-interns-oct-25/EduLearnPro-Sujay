from django.urls import path
from . import views

app_name = "courses"

urlpatterns = [
    path("", views.course_list, name="list"),
    path("create/", views.CourseCreateView.as_view(), name="create"),
    path("instructor/dashboard/", views.instructor_dashboard, name="instructor-dashboard"),
    path("instructor/<str:username>/", views.instructor_profile, name="instructor_profile"),
    path("<slug:slug>/", views.detail, name="detail"),
    path("<slug:slug>/manage/", views.course_manage, name="manage"),
    path("<slug:slug>/edit/", views.CourseUpdateView.as_view(), name="edit"),
    path("<slug:course_slug>/lessons/<int:pk>/", views.lesson_view, name="lesson"),
]