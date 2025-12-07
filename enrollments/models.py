from __future__ import annotations

from django.db import models
from django.utils import timezone

from courses.models import Course, Lesson
from users.models import User


class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    progress = models.PositiveIntegerField(default=0)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "course")
        ordering = ("-enrolled_at",)

    def __str__(self) -> str:
        return f"{self.user} -> {self.course}"

    @property
    def completion_date(self):
        """Return completion date if course is completed"""
        if self.is_completed and self.completed_at:
            return self.completed_at
        return None

    def mark_as_completed(self):
        """Mark enrollment as completed"""
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.progress = 100
            self.save(update_fields=['is_completed', 'completed_at', 'progress'])


class LessonProgress(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="lesson_progress")
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("enrollment", "lesson")
        ordering = ("lesson__order", "lesson__id")

    def __str__(self) -> str:
        status = "Completed" if self.completed else "Pending"
        return f"{self.enrollment.user} - {self.lesson} ({status})"


def calculate_progress(enrollment: Enrollment) -> int:
    """Calculate and update enrollment progress"""
    total_lessons = enrollment.lesson_progress.count()
    if total_lessons == 0:
        enrollment.progress = 0
        enrollment.save(update_fields=["progress"])
        return 0

    completed_lessons = enrollment.lesson_progress.filter(completed=True).count()
    percentage = int((completed_lessons / total_lessons) * 100)
    percentage = min(100, max(0, percentage))

    # Check if course is completed
    was_completed = enrollment.is_completed
    is_now_completed = percentage == 100 and total_lessons > 0

    # Update progress and completion status
    if enrollment.progress != percentage or enrollment.is_completed != is_now_completed:
        enrollment.progress = percentage
        enrollment.is_completed = is_now_completed
        
        # Set completion date if just completed
        if is_now_completed and not was_completed:
            enrollment.completed_at = timezone.now()
            enrollment.save(update_fields=["progress", "is_completed", "completed_at"])
        else:
            enrollment.save(update_fields=["progress", "is_completed"])

    return percentage


class Certificate(models.Model):
    """Certificate of completion for a course"""
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="certificate"
    )
    certificate_id = models.CharField(max_length=100, unique=True, db_index=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ("-issued_at",)
        verbose_name = "Certificate"
        verbose_name_plural = "Certificates"

    def __str__(self) -> str:
        return f"Certificate for {self.enrollment.user} - {self.enrollment.course}"

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            # Generate unique certificate ID
            import uuid
            self.certificate_id = f"CERT-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
