from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from courses.models import Course, Lesson
from .models import Certificate, Enrollment, LessonProgress, calculate_progress


def _ensure_lesson_progress(enrollment: Enrollment) -> None:
    existing_lesson_ids = set(
        enrollment.lesson_progress.values_list("lesson_id", flat=True)
    )
    missing_lessons = (
        Lesson.objects.filter(course=enrollment.course)
        .exclude(id__in=existing_lesson_ids)
        .order_by("order", "id")
    )
    LessonProgress.objects.bulk_create(
        [
            LessonProgress(enrollment=enrollment, lesson=lesson, completed=False)
            for lesson in missing_lessons
        ],
        ignore_conflicts=True,
    )


@login_required
def my_courses(request):
    enrollments = (
        Enrollment.objects.filter(user=request.user)
        .select_related("course", "course__instructor")
        .order_by("-enrolled_at")
    )

    for enrollment in enrollments:
        _ensure_lesson_progress(enrollment)
        calculate_progress(enrollment)

    context = {
        "enrolled_courses": enrollments,
    }
    return render(request, "enrollments/my_courses.html", context)


@login_required
def course_progress(request, slug: str):
    course = get_object_or_404(
        Course.objects.select_related("instructor"), slug=slug
    )
    enrollment = get_object_or_404(
        Enrollment.objects.select_related("course"),
        user=request.user,
        course=course,
    )

    _ensure_lesson_progress(enrollment)
    lesson_progress_qs = (
        enrollment.lesson_progress.select_related("lesson")
        .order_by("lesson__order", "lesson__id")
    )
    progress_percentage = calculate_progress(enrollment)

    context = {
        "course": course,
        "lessons": lesson_progress_qs,
        "progress": progress_percentage,
    }
    return render(request, "enrollments/progress.html", context)


@login_required
def payment(request, slug: str):
    """Payment page before enrollment"""
    course = get_object_or_404(
        Course.objects.select_related("instructor"), slug=slug
    )
    
    # Check if already enrolled
    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, "You are already enrolled in this course.")
        return redirect("courses:detail", slug=slug)
    
    # Only allow payment for published courses
    if course.status != 'published':
        messages.error(request, "This course is not available for enrollment.")
        return redirect("courses:detail", slug=slug)
    
    # Prevent instructors from enrolling in their own courses
    if course.instructor == request.user:
        messages.info(request, "You cannot enroll in your own course. Use the instructor dashboard to manage it.")
        return redirect("courses:detail", slug=slug)
    
    # Calculate final price
    final_price = course.discounted_price if (course.discounted_price and course.discounted_price < course.price) else course.price
    
    context = {
        "course": course,
        "final_price": final_price,
        "original_price": course.price,
        "has_discount": course.discounted_price and course.discounted_price < course.price,
    }
    return render(request, "enrollments/payment.html", context)


@login_required
@transaction.atomic
def process_payment(request, slug: str):
    """Process dummy payment and enroll user"""
    course = get_object_or_404(
        Course.objects.select_related("instructor"), slug=slug
    )
    
    # Check if already enrolled
    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, "You are already enrolled in this course.")
        return redirect("enrollments:my-courses")
    
    # Only allow enrollment in published courses
    if course.status != 'published':
        messages.error(request, "This course is not not available for enrollment.")
        return redirect("courses:detail", slug=slug)
    
    # Prevent instructors from enrolling in their own courses
    if course.instructor == request.user:
        messages.info(request, "You cannot enroll in your own course.")
        return redirect("courses:detail", slug=slug)
    
    # Dummy payment processing - just enroll the user
    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user,
        course=course,
    )

    _ensure_lesson_progress(enrollment)
    calculate_progress(enrollment)

    if created:
        messages.success(request, f"Payment successful! You have been enrolled in '{course.title}'. Start learning now!")
    else:
        messages.info(request, "You are already enrolled in this course.")

    return redirect("enrollments:my-courses")


@login_required
@transaction.atomic
def enroll(request, slug: str):
    """Redirect to payment page instead of direct enrollment"""
    course = get_object_or_404(
        Course.objects.select_related("instructor"), slug=slug
    )
    
    # Check if already enrolled
    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, "You are already enrolled in this course.")
        return redirect("enrollments:my-courses")
    
    # Redirect to payment page
    return redirect("enrollments:payment", slug=slug)


@login_required
@require_POST
@transaction.atomic
def mark_lesson_complete(request, lesson_id):
    """Mark a lesson as complete or incomplete"""
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    course = lesson.course
    
    # Check enrollment
    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
    if not enrollment:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Not enrolled in this course'}, status=403)
        messages.error(request, "You must be enrolled in this course.")
        return redirect("courses:detail", slug=course.slug)
    
    # Get or create lesson progress
    lesson_progress, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson,
        defaults={'completed': False}
    )
    
    # Toggle completion status
    lesson_progress.completed = not lesson_progress.completed
    if lesson_progress.completed:
        from django.utils import timezone
        lesson_progress.completed_at = timezone.now()
        
        # Update streak when lesson is completed
        if hasattr(request.user, 'profile'):
            request.user.profile.update_streak()
    else:
        lesson_progress.completed_at = None
    lesson_progress.save()
    
    # Recalculate course progress
    progress_percentage = calculate_progress(enrollment)
    
    # Refresh enrollment from DB to get updated completion status
    enrollment.refresh_from_db()
    
    # Check if course is completed and create certificate if needed
    course_completed = enrollment.is_completed
    certificate_created = False
    
    if course_completed:
        from .models import Certificate
        certificate, created = Certificate.objects.get_or_create(
            enrollment=enrollment
        )
        certificate_created = created
    
    # AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'completed': lesson_progress.completed,
            'course_progress': progress_percentage,
            'course_completed': course_completed,
            'certificate_created': certificate_created,
            'certificate_id': enrollment.certificate.certificate_id if course_completed and hasattr(enrollment, 'certificate') else None,
            'completed_at': lesson_progress.completed_at.isoformat() if lesson_progress.completed_at else None,
        })
    
    # Regular request
    if lesson_progress.completed:
        messages.success(request, f"Lesson '{lesson.title}' marked as complete!")
        if course_completed:
            messages.success(request, f"🎉 Congratulations! You've completed '{course.title}'! Your certificate is ready.")
    else:
        messages.info(request, f"Lesson '{lesson.title}' marked as incomplete.")
    
    return redirect("courses:lesson", course_slug=course.slug, pk=lesson.pk)


@login_required
def certificate_view(request, slug: str):
    """Display certificate for a completed course"""
    course = get_object_or_404(
        Course.objects.select_related("instructor"), slug=slug
    )
    enrollment = get_object_or_404(
        Enrollment.objects.select_related("course", "user"),
        user=request.user,
        course=course,
    )
    
    # Check if course is completed
    if not enrollment.is_completed:
        messages.warning(request, "You must complete the course to view your certificate.")
        return redirect("courses:detail", slug=slug)
    
    # Get or create certificate
    certificate, created = Certificate.objects.get_or_create(enrollment=enrollment)
    
    context = {
        "certificate": certificate,
        "enrollment": enrollment,
        "course": course,
    }
    return render(request, "enrollments/certificate.html", context)


@login_required
def certificate_download(request, slug: str):
    """Download certificate as PDF (future implementation)"""
    # For now, redirect to certificate view
    # PDF generation can be added later with libraries like reportlab or weasyprint
    return redirect("enrollments:certificate", slug=slug)
