from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.functional import cached_property

from users.models import User


class Course(models.Model):
    CATEGORY_CHOICES = (
        ("development", "Development"),
        ("design", "Design"),
        ("marketing", "Marketing"),
        ("business", "Business"),
        ("data", "Data Science"),
        ('programming', "Programming"),
        ("other", "Other"),
    )

    CATEGORY_THUMBNAILS = {
        "development": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1600&q=80",
        "design": "https://images.unsplash.com/photo-1523475472560-d2df97ec485c?auto=format&fit=crop&w=1600&q=80",
        "marketing": "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1600&q=80",
        "business": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&w=1600&q=80",
        "data": "https://images.unsplash.com/photo-1517430816045-df4b7de11d1d?auto=format&fit=crop&w=1600&q=80",
        "other": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=1600&q=80",
    }

    DEFAULT_THUMBNAIL = "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?auto=format&fit=crop&w=1600&q=80"

    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("published", "Published"),
    )

    LEVEL_CHOICES = (
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
        ("all", "All Levels"),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="courses")
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default="other")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="all")
    thumbnail = models.ImageField(upload_to="course_thumbnails/", blank=True, null=True)
    promo_video_url = models.URLField(
        blank=True,
        null=True,
        help_text="Course preview/intro video URL (YouTube or direct video URL). This video will be displayed on the course detail page."
    )
    learning_outcomes = models.TextField(
                                         
        blank=True,
        null=True,
        help_text="List the key learning outcomes (one per line or use bullet points)"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    is_free = models.BooleanField(default=False, help_text="Check if this course is free")
    duration = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="e.g., '6 weeks', '10 hours', '4 months'"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("title",)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            num = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("courses:detail", kwargs={"slug": self.slug})

    def get_thumbnail_url(self) -> str:
        """Return uploaded thumbnail or a polished fallback based on category."""
        if self.thumbnail:
            return self.thumbnail.url
        return self.CATEGORY_THUMBNAILS.get(self.category, self.DEFAULT_THUMBNAIL)

    @cached_property
    def intro_lesson(self) -> "Lesson | None":
        return (
            self.lessons.filter(video_url__isnull=False)
            .exclude(video_url="")
            .order_by("order", "id")
            .first()
        )

    def get_promo_video_embed_url(self) -> str | None:
        """Get embed URL for promo video (course preview/intro video)."""
        if not self.promo_video_url:
            return None
        # Check if it's a YouTube URL
        parsed = urlparse(self.promo_video_url)
        host = parsed.netloc.lower()
        if "youtube.com" in host or "youtu.be" in host:
            # Extract video ID
            if parsed.path.startswith("/embed/"):
                video_id = parsed.path.split("/")[2]
            elif "youtu.be" in host:
                video_id = parsed.path.lstrip("/")
            else:
                query = parse_qs(parsed.query)
                video_ids = query.get("v")
                video_id = video_ids[0] if video_ids else None
            if video_id:
                # Add parameters to prevent redirects and ensure embedding works
                return f"https://www.youtube.com/embed/{video_id}?rel=0&showinfo=0&modestbranding=1&enablejsapi=1&playsinline=1&controls=1&fs=1"
        # For non-YouTube URLs, return as-is
        return self.promo_video_url

    def get_intro_video_embed_url(self) -> str | None:
        """Get intro video - prefer promo video, fallback to first lesson video."""
        if self.promo_video_url:
            return self.get_promo_video_embed_url()
        lesson = self.intro_lesson
        if lesson:
            return lesson.get_embed_url()
        return None

    def get_intro_video_thumbnail_url(self) -> str | None:
        """Get intro video thumbnail - prefer promo video thumbnail, fallback to first lesson."""
        if self.promo_video_url:
            # Extract YouTube video ID for thumbnail
            parsed = urlparse(self.promo_video_url)
            host = parsed.netloc.lower()
            if "youtube.com" in host or "youtu.be" in host:
                if parsed.path.startswith("/embed/"):
                    video_id = parsed.path.split("/")[2]
                elif "youtu.be" in host:
                    video_id = parsed.path.lstrip("/")
                else:
                    query = parse_qs(parsed.query)
                    video_ids = query.get("v")
                    video_id = video_ids[0] if video_ids else None
                if video_id:
                    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        lesson = self.intro_lesson
        if lesson:
            thumb = lesson.get_thumbnail_url()
            if thumb:
                return thumb
        return None

    def get_cover_image_url(self) -> str:
        return self.get_intro_video_thumbnail_url() or self.get_thumbnail_url()

    def __str__(self) -> str:
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField(default=1)
    video_url = models.URLField(blank=True, null=True, help_text="YouTube URL or direct video URL")
    resources = models.FileField(upload_to="lesson_resources/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("course", "order", "id")
        unique_together = ("course", "order")

    def __str__(self) -> str:
        return f"{self.course.title} - {self.title}"

    def get_youtube_video_id(self) -> str | None:
        if not self.video_url:
            return None
        parsed = urlparse(self.video_url)
        host = parsed.netloc.lower()
        if "youtube.com" in host:
            if parsed.path.startswith("/embed/"):
                return parsed.path.split("/")[2]
            query = parse_qs(parsed.query)
            video_ids = query.get("v")
            if video_ids:
                return video_ids[0]
        if "youtu.be" in host and parsed.path:
            return parsed.path.lstrip("/")
        return None

    def get_embed_url(self) -> str | None:
        """Get the embed URL for the video. Returns YouTube embed URL if YouTube, otherwise returns original URL."""
        if not self.video_url:
            return None
        video_id = self.get_youtube_video_id()
        if video_id:
            # Add parameters to prevent redirects and ensure embedding works
            return f"https://www.youtube.com/embed/{video_id}?rel=0&showinfo=0&modestbranding=1&enablejsapi=1&playsinline=1&controls=1&fs=1"
        # For non-YouTube URLs, return as-is (works for direct video URLs)
        return self.video_url

    def get_thumbnail_url(self) -> str | None:
        video_id = self.get_youtube_video_id()
        if video_id:
            return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        return None