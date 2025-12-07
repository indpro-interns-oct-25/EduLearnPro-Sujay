import random
import logging
import traceback
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.conf import settings

from courses.models import Course
from enrollments.models import Enrollment
from .forms import ProfileEditForm, UserRegistrationForm, PasswordResetRequestForm, OTPVerificationForm, PasswordResetForm
from .models import PasswordResetOTP

User = get_user_model()


def login_user(request):
    if request.user.is_authenticated:
        destination = 'courses:instructor-dashboard' if request.user.role == "instructor" else 'users:student_dashboard'
        return redirect(destination)

    context = {}

    if request.method == "POST":
        identifier = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        remember_me = request.POST.get("remember_me", False)
        user = None

        if identifier and password:
            UserModel = get_user_model()
            matched_user = UserModel.objects.filter(email__iexact=identifier).first()
            if matched_user:
                user = authenticate(request, username=matched_user.username, password=password)
            else:
                user = authenticate(request, username=identifier, password=password)

        if user is not None:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)  # Session expires when browser closes
            messages.success(request, "Welcome back! You are now signed in.")
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)

            if user.role == "instructor":
                return redirect('courses:instructor-dashboard')
            return redirect('users:student_dashboard')

        messages.error(request, "Invalid credentials. Please check your email and password.")
        context["submitted_email"] = identifier

    return render(request, 'users/login.html', context)


def register_user(request):
    if request.user.is_authenticated:
        if request.user.role == "instructor":
            return redirect('courses:instructor-dashboard')
        return redirect('users:student_dashboard')
    
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('users:login')
        else:
            # Form errors will be displayed in the template
            pass
    else:
        form = UserRegistrationForm()

    return render(request, "users/register.html", {"form": form})


def check_and_award_achievements(user):
    """Check and award achievements for a user"""
    from .models import Achievement
    from enrollments.models import Enrollment
    
    completed_count = Enrollment.objects.filter(user=user, is_completed=True).count()
    profile = user.profile
    
    # Course completion achievements
    if completed_count >= 1:
        Achievement.objects.get_or_create(user=user, achievement_type='first_course')
    if completed_count >= 5:
        Achievement.objects.get_or_create(user=user, achievement_type='five_courses')
    if completed_count >= 10:
        Achievement.objects.get_or_create(user=user, achievement_type='ten_courses')
    
    # Streak achievements
    if profile.current_streak >= 7:
        Achievement.objects.get_or_create(user=user, achievement_type='streak_7')
    if profile.current_streak >= 30:
        Achievement.objects.get_or_create(user=user, achievement_type='streak_30')
    if profile.current_streak >= 100:
        Achievement.objects.get_or_create(user=user, achievement_type='streak_100')


def get_course_recommendations(user, limit=6):
    """Get course recommendations for a user"""
    from courses.models import Course
    from enrollments.models import Enrollment
    
    # Get user's enrolled course categories
    enrolled_courses = Enrollment.objects.filter(user=user).select_related('course')
    enrolled_categories = set(enrolled_courses.values_list('course__category', flat=True))
    enrolled_course_ids = set(enrolled_courses.values_list('course_id', flat=True))
    
    # Recommend courses in same categories or popular courses
    recommendations = Course.objects.filter(
        status='published'
    ).exclude(
        id__in=enrolled_course_ids
    ).exclude(
        instructor=user
    ).select_related('instructor').prefetch_related('lessons')
    
    # Prioritize courses in enrolled categories
    same_category = recommendations.filter(category__in=enrolled_categories)
    other_courses = recommendations.exclude(category__in=enrolled_categories)
    
    # Combine and limit
    recommended = list(same_category[:limit//2]) + list(other_courses[:limit//2])
    
    return recommended[:limit]


@login_required
def student_dashboard(request):
    """Student Dashboard with enrolled courses, progress stats, and personal info"""
    from enrollments.models import calculate_progress
    from enrollments.views import _ensure_lesson_progress
    from .models import Achievement
    
    enrollments = Enrollment.objects.filter(user=request.user).select_related('course', 'course__instructor').order_by('-enrolled_at')
    
    # Ensure lesson progress exists and recalculate progress for all enrollments
    for enrollment in enrollments:
        _ensure_lesson_progress(enrollment)
        calculate_progress(enrollment)
    
    # Refresh enrollments from DB
    enrollments = Enrollment.objects.filter(user=request.user).select_related('course', 'course__instructor').order_by('-enrolled_at')
    
    # Calculate stats
    total_enrolled = enrollments.count()
    in_progress_courses = enrollments.filter(is_completed=False).select_related('course', 'course__instructor')
    completed_courses = enrollments.filter(is_completed=True).select_related('course', 'course__instructor')
    
    # Calculate overall progress
    total_progress = 0
    total_lessons_completed = 0
    total_lessons = 0
    
    if enrollments.exists():
        total_progress = sum(e.progress for e in enrollments) / enrollments.count()
        # Calculate total lessons completed across all courses
        for enrollment in enrollments:
            total_lessons += enrollment.lesson_progress.count()
            total_lessons_completed += enrollment.lesson_progress.filter(completed=True).count()
    
    # Get next lesson for in-progress courses
    for enrollment in in_progress_courses:
        next_lesson = enrollment.lesson_progress.filter(completed=False).select_related('lesson').order_by('lesson__order', 'lesson__id').first()
        enrollment.next_lesson = next_lesson.lesson if next_lesson else None
    
    # Get recent activity (last 6 enrollments)
    recent_enrollments = enrollments[:6]
    
    # Get streak info
    profile = request.user.profile
    current_streak = profile.current_streak
    longest_streak = profile.longest_streak
    
    # Get achievements
    achievements = Achievement.objects.filter(user=request.user).order_by('-unlocked_at')[:6]
    
    # Get recommendations
    recommendations = get_course_recommendations(request.user, limit=6)
    
    # Check for new achievements
    check_and_award_achievements(request.user)
    
    context = {
        'total_enrolled': total_enrolled,
        'in_progress_courses': in_progress_courses,
        'completed_courses': completed_courses,
        'recent_enrollments': recent_enrollments,
        'total_progress': round(total_progress, 1),
        'total_lessons_completed': total_lessons_completed,
        'total_lessons': total_lessons,
        'completed_count': completed_courses.count(),
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'achievements': achievements,
        'recommendations': recommendations,
    }
    return render(request, 'users/student_dashboard.html', context)


@login_required
def instructor_dashboard(request):
    """Instructor Dashboard - only accessible to instructors"""
    if request.user.role != 'instructor':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('users:student_dashboard')
    
    from django.db.models import Avg, Count, Q
    from enrollments.models import calculate_progress
    from enrollments.views import _ensure_lesson_progress
    
    # Get instructor's courses
    instructor_courses = Course.objects.filter(instructor=request.user).annotate(
        enrolled_count=Count('enrollments')
    ).order_by('-created_at')
    
    # Calculate stats
    total_courses = instructor_courses.count()
    total_students = Enrollment.objects.filter(course__instructor=request.user).values('user').distinct().count()
    total_enrollments = Enrollment.objects.filter(course__instructor=request.user).count()
    
    # Calculate completion stats
    completed_enrollments = Enrollment.objects.filter(
        course__instructor=request.user,
        is_completed=True
    ).count()
    
    # Calculate average progress across all enrollments
    avg_progress = Enrollment.objects.filter(
        course__instructor=request.user
    ).aggregate(avg=Avg('progress'))['avg'] or 0
    
    # Get recent students with progress
    recent_enrollments = Enrollment.objects.filter(
        course__instructor=request.user
    ).select_related('user', 'course').order_by('-enrolled_at')[:10]
    
    # Ensure progress is calculated for recent enrollments
    for enrollment in recent_enrollments:
        _ensure_lesson_progress(enrollment)
        calculate_progress(enrollment)
    
    # Refresh to get updated progress
    recent_enrollments = Enrollment.objects.filter(
        course__instructor=request.user
    ).select_related('user', 'course').order_by('-enrolled_at')[:10]
    
    # Get courses with student progress breakdown
    courses_with_stats = []
    for course in instructor_courses[:5]:  # Top 5 courses
        course_enrollments = Enrollment.objects.filter(course=course)
        course_avg_progress = course_enrollments.aggregate(avg=Avg('progress'))['avg'] or 0
        course_completed = course_enrollments.filter(is_completed=True).count()
        course_total = course_enrollments.count()
        course_completion_rate = (course_completed / course_total * 100) if course_total > 0 else 0
        
        courses_with_stats.append({
            'course': course,
            'avg_progress': round(course_avg_progress, 1),
            'completed_count': course_completed,
            'total_enrollments': course_total,
            'completion_rate': round(course_completion_rate, 1),
        })
    
    # Calculate completion rate
    completion_rate = (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0
    
    # Course metrics summary
    published_courses = instructor_courses.filter(status='published').count()
    draft_courses = instructor_courses.filter(status='draft').count()
    total_lessons = sum(course.lessons.count() for course in instructor_courses)
    
    context = {
        'instructor_courses': instructor_courses,
        'courses_count': total_courses,
        'published_courses': published_courses,
        'draft_courses': draft_courses,
        'total_lessons': total_lessons,
        'total_students': total_students,
        'total_enrollments': total_enrollments,
        'completed_enrollments': completed_enrollments,
        'completion_rate': round(completion_rate, 1),
        'avg_progress': round(avg_progress, 1),
        'recent_students': recent_enrollments,
        'courses_with_stats': courses_with_stats,
    }
    return render(request, 'users/instructor_dashboard.html', context)


@login_required
def profile(request):
    """User profile page with editing capability"""
    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            # Refresh user and profile to get updated photo
            request.user.refresh_from_db()
            if hasattr(request.user, 'profile'):
                request.user.profile.refresh_from_db()
            messages.success(request, "Profile updated successfully!")
            return redirect('users:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileEditForm(instance=request.user)
    
    # Ensure profile exists
    from .models import Profile
    Profile.objects.get_or_create(user=request.user)
    request.user.refresh_from_db()
    
    context = {
        'form': form,
    }
    return render(request, 'users/profile.html', context)


def logout_view(request):
    """Logout user and redirect to home"""
    if request.user.is_authenticated:
        auth_logout(request)
        messages.success(request, "You have been logged out successfully.")
    return redirect('home')


def password_reset_request(request):
    """Request OTP for password reset"""
    if request.user.is_authenticated:
        return redirect('users:student_dashboard')
    
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            
            # Check if user exists
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                # For security, show same message even if user doesn't exist
                messages.success(request, f"If an account exists with {email}, an OTP has been sent. Please check your email.")
                return redirect('users:password_reset_request')
            
            # Generate 6-digit OTP
            otp = str(random.randint(100000, 999999))
            
            # Save OTP to database
            PasswordResetOTP.objects.create(email=email, otp=otp)
            
            # Send OTP via email
            try:
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@edulearnpro.com')
                
                # Check if email is configured (skip check if using console backend for testing)
                email_backend = getattr(settings, 'EMAIL_BACKEND', '')
                is_console_backend = 'console' in email_backend.lower()
                
                if not is_console_backend:
                    email_user = getattr(settings, 'EMAIL_HOST_USER', '')
                    if not email_user or email_user == 'your-email@gmail.com':
                        messages.error(
                            request, 
                            "⚠️ Email is not configured! Please update EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in settings.py. "
                            "Or use console backend for testing by setting: EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'"
                        )
                        form = PasswordResetRequestForm()
                        return render(request, 'users/password_reset_request.html', {'form': form})
                
                send_mail(
                    subject='Password Reset OTP - EduLearnPro',
                    message=f'Your password reset OTP is: {otp}\n\nThis OTP will expire in 10 minutes.\n\nIf you did not request this, please ignore this email.',
                    from_email=from_email,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                # Store email in session for next step
                request.session['reset_email'] = email
                
                # Show appropriate message based on backend
                if is_console_backend:
                    messages.success(request, f"OTP has been generated. Check your Django console/terminal for the OTP: {otp}")
                    # Also print to console for easy access
                    print(f"\n{'='*60}")
                    print(f"PASSWORD RESET OTP for {email}")
                    print(f"OTP: {otp}")
                    print(f"This OTP expires in 10 minutes.")
                    print(f"{'='*60}\n")
                else:
                    messages.success(request, f"OTP has been sent to {email}. Please check your email.")
                
                return redirect('users:verify_otp')
            except Exception as e:
                import traceback
                error_details = str(e)
                # Provide user-friendly error messages
                if 'authentication failed' in error_details.lower() or 'invalid credentials' in error_details.lower():
                    messages.error(request, "Email authentication failed. Please check your EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in settings.py")
                elif 'connection' in error_details.lower() or 'timeout' in error_details.lower():
                    messages.error(request, "Could not connect to email server. Please check your EMAIL_HOST and EMAIL_PORT settings.")
                else:
                    messages.error(request, f"Failed to send email: {error_details}. Please check your email configuration in settings.py.")
                
                # Log the full error for debugging
                logger = logging.getLogger(__name__)
                logger.error(f"Email send error: {traceback.format_exc()}")
                
                form = PasswordResetRequestForm()
                return render(request, 'users/password_reset_request.html', {'form': form})
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'users/password_reset_request.html', {'form': form})


def verify_otp(request):
    """Verify OTP for password reset"""
    if request.user.is_authenticated:
        return redirect('users:student_dashboard')
    
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, "Please request an OTP first.")
        return redirect('users:password_reset_request')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST, initial={'email': email})
        if form.is_valid():
            otp = form.cleaned_data['otp']
            
            # Mark OTP as verified
            otp_obj = PasswordResetOTP.objects.filter(
                email=email,
                otp=otp,
                is_verified=False
            ).order_by('-created_at').first()
            
            if otp_obj:
                otp_obj.is_verified = True
                otp_obj.save()
                
                # Store email and OTP in session for password reset
                request.session['reset_email'] = email
                request.session['otp_verified'] = True
                messages.success(request, "OTP verified successfully. Please set your new password.")
                return redirect('users:reset_password')
            else:
                messages.error(request, "Invalid OTP. Please try again.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = OTPVerificationForm(initial={'email': email})
    
    return render(request, 'users/verify_otp.html', {'form': form, 'email': email})


def reset_password(request):
    """Reset password after OTP verification"""
    if request.user.is_authenticated:
        return redirect('users:student_dashboard')
    
    email = request.session.get('reset_email')
    otp_verified = request.session.get('otp_verified', False)
    
    if not email or not otp_verified:
        messages.error(request, "Please verify OTP first.")
        return redirect('users:password_reset_request')
    
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('users:password_reset_request')
    
    if request.method == 'POST':
        form = PasswordResetForm(user, request.POST)
        if form.is_valid():
            form.save()
            
            # Clear session
            del request.session['reset_email']
            del request.session['otp_verified']
            
            messages.success(request, "Your password has been reset successfully. You can now login with your new password.")
            return redirect('users:login')
    else:
        form = PasswordResetForm(user)
    
    return render(request, 'users/reset_password.html', {'form': form})
