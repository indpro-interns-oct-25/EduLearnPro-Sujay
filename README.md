# 🎓 EduLearnPro

<div align="center">

![Django](https://img.shields.io/badge/Django-5.2+-green.svg)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

**A complete, full-stack e-learning platform built with Django**

[Features](#-key-features) • [Installation](#-installation) • [Documentation](#-architecture-overview) • [Contributing](#-contributing)

</div>

---

## 📖 Project Introduction

**EduLearnPro** is a comprehensive e-learning platform that enables instructors to create and manage courses while providing students with an engaging learning experience. Built with Django's MVT (Model-View-Template) architecture, the platform supports course creation, lesson management, student enrollments, progress tracking, achievements, streaks, and certificate generation.

The platform features role-based access control, responsive design, and a recommendation engine to help students discover relevant courses based on their interests and learning history.

---

## ✨ Key Features

### 👥 User Management
- **Custom User Model** with extended profile fields
- **Dual Role System**: Student and Instructor roles with distinct permissions
- **User Profiles** with bio, profile photos, and personal information
- **Secure Authentication** with login, registration, and password reset via OTP

### 🎯 Student Features
- **Student Dashboard** with personalized learning statistics
- **Course Enrollment** system with payment page (Udemy-style checkout)
- **Payment Processing** with dummy payment flow
- **My Courses** page showing all enrolled courses with progress
- **Progress Tracking** with visual progress indicators per course
- **Lesson Completion** system with AJAX-powered updates
- **Lesson View** with video player and sidebar navigation
- **Course Progress** page with detailed lesson completion status
- **Achievement System** with badges and milestones
- **Streak Tracking** to encourage consistent learning
- **Course Recommendations** based on category preferences
- **Auto-generated Certificates** with unique certificate IDs upon course completion
- **Certificate View** and download page for completed courses

### 👨‍🏫 Instructor Features
- **Instructor Dashboard** with comprehensive course analytics
- **Course Management**: Create, edit, and publish courses
- **Lesson Management**: Add, edit, delete, and reorder lessons
- **Student Performance** tracking and analytics
- **Course Statistics**: Enrollment numbers, completion rates, and engagement metrics
- **Thumbnail Upload** for course branding
- **Promo Video** integration (YouTube)

### 📚 Course Management
- **Course Creation** with rich text descriptions
- **Category System**: Development, Design, Marketing, Business, Data Science, Programming, Other
- **Course Levels**: Beginner, Intermediate, Advanced, All Levels
- **Pricing System** with discount support (price and discounted_price)
- **Currency**: Indian Rupee (₹)
- **Free Courses** option (is_free field)
- **Course Status**: Draft and Published states
- **Learning Outcomes** field for course objectives
- **Duration** field (e.g., "6 weeks", "10 hours")
- **Promo Video** integration (YouTube) for course preview
- **Thumbnail Upload** with category-based fallbacks
- **Lesson Resources**: Upload files and materials for each lesson
- **Video Integration**: YouTube video embedding for lessons
- **Lesson Ordering**: Custom order field for lesson sequence

### 🏆 Gamification
- **Achievement System**:
  - First Course Completion
  - Five Courses Completed
  - Ten Courses Completed
  - Streak Milestones (7 days, 30 days, 100 days)
  - Perfect Progress
  - Early Bird
- **Streak Tracking**: Daily activity tracking with visual indicators
- **Progress Visualization**: Real-time progress bars and completion percentages
- **Auto-generated Certificates**: Unique certificate IDs for completed courses

### 🎨 User Interface
- **Responsive Design** with Bootstrap 5
- **Modern Glassmorphism UI** with dark theme
- **Mobile-First Approach** with hamburger navigation
- **AJAX Integration** for seamless user experience
- **Dynamic Content Rendering** using Django templates

---

## 🏗️ Architecture Overview

EduLearnPro follows Django's **MVT (Model-View-Template)** architecture pattern:

```
┌─────────────────────────────────────────────────────────┐
│                     User Request                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                      URL Routing                         │
│              (urls.py - URL Configuration)              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                      Views Layer                         │
│         (views.py - Business Logic & Request Handling)   │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Models Layer   │    │  Templates Layer │
│  (models.py -    │    │ (HTML Templates)│
│   Database)      │    │                  │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Database (SQLite)                      │
└─────────────────────────────────────────────────────────┘
```

### MVT Components

- **Models**: Define database structure and business logic
  - `User`, `Profile`, `Achievement`, `PasswordResetOTP` (users app)
  - `Course`, `Lesson` (courses app)
  - `Enrollment`, `LessonProgress`, `Certificate` (enrollments app)

- **Views**: Handle HTTP requests and return responses
  - Authentication views (login, register, password reset via OTP)
  - Course management views (CRUD operations, course listing)
  - Dashboard views (student/instructor with statistics)
  - Enrollment views (enroll, my courses, payment)
  - Progress tracking views (lesson completion, progress calculation)
  - Certificate views (auto-generation and display)

- **Templates**: Render HTML with dynamic data
  - Base template with navigation
  - Course listing and detail pages
  - Dashboard templates
  - Authentication forms

---

## 🗄️ Database Schema Overview

### Core Models

#### User & Profile (`users/models.py`)
```python
User (AbstractUser)
├── username, email, password
├── phone, bio
└── profile (OneToOne) → Profile
    ├── role (student/instructor)
    ├── current_streak, longest_streak
    ├── last_activity_date
    ├── date_of_birth, gender
    └── profile_photo
```

#### Course & Lesson (`courses/models.py`)
```python
Course
├── title, slug, description
├── instructor (ForeignKey → User)
├── category, level, status
├── price, discounted_price
├── thumbnail, promo_video_url
└── lessons (Related) → Lesson[]
    ├── title, order, content
    ├── video_url, resources
    └── course (ForeignKey → Course)
```

#### Enrollment (`enrollments/models.py`)
```python
Enrollment
├── user (ForeignKey → User)
├── course (ForeignKey → Course)
├── progress (PositiveIntegerField)
├── enrolled_at, completed_at
├── is_completed
└── lesson_progress (Related) → LessonProgress[]
    ├── enrollment (ForeignKey → Enrollment)
    ├── lesson (ForeignKey → Lesson)
    ├── completed (BooleanField)
    └── completed_at
└── certificate (OneToOne) → Certificate
    ├── certificate_id (unique)
    └── issued_at
```

#### Achievement (`users/models.py`)
```python
Achievement
├── user (ForeignKey → User)
├── achievement_type (choices)
│   ├── first_course
│   ├── five_courses, ten_courses
│   ├── streak_7, streak_30, streak_100
│   ├── perfect_progress
│   └── early_bird
└── unlocked_at
```

#### Password Reset (`users/models.py`)
```python
PasswordResetOTP
├── email
├── otp (6 characters)
├── created_at
└── is_verified
```

### Relationships Diagram

```
User (1) ────── (1) Profile
  │
  │ (1:N)
  ├─── Courses (as Instructor)
  │
  │ (1:N)
  ├─── Enrollments (as Student)
  │      │
  │      │ (1:N)
  │      ├─── LessonProgress
  │      │
  │      │ (1:1)
  │      └─── Certificate
  │
  │ (1:N)
  ├─── Achievements
  │
  └─── PasswordResetOTP (temporary)

Course (1) ────── (N) Lesson
  │
  │ (1:N)
  └─── Enrollments
```

---

## 🚀 Installation

### Prerequisites

- **Python** 3.10 or higher
- **pip** (Python package manager)
- **Git** (for cloning the repository)
- **Virtual Environment** (recommended)

### Step-by-Step Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/EduLearnPro.git
   cd EduLearnPro
   ```

2. **Create a virtual environment**
   ```bash
   # On Windows
   python -m venv myenv
   myenv\Scripts\activate

   # On macOS/Linux
   python3 -m venv myenv
   source myenv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install django>=5.2.7
   # Or if you have a requirements.txt:
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root (or modify `settings.py` directly):
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   # Email Configuration (for password reset)
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files** (for production)
   ```bash
   python manage.py collectstatic
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Open your browser and navigate to: `http://127.0.0.1:8000/`
   - Admin panel: `http://127.0.0.1:8000/admin/`

---

## 📁 Folder Structure

```
EduLearnPro/
│
├── EduLearnPro/              # Main project directory
│   ├── __init__.py
│   ├── settings.py           # Django settings
│   ├── urls.py               # Root URL configuration
│   ├── wsgi.py               # WSGI configuration
│   └── asgi.py               # ASGI configuration
│
├── users/                     # User management app
│   ├── models.py             # User, Profile, Achievement models
│   ├── views.py              # Authentication views
│   ├── forms.py              # User registration/login forms
│   ├── urls.py               # User-related URLs
│   ├── signals.py            # Signal handlers
│   └── migrations/           # Database migrations
│
├── courses/                   # Course management app
│   ├── models.py             # Course, Lesson models
│   ├── views.py              # Course CRUD views
│   ├── forms.py              # Course creation/editing forms
│   ├── urls.py               # Course-related URLs
│   ├── management/           # Custom management commands
│   └── migrations/           # Database migrations
│
├── enrollments/              # Enrollment system app
│   ├── models.py             # Enrollment, LessonProgress, Certificate models
│   ├── views.py              # Enrollment, progress, payment views
│   ├── urls.py               # Enrollment-related URLs
│   ├── signals.py            # Certificate generation signals
│   └── migrations/           # Database migrations
│
├── templates/                 # HTML templates
│   ├── base.html             # Base template with navigation
│   ├── home/                  # Homepage templates
│   │   └── index.html        # Homepage with courses, testimonials
│   ├── users/                 # User-related templates
│   │   ├── login.html, register.html
│   │   ├── profile.html
│   │   ├── student_dashboard.html
│   │   ├── instructor_dashboard.html
│   │   └── password reset templates
│   ├── courses/               # Course-related templates
│   │   ├── course_list.html, course_detail.html
│   │   ├── course_form.html, course_manage.html
│   │   ├── instructor_dashboard.html
│   │   └── lesson_view.html
│   └── enrollments/           # Enrollment-related templates
│       ├── my_courses.html
│       ├── payment.html
│       ├── progress.html
│       └── certificate.html
│
├── static/                    # Static files
│   ├── css/
│   │   └── main.css          # Main stylesheet
│   ├── js/
│   │   └── main.js           # Main JavaScript file
│   └── images/               # Image assets
│
├── media/                     # User-uploaded files
│   ├── course_thumbnails/    # Course thumbnails
│   ├── lesson_resources/     # Lesson files
│   └── profile_photos/      # User profile pictures
│
├── manage.py                  # Django management script
├── db.sqlite3                 # SQLite database (development)
└── README.md                  # This file
```

---

## 🔗 URL Structure

### Main Routes
- `/` - Homepage with featured courses
- `/courses/` - Course listing page
- `/courses/<slug>/` - Course detail page
- `/courses/<slug>/manage/` - Course management (instructor only)
- `/courses/<course_slug>/lessons/<id>/` - Lesson view page

### User Routes
- `/users/login/` - User login
- `/users/register/` - User registration
- `/users/profile/` - User profile page
- `/users/student/dashboard/` - Student dashboard
- `/users/instructor/dashboard/` - Instructor dashboard
- `/users/password-reset/` - Password reset (OTP-based)

### Enrollment Routes
- `/enrollments/my-courses/` - My enrolled courses
- `/enrollments/<slug>/payment/` - Payment page (Udemy-style)
- `/enrollments/<slug>/enroll/` - Enroll in course
- `/enrollments/<slug>/progress/` - Course progress page
- `/enrollments/<slug>/certificate/` - View certificate
- `/enrollments/lesson/<id>/complete/` - Mark lesson complete (AJAX)

---

## 🛠️ Technology Stack

| Category | Technology | Version |
|----------|-----------|---------|
| **Backend Framework** | Django | 5.2+ |
| **Database** | SQLite | (Development) |
| **Frontend Framework** | Bootstrap | 5.3.3 |
| **Language** | Python | 3.10+ |
| **Template Engine** | Django Templates | Built-in |
| **JavaScript** | Vanilla JS | ES6+ |
| **CSS** | Custom CSS | Glassmorphism |
| **AJAX** | Fetch API | Native |

### Key Dependencies

- **Django 5.2+**: Web framework
- **Bootstrap 5.3.3**: Frontend CSS framework
- **Python 3.10+**: Programming language

---

## 🔧 Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Optional - defaults to SQLite)
DATABASE_NAME=edulearnpro
DATABASE_USER=your-db-user
DATABASE_PASSWORD=your-db-password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Email Configuration (for OTP password reset)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Media & Static Files
MEDIA_ROOT=media/
STATIC_ROOT=staticfiles/
```

> **Note**: For Gmail, you need to generate an [App Password](https://support.google.com/accounts/answer/185833) instead of using your regular password.

---

## 🎯 How to Run the Project Locally

### Development Mode

1. **Activate your virtual environment**
   ```bash
   # Windows
   myenv\Scripts\activate
   
   # macOS/Linux
   source myenv/bin/activate
   ```

2. **Start the development server**
   ```bash
   python manage.py runserver
   ```

3. **Access the application**
   - Main site: `http://127.0.0.1:8000/`
   - Admin panel: `http://127.0.0.1:8000/admin/`

### Creating Test Data

1. **Create a superuser** (if not already created)
   ```bash
   python manage.py createsuperuser
   ```

2. **Access admin panel** and create:
   - Courses (via admin or instructor dashboard)
   - Lessons for each course
   - Test user accounts

3. **Test the application**:
   - Register as a student
   - Register as an instructor
   - Create a course (as instructor)
   - Enroll in a course (as student)
   - Complete lessons and track progress

---

## 📸 Screenshots

> **Note**: Add screenshots of your application here. Suggested screenshots:
> - Homepage
> - Student Dashboard
> - Instructor Dashboard
> - Course Detail Page
> - Lesson View
> - Certificate View
> - Mobile Responsive Views

```
📷 Screenshots Placeholder
├── homepage.png
├── student-dashboard.png
├── instructor-dashboard.png
├── course-detail.png
├── lesson-view.png
├── certificate.png
└── mobile-view.png
```

---

## 🔌 API Extension Possibility

EduLearnPro is **DRF-ready** and can be easily extended to support REST API functionality:

### Potential API Endpoints

```python
# Example API structure (not implemented yet)
/api/v1/
├── auth/
│   ├── login/
│   ├── register/
│   └── password-reset/
├── courses/
│   ├── list/
│   ├── detail/<slug>/
│   └── enroll/<slug>/
├── lessons/
│   ├── list/<course_slug>/
│   ├── detail/<id>/
│   └── complete/<id>/
├── enrollments/
│   ├── my-courses/
│   ├── progress/<slug>/
│   ├── payment/<slug>/
│   └── certificate/<slug>/
└── achievements/
    └── list/
```

### To Add API Support

1. Install Django REST Framework:
   ```bash
   pip install djangorestframework
   ```

2. Add to `INSTALLED_APPS` in `settings.py`:
   ```python
   INSTALLED_APPS = [
       # ... existing apps
       'rest_framework',
   ]
   ```

3. Create serializers for models
4. Create API viewsets
5. Configure API URLs

---

## 🚀 Future Enhancements

### Planned Features

- [ ] **REST API** with Django REST Framework
- [ ] **Video Streaming** integration (Vimeo, AWS S3)
- [ ] **Discussion Forums** for courses
- [ ] **Live Chat** support
- [ ] **Quiz System** with automated grading
- [ ] **Assignment Submission** and grading
- [ ] **Payment Gateway** integration (Stripe, PayPal, Razorpay) - Currently has dummy payment flow
- [ ] **Email Notifications** for course updates
- [ ] **Social Features**: Follow instructors, share courses
- [ ] **Advanced Analytics** for instructors
- [ ] **Multi-language Support** (i18n)
- [ ] **Dark/Light Theme** toggle
- [ ] **Mobile App** (React Native/Flutter)
- [ ] **WebRTC** for live classes
- [ ] **AI-Powered Recommendations** using machine learning

### Technical Improvements

- [ ] **PostgreSQL** migration for production
- [ ] **Redis** for caching and sessions
- [ ] **Celery** for background tasks
- [ ] **Docker** containerization
- [ ] **CI/CD Pipeline** setup
- [ ] **Unit Tests** and integration tests
- [ ] **API Documentation** (Swagger/OpenAPI)
- [ ] **Performance Optimization**
- [ ] **Security Enhancements** (rate limiting, CSRF improvements)

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/EduLearnPro.git
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow PEP 8 style guidelines
   - Write clear commit messages
   - Add comments for complex logic

4. **Test your changes**
   ```bash
   python manage.py test
   ```

5. **Commit your changes**
   ```bash
   git commit -m "Add: Description of your feature"
   ```

6. **Push to your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Provide a clear description of changes
   - Reference any related issues
   - Add screenshots if UI changes

### Code Style Guidelines

- Follow **PEP 8** for Python code
- Use **4 spaces** for indentation
- Maximum line length: **88 characters** (Black formatter)
- Use **descriptive variable names**
- Add **docstrings** for functions and classes
- Write **meaningful commit messages**

---

## 📝 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025 EduLearnPro

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 👨‍💻 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com
- LinkedIn: [Your LinkedIn](https://linkedin.com/in/yourprofile)

---

## 🙏 Acknowledgments

- Django community for the excellent framework
- Bootstrap team for the responsive CSS framework
- All contributors and testers

---

## 📞 Support

If you encounter any issues or have questions:

- **Open an issue** on GitHub
- **Email**: your.email@example.com
- **Documentation**: Check the code comments and docstrings

---

<div align="center">

**Made with ❤️ using Django**

⭐ Star this repo if you find it helpful!

</div>

