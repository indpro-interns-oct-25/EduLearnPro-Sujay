from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return self.username

    @property
    def role(self):
        profile = getattr(self, "profile", None)
        return profile.role if profile else None

    @property
    def role_display(self):
        profile = getattr(self, "profile", None)
        return profile.get_role_display() if profile else ""

    @property
    def profile_created_at(self):
        profile = getattr(self, "profile", None)
        return profile.created_at if profile else None


class Profile(models.Model):
    ROLE_CHOICES = (
        ("student", "Student"),
        ("instructor", "Instructor"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Streak tracking
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(blank=True, null=True)
    # Profile fields
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Date of Birth")
    gender = models.CharField(
        max_length=20,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
            
        ],
        blank=True,
        null=True,
    )
    course_year = models.CharField(max_length=100, blank=True, null=True, verbose_name="Course / Year")
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True, verbose_name="Profile Photo")

    def __str__(self) -> str:
        return f"{self.user.username} - {self.get_role_display()}"

    def update_streak(self):
        """Update learning streak based on activity"""
        from django.utils import timezone
        today = timezone.now().date()
        
        if self.last_activity_date:
            days_diff = (today - self.last_activity_date).days
            
            if days_diff == 1:
                # Consecutive day
                self.current_streak += 1
            elif days_diff > 1:
                # Streak broken
                self.current_streak = 1
            # days_diff == 0 means same day, keep streak
        else:
            # First activity
            self.current_streak = 1
        
        self.last_activity_date = today
        
        # Update longest streak
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.save(update_fields=['current_streak', 'longest_streak', 'last_activity_date'])


class Achievement(models.Model):
    """Student achievements"""
    ACHIEVEMENT_TYPES = (
        ('first_course', 'First Course Completed'),
        ('five_courses', 'Five Courses Completed'),
        ('ten_courses', 'Ten Courses Completed'),
        ('streak_7', '7 Day Streak'),
        ('streak_30', '30 Day Streak'),
        ('streak_100', '100 Day Streak'),
        ('perfect_progress', 'Perfect Progress'),
        ('early_bird', 'Early Bird'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="achievements"
    )
    achievement_type = models.CharField(max_length=50, choices=ACHIEVEMENT_TYPES)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'achievement_type')
        ordering = ('-unlocked_at',)
    
    def __str__(self) -> str:
        return f"{self.user.username} - {self.get_achievement_type_display()}"
    
    @property
    def icon(self):
        """Return icon for achievement"""
        icons = {
            'first_course': 'fa-trophy',
            'five_courses': 'fa-medal',
            'ten_courses': 'fa-crown',
            'streak_7': 'fa-fire',
            'streak_30': 'fa-fire',
            'streak_100': 'fa-fire',
            'perfect_progress': 'fa-star',
            'early_bird': 'fa-sun',
        }
        return icons.get(self.achievement_type, 'fa-award')


class PasswordResetOTP(models.Model):
    """OTP for password reset"""
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['email', 'otp']),
        ]
    
    def __str__(self):
        return f"OTP for {self.email}"
    
    def is_expired(self):
        """Check if OTP is expired (10 minutes)"""
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(minutes=10)
