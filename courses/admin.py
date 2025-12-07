from django.contrib import admin
from . models import Course, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'instructor', 'category', 'level', 'status', 'is_free', 'price', 'created_at']
    list_filter = ['status', 'category', 'level', 'is_free', 'created_at']
    search_fields = ['title', 'description', 'instructor__username', 'instructor__email']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'learning_outcomes', 'instructor')
        }),
        ('Course Details', {
            'fields': ('category', 'level', 'thumbnail', 'promo_video_url', 'duration', 'status')
        }),
        ('Pricing', {
            'fields': ('is_free', 'price', 'discounted_price')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'created_at']
    list_filter = ['course', 'created_at']
    search_fields = ['title', 'course__title']
    ordering = ['course', 'order']
