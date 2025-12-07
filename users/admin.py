from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Achievement, Profile, User


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    fieldsets = ((None, {"fields": ("role",)}),)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "get_role",
        "phone",
        "is_staff",
        "is_active",
    )
    list_filter = ("is_staff", "is_active", "profile__role")
    search_fields = ("username", "email", "first_name", "last_name", "phone")
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "email", "phone", "bio")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "first_name",
                "last_name",
                "phone",
                "bio",
                "password1",
                "password2",
                "is_active",
                "is_staff",
            ),
        }),
    )

    @admin.display(ordering="profile__role", description="Role")
    def get_role(self, obj):
        if hasattr(obj, "profile") and obj.profile:
            return obj.profile.get_role_display()
        return "—"


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement_type', 'unlocked_at')
    list_filter = ('achievement_type', 'unlocked_at')
    search_fields = ('user__username', 'user__email', 'achievement_type')
    readonly_fields = ('unlocked_at',)
    ordering = ('-unlocked_at',)

