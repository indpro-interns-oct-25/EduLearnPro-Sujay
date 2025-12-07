from django.contrib import admin

from .models import Certificate, Enrollment, LessonProgress


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "progress", "is_completed", "enrolled_at", "completed_at")
    list_filter = ("is_completed", "course", "enrolled_at")
    search_fields = ("user__username", "user__email", "course__title")
    readonly_fields = ("enrolled_at", "completed_at")


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "lesson", "completed", "completed_at")
    list_filter = ("completed", "lesson__course")
    search_fields = ("enrollment__user__username", "lesson__title")


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_id", "enrollment", "issued_at")
    list_filter = ("issued_at",)
    search_fields = ("certificate_id", "enrollment__user__username", "enrollment__course__title")
    readonly_fields = ("certificate_id", "issued_at")
