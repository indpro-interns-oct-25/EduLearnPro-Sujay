// Main JavaScript file for EduLearnPro

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // Form validation helpers
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');
                } else {
                    field.classList.remove('error');
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // Mobile navigation toggle - handled in base.html to avoid duplicate handlers

    // Lesson sidebar toggle (mobile)
    const sidebarToggle = document.querySelector('[data-sidebar-toggle]');
    const lessonSidebar = document.querySelector('.lesson-sidebar');
    if (sidebarToggle && lessonSidebar) {
        sidebarToggle.addEventListener('click', function() {
            const expanded = lessonSidebar.classList.toggle('open');
            sidebarToggle.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        });
    }
});

