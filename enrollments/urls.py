from django.urls import path
from . import views

app_name = "enrollments"

urlpatterns = [
    path("my-courses/", views.my_courses, name="my-courses"),
    path("<slug:slug>/progress/", views.course_progress, name="progress"),
    path("<slug:slug>/payment/", views.payment, name="payment"),
    path("<slug:slug>/payment/process/", views.process_payment, name="process-payment"),
    path("<slug:slug>/enroll/", views.enroll, name="enroll"),
    path("lesson/<int:lesson_id>/complete/", views.mark_lesson_complete, name="mark-lesson-complete"),
    path("<slug:slug>/certificate/", views.certificate_view, name="certificate"),
    path("<slug:slug>/certificate/download/", views.certificate_download, name="certificate-download"),
]