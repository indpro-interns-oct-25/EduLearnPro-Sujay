from django.core.management.base import BaseCommand
from django.utils.text import slugify

from courses.models import Course


class Command(BaseCommand):
    help = "Populate missing Course.slug values for existing courses"

    def handle(self, *args, **options):
        qs = Course.objects.filter(slug__in=["", None])
        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("No courses with missing slug found."))
            return

        updated = 0
        for course in qs:
            base_slug = slugify(course.title) or "course"
            slug = base_slug
            num = 1
            while Course.objects.filter(slug=slug).exclude(pk=course.pk).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            course.slug = slug
            course.save(update_fields=["slug"])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Populated slug for {updated}/{total} courses."))
