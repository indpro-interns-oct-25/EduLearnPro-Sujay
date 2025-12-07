from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Max, Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView

from enrollments.models import Enrollment

from .forms import CourseForm
from .models import Course, Lesson

# Create your views here.

def home(request):
    # Only show published courses to guests and students
    # Instructors can see their own draft courses too
    if request.user.is_authenticated and request.user.role == 'instructor':
        # Instructors see published courses + their own drafts
        courses = Course.objects.select_related("instructor").filter(
            Q(status='published') | Q(instructor=request.user)
        ).annotate(enrollment_count=Count("enrollments", distinct=True)).order_by('-created_at')[:6]
    else:
        # Guests and students only see published courses
        courses = Course.objects.select_related("instructor").filter(status='published').annotate(enrollment_count=Count("enrollments", distinct=True)).order_by('-created_at')[:6]
    return render(request, "home/index.html", {"courses": courses})


def course_list(request):
    # Role-based course visibility:
    # - Guests/Students: Only published courses
    # - Instructors: Published courses + their own drafts
    if request.user.is_authenticated and request.user.role == 'instructor':
        # Instructors see published courses + their own drafts
        courses_qs = (
            Course.objects.select_related("instructor")
            .prefetch_related("lessons", "enrollments__user")
            .filter(Q(status='published') | Q(instructor=request.user))
        )
    else:
        # Guests and students only see published courses
        courses_qs = (
            Course.objects.select_related("instructor")
            .prefetch_related("lessons", "enrollments__user")
            .filter(status='published')
        )

    query = request.GET.get("q")
    if query:
        courses_qs = courses_qs.filter(title__icontains=query)

    # Optional category filter
    category = request.GET.get("category")
    if category:
        courses_qs = courses_qs.filter(category__iexact=category)

    # Optional level filter
    level = request.GET.get("level")
    if level:
        courses_qs = courses_qs.filter(level__iexact=level)

    price_filter = request.GET.get("price")
    if price_filter == "paid":
        courses_qs = courses_qs.filter(price__gt=0)

    courses_qs = courses_qs.annotate(enrollment_count=Count("enrollments", distinct=True))

    sort = request.GET.get("sort", "popular")
    if sort == "newest":
        courses_qs = courses_qs.order_by("-created_at")
    elif sort == "price_low":
        courses_qs = courses_qs.order_by("price", "-created_at")
    elif sort == "price_high":
        courses_qs = courses_qs.order_by("-price", "-created_at")
    else:
        courses_qs = courses_qs.order_by("-enrollment_count", "-created_at")

    # Gather available categories for the filter dropdown (only from published courses)
    categories = (
        Course.objects.filter(status='published')
        .order_by("category")
        .values_list("category", flat=True)
        .distinct()
        .exclude(category__isnull=True)
    )

    choice_map = dict(Course.CATEGORY_CHOICES)
    category_options = [(cat, choice_map.get(cat, cat.title())) for cat in categories if cat]

    # Get available levels for filter
    levels = (
        Course.objects.filter(status='published')
        .order_by("level")
        .values_list("level", flat=True)
        .distinct()
        .exclude(level__isnull=True)
    )
    
    choice_map = dict(Course.LEVEL_CHOICES)
    level_options = [(lev, choice_map.get(lev, lev.title())) for lev in levels if lev]

    paginator = Paginator(courses_qs, 12)
    page_number = request.GET.get("page")
    courses_page = paginator.get_page(page_number)

    context = {
        "courses": courses_page,
        "query": query or "",
        "category": category or "",
        "level": level or "",
        "categories": [c for c in categories if c],
        "category_options": category_options,
        "level_options": level_options,
        "total_courses": paginator.count,
        "page_obj": courses_page,
        "paginator": paginator,
        "selected_filters": {
            "category": category or "",
            "level": level or "",
            "price": price_filter or "",
            "sort": sort,
        },
    }
    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")
    context["querystring"] = query_params.urlencode()
    # If user is authenticated, compute enrolled course ids to show correct CTA without template hacks
    if request.user.is_authenticated:
        enrolled_ids = (
            Enrollment.objects.filter(user=request.user, course__in=courses_page.object_list)
            .values_list("course_id", flat=True)
        )
        context["enrolled_ids"] = set(enrolled_ids)
    else:
        context["enrolled_ids"] = set()
    return render(request, "courses/course_list.html", context)


def detail(request, slug):
    course = get_object_or_404(Course.objects.select_related("instructor"), slug=slug)
    
    # Access control: Check if user can view this course
    is_instructor_owner = (
        request.user.is_authenticated 
        and course.instructor == request.user
    )
    
    # If course is draft, only instructor owner can view
    if course.status == 'draft' and not is_instructor_owner:
        return HttpResponseForbidden("This course is not available. Only the instructor can view draft courses.")
    
    # If course is not published and user is not the instructor, deny access
    if course.status != 'published' and not is_instructor_owner:
        return HttpResponseForbidden("This course is not available.")
    
    lessons = course.lessons.all()
    
    # Related courses: Only show published courses
    related_courses = (
        Course.objects.filter(status='published')
        .exclude(pk=course.pk)
        .select_related("instructor")
        .prefetch_related("lessons")
        [:3]
    )
    
    # Get learning outcomes from course if available, otherwise use defaults
    if course.learning_outcomes:
        learning_points = [point.strip() for point in course.learning_outcomes.split('\n') if point.strip()]
    else:
        learning_points = [
            "Understand the core concepts with hands-on examples",
            "Build real-world projects to reinforce learning",
            "Collaborate with peers and receive instructor feedback",
        ]

    # Determine if current user is enrolled in this course (if authenticated)
    is_enrolled = False
    enrollment_obj = None
    if request.user.is_authenticated:
        enrollment_qs = Enrollment.objects.filter(user=request.user, course=course)
        if enrollment_qs.exists():
            is_enrolled = True
            enrollment_obj = enrollment_qs.first()

    context = {
        "course": course,
        "lessons": lessons,
        "related_courses": related_courses,
        "learning_points": learning_points,
        "is_enrolled": is_enrolled,
        "enrollment": enrollment_obj,
        "is_instructor_owner": is_instructor_owner,
    }
    return render(request, "courses/course_detail.html", context)


@login_required
def course_manage(request, slug):
    course = get_object_or_404(Course, slug=slug, instructor=request.user)
    lessons = course.lessons.all().order_by("order", "id")
    
    # Handle lesson deletion
    if request.method == "GET" and "delete" in request.GET:
        lesson_id = request.GET.get("delete")
        try:
            lesson = Lesson.objects.get(pk=lesson_id, course=course)
            lesson.delete()
            # Reorder remaining lessons
            remaining_lessons = course.lessons.all().order_by("order", "id")
            for idx, remaining_lesson in enumerate(remaining_lessons, start=1):
                if remaining_lesson.order != idx:
                    remaining_lesson.order = idx
                    remaining_lesson.save()
            messages.success(request, "Lesson deleted successfully.")
            return redirect("courses:manage", slug=slug)
        except Lesson.DoesNotExist:
            messages.error(request, "Lesson not found.")
            return redirect("courses:manage", slug=slug)
    
    # Handle lesson reordering
    if request.method == "GET" and "reorder" in request.GET:
        lesson_id = request.GET.get("reorder")
        direction = request.GET.get("direction")
        try:
            lesson = Lesson.objects.get(pk=lesson_id, course=course)
            all_lessons = list(course.lessons.all().order_by("order", "id"))
            current_index = next((i for i, l in enumerate(all_lessons) if l.pk == lesson.pk), None)
            
            if current_index is not None:
                if direction == "up" and current_index > 0:
                    # Swap with previous lesson
                    prev_lesson = all_lessons[current_index - 1]
                    lesson.order, prev_lesson.order = prev_lesson.order, lesson.order
                    lesson.save()
                    prev_lesson.save()
                    messages.success(request, "Lesson moved up successfully.")
                elif direction == "down" and current_index < len(all_lessons) - 1:
                    # Swap with next lesson
                    next_lesson = all_lessons[current_index + 1]
                    lesson.order, next_lesson.order = next_lesson.order, lesson.order
                    lesson.save()
                    next_lesson.save()
                    messages.success(request, "Lesson moved down successfully.")
            
            return redirect("courses:manage", slug=slug)
        except Lesson.DoesNotExist:
            messages.error(request, "Lesson not found.")
            return redirect("courses:manage", slug=slug)
    
    # Handle lesson creation and editing
    if request.method == "POST":
        lesson_id = request.POST.get("lesson_id")
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        order = request.POST.get("order", "1")
        video_url = request.POST.get("video_url", "").strip()
        resources = request.FILES.get("resources")
        
        if not title or not content:
            messages.error(request, "Title and content are required.")
            return redirect("courses:manage", slug=slug)
        
        try:
            order = int(order)
            # Ensure order doesn't conflict with existing lessons
            if lesson_id:
                # Editing existing lesson - check if order conflicts
                existing_lesson = Lesson.objects.filter(course=course, order=order).exclude(pk=lesson_id).first()
                if existing_lesson:
                    # Find next available order
                    max_order = course.lessons.aggregate(Max('order'))['order__max'] or 0
                    order = max_order + 1
            else:
                # Creating new lesson - check if order conflicts
                existing_lesson = Lesson.objects.filter(course=course, order=order).first()
                if existing_lesson:
                    # Find next available order
                    max_order = course.lessons.aggregate(Max('order'))['order__max'] or 0
                    order = max_order + 1
        except (ValueError, TypeError):
            max_order = course.lessons.aggregate(Max('order'))['order__max'] or 0
            order = max_order + 1
        
        # Check if we're editing an existing lesson
        if lesson_id:
            try:
                lesson = Lesson.objects.get(pk=lesson_id, course=course)
                lesson.title = title
                lesson.content = content
                lesson.order = order
                lesson.video_url = video_url if video_url else None
                if resources:
                    lesson.resources = resources
                lesson.save()
                messages.success(request, "Lesson updated successfully.")
            except Lesson.DoesNotExist:
                messages.error(request, "Lesson not found.")
        else:
            # Create new lesson
            lesson = Lesson.objects.create(
                course=course,
                title=title,
                content=content,
                order=order,
                video_url=video_url if video_url else None,
            )
            if resources:
                lesson.resources = resources
                lesson.save()
            messages.success(request, "Lesson created successfully.")
        
        return redirect("courses:manage", slug=slug)
    
    context = {
        "course": course,
        "lessons": lessons,
    }
    return render(request, "courses/course_manage.html", context)


class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = "courses/course_form.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "page_title": "Update Course",
            "submit_label": "Save Changes",
        })
        return context

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        return super().form_valid(form)

    def test_func(self):
        course = self.get_object()
        return self.request.user.is_authenticated and course.instructor == self.request.user

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return HttpResponseForbidden("Only the course instructor can modify this course.")
        return super().handle_no_permission()

    def get_success_url(self):
        return reverse("courses:detail", kwargs={"slug": self.object.slug})


@login_required
def lesson_view(request, course_slug, pk):
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, pk=pk, course=course)
    
    # Check if user is the instructor (instructors can always view their course lessons)
    is_instructor_owner = course.instructor == request.user
    
    enrollment = None
    lesson_progress = None
    course_progress_percentage = 0
    
    # If not instructor, check enrollment
    if not is_instructor_owner:
        # Check if course is published
        if course.status != 'published':
            return HttpResponseForbidden("This course is not available.")
        
        # Check if user is enrolled
        enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
        if not enrollment:
            messages.error(request, "You must enroll in this course to access lessons.")
            return redirect("courses:detail", slug=course.slug)
        
        # Get or create lesson progress
        from enrollments.models import LessonProgress, calculate_progress
        lesson_progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={'completed': False}
        )
        
        # Calculate course progress
        course_progress_percentage = calculate_progress(enrollment)
    
    # Get all lessons in order
    all_lessons = list(course.lessons.all().order_by("order", "id"))
    current_index = next((i for i, l in enumerate(all_lessons) if l.pk == lesson.pk), None)
    
    # Get previous and next lessons
    prev_lesson = all_lessons[current_index - 1] if current_index and current_index > 0 else None
    next_lesson = all_lessons[current_index + 1] if current_index is not None and current_index < len(all_lessons) - 1 else None
    
    # Get all lessons with progress status for sidebar
    lessons_with_progress = []
    if enrollment:
        from enrollments.models import LessonProgress
        progress_dict = {
            lp.lesson_id: lp 
            for lp in LessonProgress.objects.filter(
                enrollment=enrollment,
                lesson__course=course
            ).select_related('lesson')
        }
        
        for l in all_lessons:
            lessons_with_progress.append({
                'lesson': l,
                'progress': progress_dict.get(l.pk),
                'is_current': l.pk == lesson.pk
            })
    else:
        for l in all_lessons:
            lessons_with_progress.append({
                'lesson': l,
                'progress': None,
                'is_current': l.pk == lesson.pk
            })

    context = {
        "course": course,
        "lesson": lesson,
        "prev_lesson": prev_lesson,
        "next_lesson": next_lesson,
        "lessons_with_progress": lessons_with_progress,
        "is_instructor_owner": is_instructor_owner,
        "enrollment": enrollment,
        "lesson_progress": lesson_progress,
        "course_progress_percentage": course_progress_percentage,
        "is_completed": lesson_progress.completed if lesson_progress else False,
    }
    return render(request, "courses/lesson_view.html", context)


class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = "courses/course_form.html"
    success_url = reverse_lazy("courses:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "page_title": "Create a New Course",
            "submit_label": "Create Course",
        })
        return context

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        return super().form_valid(form)

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and hasattr(self.request.user, "profile")
            and self.request.user.role == "instructor"
        )

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return HttpResponse("Only instructors can create courses.", status=403)
        return super().handle_no_permission()

    def get_success_url(self):
        return reverse("courses:detail", kwargs={"slug": self.object.slug})



@login_required
def instructor_dashboard(request):
    instructor = request.user

    # All courses created by instructor
    instructor_courses = (
        Course.objects.filter(instructor=instructor)
        .annotate(
            enrolled_count=Count("enrollments", distinct=True),
            avg_progress=Avg("enrollments__progress"),
        )
        .prefetch_related("lessons")
    )

    # All students enrolled in any of instructor's courses
    enrollment_qs = Enrollment.objects.filter(course__in=instructor_courses)
    recent_students = (
        enrollment_qs.select_related("user", "course")
        .order_by("-id")[:10]
    )

    # Basic stats
    context = {
        "courses_count": instructor_courses.count(),
        "total_students": enrollment_qs.count(),
        "total_earnings": 0,  # Update later if you add pricing
        "instructor_courses": instructor_courses,
        "recent_students": recent_students,
    }

    return render(request, "courses/instructor_dashboard.html", context)


def instructor_profile(request, username):
    """Public instructor profile page"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    instructor = get_object_or_404(User, username=username)
    
    # Check if user is an instructor
    if getattr(instructor, 'role', None) != 'instructor':
        messages.error(request, "This user is not an instructor.")
        return redirect('courses:list')
    
    # Get instructor's published courses
    instructor_courses = (
        Course.objects.filter(instructor=instructor, status='published')
        .annotate(enrolled_count=Count("enrollments", distinct=True))
        .prefetch_related("lessons")
        .order_by('-created_at')
    )
    
    # Calculate statistics
    total_courses = instructor_courses.count()
    total_students = Enrollment.objects.filter(
        course__instructor=instructor,
        course__status='published'
    ).values('user').distinct().count()
    
    total_enrollments = Enrollment.objects.filter(
        course__instructor=instructor,
        course__status='published'
    ).count()
    
    # Calculate average rating (placeholder - you can implement actual reviews later)
    avg_rating = 4.8  # Placeholder
    total_reviews = 1250  # Placeholder
    
    context = {
        'instructor': instructor,
        'instructor_courses': instructor_courses,
        'total_courses': total_courses,
        'total_students': total_students,
        'total_enrollments': total_enrollments,
        'total_reviews': total_reviews,
        'avg_rating': avg_rating,
    }
    
    return render(request, "courses/instructor_profile.html", context)