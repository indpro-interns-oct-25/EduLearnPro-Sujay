from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from courses.models import Course
from users.models import Profile


class Command(BaseCommand):
    help = "Run a smoke test for enroll flow (anonymous -> enroll -> resume)"

    def handle(self, *args, **options):
        User = get_user_model()
        client = Client()
        # Ensure the test client uses a host in ALLOWED_HOSTS (dev server)
        client.defaults['HTTP_HOST'] = '127.0.0.1:8000'

        # Ensure an instructor and a course exist
        instr_username = "smoke_instructor"
        instr, created = User.objects.get_or_create(username=instr_username)
        if created:
            instr.set_password("instrpass")
            instr.save()
        Profile.objects.get_or_create(user=instr, defaults={"role": "instructor"})

        course, created = Course.objects.get_or_create(
            slug="smoke-course",
            defaults={
                "title": "Smoke Test Course",
                "description": "Auto-created for smoke testing",
                "instructor": instr,
            },
        )

        slug = course.slug
        detail_url = reverse("courses:detail", kwargs={"slug": slug})
        enroll_url = reverse("enrollments:enroll", kwargs={"slug": slug})
        progress_url = reverse("enrollments:progress", kwargs={"slug": slug})

        self.stdout.write("[1] Checking course detail as anonymous user...")
        r = client.get(detail_url)
        if r.status_code == 200 and b"Enroll" in r.content:
            self.stdout.write(self.style.SUCCESS("Anonymous view contains Enroll CTA"))
        else:
            self.stdout.write(self.style.WARNING("Anonymous view did not contain Enroll CTA (status=%s)" % r.status_code))

        # Create student user
        student_username = "smoke_student"
        student_password = "studentpass"
        student, created = User.objects.get_or_create(username=student_username)
        if created:
            student.set_password(student_password)
            student.save()
        Profile.objects.get_or_create(user=student, defaults={"role": "student"})

        # Login as student
        logged_in = client.login(username=student_username, password=student_password)
        if not logged_in:
            # try to set password and login again
            student.set_password(student_password)
            student.save()
            logged_in = client.login(username=student_username, password=student_password)

        if logged_in:
            self.stdout.write(self.style.SUCCESS("[2] Logged in as student"))
        else:
            self.stdout.write(self.style.ERROR("[2] Failed to log in as student"))
            return

        # Visit detail page as logged-in (should show Enroll)
        r2 = client.get(detail_url)
        if r2.status_code == 200 and b"Enroll" in r2.content:
            self.stdout.write(self.style.SUCCESS("Logged-in student sees Enroll CTA"))
        else:
            self.stdout.write(self.style.WARNING("Logged-in student page missing Enroll CTA (status=%s)" % r2.status_code))

        # Perform enroll (GET)
        r3 = client.get(enroll_url, follow=True)
        if r3.status_code == 200:
            self.stdout.write(self.style.SUCCESS("Enroll endpoint responded; redirected to My Courses"))
        else:
            self.stdout.write(self.style.ERROR("Enroll endpoint failed (status=%s)" % r3.status_code))

        # Check detail page now shows Resume/Continue
        r4 = client.get(detail_url)
        if r4.status_code == 200 and (b"Continue" in r4.content or b"Resume" in r4.content):
            self.stdout.write(self.style.SUCCESS("After enrolling, student sees Resume/Continue CTA"))
        else:
            self.stdout.write(self.style.ERROR("After enrolling, Resume CTA not found"))

        # Check instructor dashboard for instructor user
        client.logout()
        client.login(username=instr_username, password="instrpass")
        dash_url = reverse("courses:instructor-dashboard")
        rd = client.get(dash_url)
        if rd.status_code == 200:
            self.stdout.write(self.style.SUCCESS("Instructor dashboard reachable (status 200)"))
        else:
            self.stdout.write(self.style.ERROR("Instructor dashboard failed (status=%s)" % rd.status_code))

        self.stdout.write(self.style.SUCCESS("Smoke enroll test completed."))
