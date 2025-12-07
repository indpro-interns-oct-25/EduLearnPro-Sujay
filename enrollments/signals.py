from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from courses.models import Lesson
from .models import Enrollment, LessonProgress, calculate_progress


@receiver(post_save, sender=Enrollment)
def create_lesson_progress_records(sender, instance: Enrollment, created: bool, **kwargs) -> None:
    if not created:
        return

    lessons = Lesson.objects.filter(course=instance.course).order_by("order", "id")
    progress_objects = []

    for lesson in lessons:
        progress_objects.append(
            LessonProgress(enrollment=instance, lesson=lesson, completed=False)
        )

    LessonProgress.objects.bulk_create(progress_objects, ignore_conflicts=True)
    calculate_progress(instance)
